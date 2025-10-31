import google.generativeai as genai
import os
import json
from pydantic import ValidationError
from dotenv import load_dotenv

from domain.gateway.classificador_gateway import IClassificadorGateway
from domain.entities.documento import DocumentoProcessar, ResultadoClassificacao
from domain.entities.categorias import CategoriaDocumento
from ..prompts.prompt_classificador import PROMPT_MESTRE
from ..dto.gemini_dto import GeminiResponseDTO
from ..mapper.classificacao_mapper import ClassificacaoMapper

class GeminiClassificadorGateway(IClassificadorGateway):
    """
    Implementa o IClassificadorGateway usando a API Google Gemini.
    """
    def __init__(self):
        self.model = None
        self.generation_config = None

    def configurar(self):
        """
        Carrega a chave de API do arquivo .env e configura a API do Gemini.
        """
        if self.model:
            print("Gateway: Gemini já configurado.")
            return

        print("Gateway: Configurando API do Gemini...")
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Chave de API não encontrada (GOOGLE_API_KEY). Verifique seu arquivo .env")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name="gemini-2.5-flash")
            self.generation_config = genai.GenerationConfig(
                response_mime_type="application/json"
            )
            print("Gateway: Configuração do Gemini concluída com sucesso.")
        except Exception as e:
            print(f"Gateway: ERRO CRÍTICO NA INICIALIZAÇÃO DO GEMINI: {e}")
            raise

    def classificar(self, documento: DocumentoProcessar) -> ResultadoClassificacao:
        """
        Envia um documento para a API do Gemini, recebe um JSON com a categoria
        e mapeia para a entidade de domínio.
        """
        if not self.model:
            raise RuntimeError("Gateway não configurado. Chame .configurar() primeiro.")

        print(f"Gateway: Subindo o arquivo: {documento.caminho_temporario}...")
        arquivo_upload = None
        try:
            arquivo_upload = genai.upload_file(path=documento.caminho_temporario)
            print("Gateway: Arquivo enviado. Classificando...")

            response = self.model.generate_content(
                [PROMPT_MESTRE, arquivo_upload],
                generation_config=self.generation_config
            )
            
            # Validação Pydantic + Mapeamento
            response_dto = GeminiResponseDTO.model_validate_json(response.text)
            print(f"Gateway: Classificação recebida (DTO): {response_dto.categoria}")
            
            # Mapeia para a entidade de domínio
            resultado_entidade = ClassificacaoMapper.to_domain(
                response_dto=response_dto,
                documento_original_nome=documento.nome_arquivo_original,
                documento_original_formato=documento.formato_arquivo
            )
            
            return resultado_entidade

        except json.JSONDecodeError as e:
            print(f"Gateway: Erro ao decodificar JSON da API: {response.text if 'response' in locals() else 'N/A'}. Erro: {e}")
            return self._criar_resultado_erro(documento, CategoriaDocumento.ERRO_DE_FORMATO)
        
        except ValidationError as e:
            print(f"Gateway: Erro de validação Pydantic: {response.text}. Erro: {e}")
            return self._criar_resultado_erro(documento, CategoriaDocumento.ERRO_DE_FORMATO)
        
        except Exception as e:
            print(f"Gateway: Erro inesperado durante a classificação: {e}")
            return self._criar_resultado_erro(documento, CategoriaDocumento.ERRO_NA_CLASSIFICACAO)
        
        finally:
            # Garante a limpeza do arquivo no Gemini
            if arquivo_upload:
                try:
                    genai.delete_file(arquivo_upload.name)
                    print(f"Gateway: Arquivo {arquivo_upload.name} deletado do Gemini.")
                except Exception as e:
                    print(f"Gateway: AVISO - Falha ao deletar arquivo {arquivo_upload.name} do Gemini: {e}")
    
    def _criar_resultado_erro(self, documento: DocumentoProcessar, tipo_erro: CategoriaDocumento) -> ResultadoClassificacao:
        """Helper para criar uma entidade de resultado em caso de erro."""
        return ResultadoClassificacao(
            categoria=tipo_erro,
            nome_arquivo=documento.nome_arquivo_original,
            formato_arquivo=documento.formato_arquivo
        )
