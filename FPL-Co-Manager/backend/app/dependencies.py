"""FastAPI dependency wiring."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_db
from app.providers.explanation_provider import ExplanationProvider
from app.providers.fpl_public_api import FPLPublicApiProvider
from app.providers.hydra_memory import get_hydra_client
from app.providers.image_parser_provider import ImageParserProvider, KimiImageParserProvider
from app.providers.kimi_provider import KimiViaGMIProvider
from app.repositories.memory_repository import SQLiteMemoryRepository
from app.services.compare_service import CompareService
from app.services.explanation_service import ExplanationService
from app.services.memory_service import MemoryService
from app.services.optimizer_service import OptimizerService
from app.services.recommendation_service import RecommendationService
from app.services.scoring_service import ScoringService
from app.services.team_import_service import TeamImportService
from app.services.transfer_service import TransferService


def get_app_settings() -> Settings:
    return get_settings()


@lru_cache
def get_fpl_provider() -> FPLPublicApiProvider:
    return FPLPublicApiProvider(get_settings())


def build_scoring() -> ScoringService:
    return ScoringService()


def build_optimizer(scoring: ScoringService) -> OptimizerService:
    return OptimizerService(scoring)


def build_transfer(fpl: FPLPublicApiProvider, scoring: ScoringService) -> TransferService:
    return TransferService(fpl, scoring)


def build_recommendation(
    fpl: FPLPublicApiProvider,
    kimi_explanation: ExplanationProvider,
) -> RecommendationService:
    scoring = build_scoring()
    opt = build_optimizer(scoring)
    xfer = build_transfer(fpl, scoring)
    expl = ExplanationService()
    return RecommendationService(scoring, opt, xfer, expl, kimi_explanation)


def get_explanation_provider(settings: Settings = Depends(get_app_settings)) -> ExplanationProvider:
    return KimiViaGMIProvider(settings)


def get_recommendation_service(
    fpl: FPLPublicApiProvider = Depends(get_fpl_provider),
    kimi_explanation: ExplanationProvider = Depends(get_explanation_provider),
) -> RecommendationService:
    return build_recommendation(fpl, kimi_explanation)


def get_team_import_service(
    fpl: FPLPublicApiProvider = Depends(get_fpl_provider),
) -> TeamImportService:
    return TeamImportService(fpl)


def get_memory_repo(db: Session = Depends(get_db)) -> SQLiteMemoryRepository:
    return SQLiteMemoryRepository(db)


def get_hydra_optional(settings: Settings = Depends(get_app_settings)):
    return get_hydra_client(settings)


def get_memory_service(
    db: Session = Depends(get_db),
    rec: RecommendationService = Depends(get_recommendation_service),
    hydra=Depends(get_hydra_optional),
) -> MemoryService:
    return MemoryService(SQLiteMemoryRepository(db), rec, hydra)


def get_compare_service(
    db: Session = Depends(get_db),
    rec: RecommendationService = Depends(get_recommendation_service),
) -> CompareService:
    return CompareService(SQLiteMemoryRepository(db), rec)


def get_image_parser(settings: Settings = Depends(get_app_settings)) -> ImageParserProvider:
    return KimiImageParserProvider(settings)
