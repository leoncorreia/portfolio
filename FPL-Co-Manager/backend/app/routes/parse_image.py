from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_image_parser
from app.providers.image_parser_provider import ImageParserProvider
from app.schemas import ParseImageResponse

router = APIRouter(prefix="/api", tags=["multimodal"])


@router.post("/parse-image", response_model=ParseImageResponse)
async def parse_image(
    file: UploadFile = File(...),
    parser: ImageParserProvider = Depends(get_image_parser),
) -> ParseImageResponse:
    content = await file.read()
    squad, raw = await parser.parse_squad_image(content, file.content_type or "application/octet-stream")
    return ParseImageResponse(
        ok=squad is not None,
        message=raw,
        parsed_squad=squad,
        raw_model_output=raw,
    )
