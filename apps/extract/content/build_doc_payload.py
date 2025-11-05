"""Utility helpers to extract document content and persist it as JSON payloads.

The script looks for PDF (and other supported types in the future) inside the
`docs` directory that lives alongside this module. Run it via

python -m content.build_doc_payload

Optionally pass a specific file name (relative to the docs directory) as the
first argument: `python -m content.build_doc_payload my-file.pdf`.
"""

from __future__ import annotations

import json
import mimetypes
import sys
from pathlib import Path
from typing import Callable

BASE_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = BASE_DIR / "docs"
OUTPUT_DIR = Path(__file__).resolve().parent


class UnsupportedDocumentTypeError(RuntimeError):
    """Raised when we do not know how to parse the requested document."""


def _extract_text_pdf(path: Path) -> str:
    """Extract text from a PDF using whichever library is available."""

    try:
        from pypdf import PdfReader  # type: ignore
    except ModuleNotFoundError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Install either `pypdf` or `PyPDF2` to extract PDF content."
            ) from exc

    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        texts.append(page_text.strip())
    return "\n".join(filter(None, texts)).strip()


EXTRACTORS: dict[str, Callable[[Path], str]] = {
    ".pdf": _extract_text_pdf,
    # Future: add image/text extractors here.
}


def extract_content(path: Path) -> str:
    extractor = EXTRACTORS.get(path.suffix.lower())
    if not extractor:
        raise UnsupportedDocumentTypeError(f"Unsupported file type: {path.suffix}")
    return extractor(path)


def detect_mime(path: Path) -> str:
    mimetype, _ = mimetypes.guess_type(path.name)
    return mimetype or "application/octet-stream"


def build_payload(doc_path: Path) -> dict[str, str]:
    content_text = extract_content(doc_path)
    return {
        "content": content_text,
        "type": detect_mime(doc_path),
    }


def write_payload(doc_path: Path, payload: dict[str, str]) -> Path:
    output_path = OUTPUT_DIR / f"{doc_path.stem}.json"
    output_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    if not DOCS_DIR.exists():
        raise FileNotFoundError(f"Docs directory not found: {DOCS_DIR}")

    if len(sys.argv) > 1:
        target = DOCS_DIR / sys.argv[1]
        if not target.exists():
            raise FileNotFoundError(f"Document not found: {target}")
        doc_paths = [target]
    else:
        doc_paths = sorted(p for p in DOCS_DIR.iterdir() if p.is_file())

    if not doc_paths:
        raise FileNotFoundError(f"No files found in {DOCS_DIR}")

    for doc_path in doc_paths:
        payload = build_payload(doc_path)
        output_path = write_payload(doc_path, payload)
        print(f"Wrote payload for {doc_path.name} -> {output_path}")


if __name__ == "__main__":
    main()
