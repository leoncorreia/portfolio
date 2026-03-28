"""SQLite + HydraDB memory; Dify workflow after analyze (appends note to explanation)."""

from __future__ import annotations

from app.config import get_settings
from app.providers.ai_credentials import is_live_key
from app.providers.dify_workflow import invoke_post_analyze_orchestration
from app.providers.hydra_memory import HydraMemoryClient
from app.repositories.interfaces import MemoryRepository
from app.schemas import AnalyzeTeamResponse, MemoryRecordOut, Squad
from app.services.recommendation_service import RecommendationService

_COACH_MARKER = "--- Coach explanation (Kimi via GMI) ---"
_DIFY_MARKER = "\n\n--- Dify workflow note ---\n"


def _split_explanation(full: str) -> tuple[str, str]:
    if _COACH_MARKER in full:
        det, _, coach = full.partition(_COACH_MARKER)
        return det.strip(), coach.strip()
    return full.strip(), ""


class MemoryService:
    def __init__(
        self,
        repo: MemoryRepository,
        rec_svc: RecommendationService,
        hydra: HydraMemoryClient | None = None,
    ) -> None:
        self._repo = repo
        self._rec_svc = rec_svc
        self._hydra = hydra

    async def analyze_with_memory(
        self, user_id: str, squad: Squad, use_memory: bool
    ) -> AnalyzeTeamResponse:
        settings = get_settings()
        prev_sqlite: MemoryRecordOut | None = None
        previous_summary: str | None = None
        previous_from_hydra = False
        memory_used = False

        if use_memory:
            if self._hydra:
                try:
                    hydra_prev = await self._hydra.load_latest_fpl_session(user_id=user_id)
                    if hydra_prev:
                        rec = hydra_prev.get("recommendation") or {}
                        if isinstance(rec, dict) and rec.get("summary"):
                            previous_summary = str(rec.get("summary"))
                            previous_from_hydra = True
                            memory_used = True
                except Exception:
                    pass

            if previous_summary is None:
                prev_sqlite = self._repo.get_latest(user_id)
                if prev_sqlite:
                    previous_summary = (
                        prev_sqlite.recommendation.get("summary", "")
                        if prev_sqlite.recommendation
                        else None
                    )
                    memory_used = True

        recommendation = await self._rec_svc.analyze(squad, user_id=user_id)
        self._repo.save_recommendation(user_id, squad, recommendation)

        if self._hydra:
            try:
                await self._hydra.save_fpl_session(
                    user_id=user_id,
                    squad_snapshot=squad.model_dump(),
                    recommendation=recommendation.model_dump(),
                    captain_id=recommendation.captain,
                    transfer_action=recommendation.transfer_action,
                    transfer_options=[t.model_dump() for t in recommendation.transfer_options],
                )
            except Exception:
                pass

        det_text, _coach = _split_explanation(recommendation.explanation)
        dify_result = await invoke_post_analyze_orchestration(
            settings,
            user_id=user_id,
            squad_json=squad.model_dump_json(),
            recommendation_json=recommendation.model_dump_json(),
            deterministic_explanation=det_text,
        )

        if dify_result.output_text:
            recommendation.explanation = recommendation.explanation + _DIFY_MARKER + dify_result.output_text

        return AnalyzeTeamResponse(
            recommendation=recommendation,
            memory_used=memory_used,
            previous_summary=previous_summary,
            previous_from_hydradb=previous_from_hydra,
            dify_key_configured=is_live_key(settings.dify_api_key),
            dify_used=dify_result.dify_used,
            dify_error=dify_result.error,
            dify_workflow_run_id=dify_result.workflow_run_id,
            dify_status=dify_result.status,
            dify_output_preview=dify_result.output_preview,
        )
