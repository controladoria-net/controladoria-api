from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List, Dict
import tempfile
import os
import shutil

from infra.factories.classificador_factory import create_classificar_documentos_usecase
from domain.entities.documento import DocumentoProcessar, ResultadoClassificacao
# Cria um router específico para o classificador
router = APIRouter(
    prefix="/classificador",
    tags=["Classificador"]
)

@router.post(
    "/processar/", 
    summary="Processa um ou mais documentos",
    response_model=Dict[str, List[ResultadoClassificacao]]
)
async def processar_documentos(
    files: List[UploadFile] = File(..., description="Um ou mais arquivos para classificar")
):
    """
    Recebe um ou mais arquivos (PDF, PNG, JPG), passa o stream
    para o classificador e retorna os resultados agrupados.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum arquivo enviado."
        )

    documentos_para_processar: List[DocumentoProcessar] = []
    # Não precisamos mais da lista de caminhos temporários

    try:
        # 1. Obter streams dos UploadFiles
        for i, file in enumerate(files):
            try:
                print(f"API: Arquivo [{i+1}/{len(files)}] {file.filename} obtido (stream).")
                
                # 4. Converter para entidade de domínio
                # Passamos o ponteiro do arquivo (file.file)
                documento = DocumentoProcessar(
                    file_object=file.file, # <-- Passa o file-like object
                    nome_arquivo_original=file.filename,
                    mimetype=file.content_type
                )
                documentos_para_processar.append(documento)

            except Exception as e:
                print(f"API: Erro ao obter stream do arquivo {file.filename}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao processar arquivo {file.filename}."
                )
            # NOTA: Não fechamos o arquivo (await file.close())
            # O FastAPI gerencia o ciclo de vida do stream do UploadFile
            # e o gateway do Gemini fará a leitura.

        # 2. Chamar a fábrica para obter o Usecase
        usecase = create_classificar_documentos_usecase()

        # 3. Executar o caso de uso
        resultados_agrupados = usecase.executar(documentos_para_processar)
        
        return resultados_agrupados

    except Exception as e:
        # Erro geral (ex: falha na factory, erro no usecase)
        print(f"API: Erro inesperado no processamento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro interno: {e}"
        )
    # Não precisamos mais do 'finally' para limpar arquivos