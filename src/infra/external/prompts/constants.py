from src.domain.entities.document import DocumentClassification

PROMPT_COMMON_ENV_VARS = {
    "BASE_SYSTEM_PROMPT": """
        ⚠️ Regras Gerais:
        - Responda apenas com JSON válido;
        - Se a informação não aparecer, não a inclua;
        - Utilize datas no formato YYYY-MM-DD;
        - Os documentos podem estar em formato PDF ou imagem (JPG/PNG);
        - Sempre identifique o tipo de documento com base nos termos mais evidentes no conteúdo;
        - Se não for possível identificar o documento, retorne um JSON vazio: {};
        - Não inclua explicações ou comentários fora do JSON.
        - Considere que os documentos podem conter erros de OCR e ruídos no texto extraído.
        - Não invente informações que não estejam presentes no texto extraído do documento.

        Os documentos podem estar no formato PDF ou imagem (JPG/PNG). Caso seja uma imagem utilize técnicas de
        OCR para extrair o texto, e também considere que o texto extraído pode conter erros de OCR e ruídos no texto.
    """,
    "DOCUMENT_CATEGORIES_ENUMERATION": "\n".join(
        f"{idx}. {categoria.value}"
        for idx, categoria in enumerate(DocumentClassification, start=1)
    ),
}
