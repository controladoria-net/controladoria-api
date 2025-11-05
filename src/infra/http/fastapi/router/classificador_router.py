from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List, Dict


from infra.factories.classificador_factory import create_classificar_documentos_usecase
from domain.entities.documento import DocumentoProcessar, ResultadoClassificacao

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

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum arquivo enviado."
        )

    documentos_para_processar: List[DocumentoProcessar] = []

    try:
        # 1. Obter streams dos UploadFiles
        for i, file in enumerate(files):
            try:            
                # 4. Converter para entidade de domínio
                documento = DocumentoProcessar(
                    file_object=file.file, 
                    nome_arquivo_original=file.filename,
                    mimetype=file.content_type
                )
                documentos_para_processar.append(documento)

            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao processar arquivo {file.filename}."
                )


        # 2. Chamar a fábrica para obter o Usecase
        usecase = create_classificar_documentos_usecase()

        # 3. Executar o caso de uso
        resultados_agrupados = usecase.executar(documentos_para_processar)
        
        return resultados_agrupados

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro interno: {e}"
        )
