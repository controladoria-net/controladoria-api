from __future__ import annotations
import json
import tempfile
import os
from pydantic import ValidationError
from dotenv import load_dotenv

import google.genai as genai

from domain.gateway.classificador_gateway import IClassificadorGateway
from domain.entities.documento import DocumentoProcessar, ResultadoClassificacao
from domain.entities.categorias import CategoriaDocumento
from infra.external.prompts.prompt_classificador import PROMPT_MESTRE
from infra.external.dto.gemini_dto import GeminiResponseDTO
from infra.external.mapper.classificacao_mapper import ClassificacaoMapper


class GeminiClassificadorGateway(IClassificadorGateway):

    def __init__(self):
        self.model_name: str = "gemini-2.5-flash"
        self.generation_config: dict | None = {"response_mime_type": "application/json"}

    def configurar(self):
        load_dotenv()

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Chave de API não encontrada (GOOGLE_API_KEY). Configure a variável de ambiente.")

                
        self.client = genai.Client(api_key=api_key)

    def classificar(self, documento: DocumentoProcessar) -> ResultadoClassificacao:
        tmp_path = None
        try:
            # 1) lê bytes do stream
            documento.file_object.seek(0)
            raw = documento.file_object.read()
            if isinstance(raw, str):
                raw_bytes = raw.encode("utf-8")
            else:
                raw_bytes = raw

            # 2) grava em arquivo temporário (NamedTemporaryFile) — fornece compatibilidade máxima com client.files.upload
            suffix = ""
            try:
                _, ext = os.path.splitext(documento.nome_arquivo_original or "")
                suffix = ext if ext else ""
            except Exception:
                suffix = ""

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            try:
                tmp.write(raw_bytes)
                tmp.flush()
                tmp_path = tmp.name
            finally:
                tmp.close()

            # 3) upload via client.files.upload(file=path)
            uploaded = self.client.files.upload(
                file=tmp_path,
                config={
                    "mime_type": documento.mimetype or "application/octet-stream",
                    "display_name": documento.nome_arquivo_original or "uploaded_file",
                },
            )

            file_uri = getattr(uploaded, "uri", None) or getattr(uploaded, "name", None) or getattr(uploaded, "id", None)
            uploaded_mime = getattr(uploaded, "mime_type", None) or documento.mimetype

            if not file_uri:
                part_for_contents = uploaded
            else:
                try:
                    part_for_contents = genai.types.Part.from_uri(file_uri=file_uri, mime_type=uploaded_mime)
                except Exception:
                    part_for_contents = {"file_uri": file_uri, "mime_type": uploaded_mime}

            # 5) chamada ao modelo pedindo JSON
            contents = [
                {
                    "role": "user",
                    "parts": [
                        {"text": PROMPT_MESTRE},
                        part_for_contents,
                    ],
                }
            ]

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=self.generation_config,
            )

            # 6) interpretar retorno (texto JSON ou conteúdo envelopado)
            text = getattr(response, "text", None)
            if not text:
                candidates = getattr(response, "candidates", None)
                if candidates and len(candidates) > 0:
                    cand = candidates[0]
                    content = getattr(cand, "content", None)
                    if content and getattr(content, "parts", None):
                        p = content.parts[0]
                        text = getattr(p, "text", None) or getattr(cand, "text", None)
            if not text:
                raise ValueError("Resposta vazia do modelo Gemini.")

            try:
                response_json = json.loads(text)
            except json.JSONDecodeError:
                s, e = text.find("{"), text.rfind("}")
                if s != -1 and e != -1 and e > s:
                    response_json = json.loads(text[s : e + 1])
                else:
                    raise

            response_dto = GeminiResponseDTO.model_validate(response_json)

            mimetype_normalizado = self._normalizar_mimetype(documento.mimetype)
            return ClassificacaoMapper.to_domain(
                response_dto=response_dto,
                documento=documento,
                gemini_file=file_uri if file_uri else None,
                mimetype=mimetype_normalizado,
            )   

        except (json.JSONDecodeError, ValidationError) as e:
            return self._criar_resultado_erro(documento, CategoriaDocumento.ERRO_DE_FORMATO)

        except Exception as e:
            return self._criar_resultado_erro(documento, CategoriaDocumento.ERRO_NA_CLASSIFICACAO)

        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass

    def _normalizar_mimetype(self, mimetype: str | None) -> str:
        if not mimetype:
            return "application/octet-stream"
        if "/" not in mimetype:
            if mimetype.lower() in ["pdf", "x-pdf"]:
                return "application/pdf"
            elif mimetype.lower() in ["png", "jpeg", "jpg", "gif"]:
                return f"image/{mimetype.lower()}"
            else:
                return f"application/{mimetype.lower()}"
        return mimetype


    def _criar_resultado_erro(self, documento: DocumentoProcessar, tipo_erro: CategoriaDocumento) -> ResultadoClassificacao:
        return ResultadoClassificacao(
            classificacao=tipo_erro,
            confianca=0.0,
            arquivo=documento.nome_arquivo_original,
            mimetype=documento.mimetype,
        )