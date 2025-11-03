import mimetypes
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import File, Form, FastAPI, HTTPException, UploadFile, responses, status
from google import genai
from google.genai import types
from models import (
    DocumentMetadataResponse,
    GetDocumentMetadataRequest,
    REGISTRY,
    GeminiModels,
    build_dto,
    dto_to_dict,
)
from pydantic import BaseModel

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


@app.get("/health")
async def health_check() -> responses.JSONResponse:
    return responses.JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)


async def _generate_metadata(request: GetDocumentMetadataRequest) -> dict:
    client = genai.Client(api_key=os.environ["GENAI_API_KEY"])

    if isinstance(request.content, str):
        content_path = Path(request.content)
    else:
        content_path = request.content

    if content_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Expected a file but got a directory: {content_path}")
    if not content_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {content_path}")

    request.content = content_path

    descriptor = REGISTRY.get(request.type)
    if not descriptor:
        raise HTTPException(status_code=400, detail=f"Unsupported document type: {request.type}")

    if not request.content_mime_type:
        guessed_mime = mimetypes.guess_type(request.content.name)[0]
        request.content_mime_type = guessed_mime or "application/octet-stream"

    uploaded_content = client.files.upload(
        file=request.content,
        config={
            "mime_type": request.content_mime_type,
            "display_name": descriptor.name.upper(),
        },
    )
    response = client.models.generate_content(
        model=request.model,
        contents=[uploaded_content],
        config=types.GenerateContentConfig(
            response_mime_type=descriptor.response_mime_type,
            response_schema=descriptor.response_schema,
            system_instruction=descriptor.system_instruction,
            temperature=request.temperature,
        ),
    )

    if isinstance(response.parsed, BaseModel):
        raw_payload = response.parsed.model_dump(mode="python")
    elif isinstance(response.parsed, dict):
        raw_payload = response.parsed
    else:
        raise TypeError(f"Unexpected response type: {type(response.parsed)!r}")

    dto_instance = build_dto(request.type, raw_payload)
    standardized_data = dto_to_dict(dto_instance)

    response_model = DocumentMetadataResponse(
        type=request.type,
        data=standardized_data,
        raw=raw_payload,
    )
    return response_model.model_dump(mode="json")


async def _save_upload_to_temp(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            tmp.write(chunk)
        temp_path = Path(tmp.name)
    await upload.seek(0)
    return temp_path


@app.post("/metadata")
async def create_metadata(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    model: GeminiModels = Form(GeminiModels.GEMINI_FLASH_2_0),
    temperature: float | None = Form(None),
    content_mime_type: str | None = Form(None),
) -> responses.JSONResponse:
    temp_path = await _save_upload_to_temp(file)
    try:
        request = GetDocumentMetadataRequest(
            content=temp_path,
            type=doc_type,
            model=model,
            content_mime_type=content_mime_type or file.content_type,
            temperature=temperature,
        )
        result = await _generate_metadata(request)
    finally:
        temp_path.unlink(missing_ok=True)
        await file.close()

    return responses.JSONResponse(content=result, status_code=status.HTTP_200_OK)


@app.get("/test_metadata")
async def test_metadata(
    filename: str,
    doc_type: str,
    model: GeminiModels = GeminiModels.GEMINI_FLASH_2_0,
    temperature: float | None = None,
    content_mime_type: str | None = None,
) -> responses.JSONResponse:
    doc_path = DOCS_DIR / filename
    if not doc_path.exists() or not doc_path.is_file():
        raise HTTPException(status_code=404, detail=f"Document not found: {filename}")

    request = GetDocumentMetadataRequest(
        content=doc_path,
        type=doc_type,
        model=model,
        content_mime_type=content_mime_type or mimetypes.guess_type(doc_path.name)[0],
        temperature=temperature,
    )

    result = await _generate_metadata(request)
    return responses.JSONResponse(content=result, status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
