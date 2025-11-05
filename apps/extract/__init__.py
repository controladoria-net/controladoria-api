import mimetypes
import os
import re
import tempfile
import unicodedata
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from fastapi import File, Form, FastAPI, HTTPException, Query, UploadFile, responses, status
from google import genai
from google.genai import types
from models import (
    DocumentMetadataBatchResponse,
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


TERMO_REQUIRED_PATTERNS = [
    {"termo", "representacao"},
    {"procuracao"},
]

DOC_TYPE_TITLES: dict[str, str] = {
    "TERMO_REPRESENTACAO": "PROCURAÇÃO OU TERMO DE REPRESENTAÇÃO",
}


def _normalize_doc_type(value: str | None) -> str:
    if not value or not value.strip():
        raise HTTPException(status_code=400, detail="Document type is required for each uploaded file.")
    return value.strip().upper()


async def _generate_metadata(request: GetDocumentMetadataRequest) -> DocumentMetadataResponse:
    client = genai.Client(api_key=os.environ["GENAI_API_KEY"])

    raw_content = request.content
    if isinstance(raw_content, (str, Path)):
        content_paths = [Path(raw_content)]
    else:
        content_paths = [Path(path) for path in raw_content]

    if not content_paths:
        raise HTTPException(status_code=400, detail="No content provided for metadata generation.")

    for content_path in content_paths:
        if content_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Expected a file but got a directory: {content_path}")
        if not content_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {content_path}")

    descriptor = REGISTRY.get(request.type)
    if not descriptor:
        raise HTTPException(status_code=400, detail=f"Unsupported document type: {request.type}")

    raw_mime = request.content_mime_type
    mime_types: list[str] = []
    if isinstance(raw_mime, (list, tuple)):
        if len(raw_mime) != len(content_paths):
            raise HTTPException(
                status_code=400,
                detail="Number of MIME types provided does not match the number of files supplied.",
            )
        for supplied_mime, path in zip(raw_mime, content_paths):
            if supplied_mime:
                mime_types.append(supplied_mime)
            else:
                guessed = mimetypes.guess_type(path.name)[0]
                mime_types.append(guessed or "application/octet-stream")
    elif isinstance(raw_mime, str) and raw_mime.strip():
        mime_types = [raw_mime] * len(content_paths)
    else:
        for path in content_paths:
            guessed = mimetypes.guess_type(path.name)[0]
            mime_types.append(guessed or "application/octet-stream")

    source_files = request.source_filenames or [path.name for path in content_paths]
    source_files = [str(name) for name in source_files]
    if len(source_files) != len(content_paths):
        source_files = [path.name for path in content_paths]

    uploaded_contents = []
    for index, (path, mime_type) in enumerate(zip(content_paths, mime_types), start=1):
        display_name = descriptor.name.upper()
        if len(content_paths) > 1:
            display_name = f"{descriptor.name.upper()}-{index}"

        uploaded_contents.append(
            client.files.upload(
                file=path,
                config={
                    "mime_type": mime_type,
                    "display_name": display_name,
                },
            )
        )

    response = client.models.generate_content(
        model=request.model,
        contents=uploaded_contents,
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

    title = DOC_TYPE_TITLES.get(request.type, descriptor.name)

    return DocumentMetadataResponse(
        type=request.type,
        title=title,
        data=standardized_data,
        raw=raw_payload,
        source_files=source_files,
    )


def _normalize_filename(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFD", value)
    stripped = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    lowered = stripped.lower()
    sanitized = re.sub(r"[^a-z0-9]+", " ", lowered)
    return sanitized.strip()


def _termo_files_are_complete(filenames: list[str]) -> bool:
    normalized_filenames = [_normalize_filename(name) for name in filenames]

    def contains_all_keywords(candidate: str, keywords: set[str]) -> bool:
        return all(keyword in candidate for keyword in keywords)

    return all(
        any(contains_all_keywords(filename, pattern) for filename in normalized_filenames)
        for pattern in TERMO_REQUIRED_PATTERNS
    )


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
    files: list[UploadFile] | None = File(None),
    file: UploadFile | None = File(None),
    doc_types: list[str] | None = Form(None),
    doc_type: str | None = Form(None),
    model: GeminiModels = Form(GeminiModels.GEMINI_FLASH_2_0),
    temperature: float | None = Form(None),
    content_mime_types: list[str] | None = Form(None),
    content_mime_type: str | None = Form(None),
) -> responses.JSONResponse:
    if files and file:
        raise HTTPException(status_code=400, detail="Provide either 'file' or 'files', not both.")

    uploads_info: list[dict[str, object]] = []
    try:
        if files:
            if not doc_types or len(doc_types) != len(files):
                raise HTTPException(
                    status_code=400,
                    detail="When sending multiple files, provide a matching 'doc_types' value for each upload.",
                )

            if content_mime_types is not None and len(content_mime_types) != len(files):
                raise HTTPException(
                    status_code=400,
                    detail="If 'content_mime_types' is provided it must match the number of uploaded files.",
                )

            for index, upload in enumerate(files):
                doc_type_value = _normalize_doc_type(doc_types[index])
                mime_value = (
                    content_mime_types[index]
                    if content_mime_types is not None
                    else upload.content_type
                )
                temp_path = await _save_upload_to_temp(upload)
                uploads_info.append(
                    {
                        "doc_type": doc_type_value,
                        "upload": upload,
                        "temp_path": temp_path,
                        "mime": mime_value or None,
                        "filename": upload.filename or Path(temp_path).name,
                    }
                )
        elif file:
            resolved_doc_type = _normalize_doc_type(doc_type or (doc_types[0] if doc_types else None))
            resolved_mime = (
                content_mime_type
                or (content_mime_types[0] if content_mime_types else None)
                or file.content_type
            )
            temp_path = await _save_upload_to_temp(file)
            uploads_info.append(
                {
                    "doc_type": resolved_doc_type,
                    "upload": file,
                    "temp_path": temp_path,
                    "mime": resolved_mime or None,
                    "filename": file.filename or Path(temp_path).name,
                }
            )
        else:
            raise HTTPException(status_code=400, detail="No file uploaded. Provide at least one document for analysis.")

        grouped_uploads: dict[str, list[dict[str, object]]] = defaultdict(list)
        for entry in uploads_info:
            grouped_uploads[entry["doc_type"]].append(entry)

        data_files: dict[str, DocumentMetadataResponse] = {}
        for doc_type_key, entries in grouped_uploads.items():
            filenames = [str(entry["filename"]) for entry in entries]
            if doc_type_key == "TERMO_REPRESENTACAO":
                if len(entries) < 2 or not _termo_files_are_complete(filenames):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Para TERMO_REPRESENTACAO é necessário enviar os documentos "
                            "'Termo de Representação' e 'Procuração'."
                        ),
                    )

            content_paths = [entry["temp_path"] for entry in entries]
            mime_values = [entry["mime"] for entry in entries]
            request = GetDocumentMetadataRequest(
                content=content_paths if len(content_paths) > 1 else content_paths[0],
                type=doc_type_key,  # type: ignore[arg-type]
                model=model,
                content_mime_type=mime_values if len(mime_values) > 1 else mime_values[0],
                temperature=temperature,
                source_filenames=filenames,
            )
            result_model = await _generate_metadata(request)
            data_files[doc_type_key] = result_model

    finally:
        for entry in uploads_info:
            temp_path = entry.get("temp_path")
            if isinstance(temp_path, Path):
                temp_path.unlink(missing_ok=True)
            upload_file = entry.get("upload")
            if isinstance(upload_file, UploadFile):
                await upload_file.close()

    batch_response = DocumentMetadataBatchResponse(data_files=data_files)
    return responses.JSONResponse(content=batch_response.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@app.get("/test_metadata")
async def test_metadata(
    filename: list[str] = Query(...),
    doc_types: list[str] = Query(..., alias="doc_type"),
    model: GeminiModels = GeminiModels.GEMINI_FLASH_2_0,
    temperature: float | None = Query(None),
    content_mime_type: list[str] | None = Query(None),
) -> responses.JSONResponse:
    filenames = [name for name in filename if name]
    if not filenames:
        raise HTTPException(status_code=400, detail="Provide at least one filename for analysis.")

    doc_type_values = list(doc_types)
    if not doc_type_values:
        raise HTTPException(status_code=400, detail="Provide at least one doc_type parameter.")

    if len(doc_type_values) == 1:
        doc_type_pairs = [(fname, doc_type_values[0]) for fname in filenames]
    elif len(doc_type_values) == len(filenames):
        doc_type_pairs = list(zip(filenames, doc_type_values))
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either a single doc_type for all filenames or one doc_type per filename.",
        )

    mime_inputs = content_mime_type or []

    def resolve_mime(index: int) -> str | None:
        if not mime_inputs:
            return None
        if len(mime_inputs) == 1:
            candidate = mime_inputs[0]
        elif len(mime_inputs) == len(filenames):
            candidate = mime_inputs[index]
        else:
            raise HTTPException(
                status_code=400,
                detail="If content_mime_type is provided, send one value for all files or one per filename.",
            )
        candidate = (candidate or "").strip()
        return candidate or None

    grouped_entries: dict[str, list[dict[str, object]]] = defaultdict(list)
    for index, (file_name, doc_type_value) in enumerate(doc_type_pairs):
        normalized_type = _normalize_doc_type(doc_type_value)
        doc_path = DOCS_DIR / file_name
        if not doc_path.exists() or not doc_path.is_file():
            raise HTTPException(status_code=404, detail=f"Document not found: {file_name}")

        grouped_entries[normalized_type].append(
            {
                "path": doc_path,
                "filename": file_name,
                "mime": resolve_mime(index),
            }
        )

    if not grouped_entries:
        raise HTTPException(status_code=400, detail="No documents matched the provided parameters.")

    data_files: dict[str, DocumentMetadataResponse] = {}
    for doc_type_key, entries in grouped_entries.items():
        content_paths = [entry["path"] for entry in entries]
        filenames_group = [str(entry["filename"]) for entry in entries]
        mime_values = [entry["mime"] for entry in entries]

        mime_payload: str | list[str | None] | None
        if any(mime_values):
            mime_payload = (
                mime_values if len(mime_values) > 1 else mime_values[0]  # type: ignore[assignment]
            )
        else:
            mime_payload = None

        request = GetDocumentMetadataRequest(
            content=content_paths if len(content_paths) > 1 else content_paths[0],
            type=doc_type_key,  # type: ignore[arg-type]
            model=model,
            content_mime_type=mime_payload,
            temperature=temperature,
            source_filenames=filenames_group,
        )

        result_model = await _generate_metadata(request)
        data_files[doc_type_key] = result_model

    batch_response = DocumentMetadataBatchResponse(data_files=data_files)
    return responses.JSONResponse(
        content=batch_response.model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
