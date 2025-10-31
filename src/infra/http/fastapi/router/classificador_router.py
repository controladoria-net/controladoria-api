from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List, Dict
import tempfile
import os
import shutil

from ....factories.classificador_factory import create_classificar_documentos_usecase
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
    Recebe um ou mais arquivos (PDF, PNG, JPG), classifica cada um usando
    a IA do Gemini e retorna um JSON com os resultados agrupados.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Nenhum arquivo enviado."
        )

    
    documentos_para_processar: List[DocumentoProcessar] = []
    caminhos_temporarios: List[str] = []
    
    try:
        # 1. Lidar com UploadFiles e criar arquivos temporários
        for i, file in enumerate(files):
            temp_path = None
            try:
                suffix = os.path.splitext(file.filename)[1]
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    shutil.copyfileobj(file.file, temp_file)
                    temp_path = temp_file.name
                
                
                # 4. Converter para entidade de domínio
                documento = DocumentoProcessar(
                    caminho_temporario=temp_path,
                    nome_arquivo_original=file.filename
                )
                documentos_para_processar.append(documento)
                caminhos_temporarios.append(temp_path)

            except Exception as e:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao salvar arquivo {file.filename}."
                )
            finally:
                await file.close()

        # 2. Chamar a fábrica para obter o Usecase
        use_case = create_classificar_documentos_usecase()
        
        # 5. Chamar o Usecase
        resultados_agrupados = use_case.execute(documentos_para_processar)
        
        # 6. Retornar a resposta
        return resultados_agrupados

    except Exception as e:
        raise HTTPException(  
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  
            detail=f"Erro inesperado no processamento dos arquivos: {str(e)}"  
        )  
    
    finally:
        # 7. Limpeza dos arquivos temporários
        for path in caminhos_temporarios:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception as e:
                    raise e