from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List, Dict
import tempfile
import os
import shutil

from ....factories.classificador_factory import create_classificar_documentos_usecase
from domain.entities.documento import DocumentoProcessar, ResultadoClassificacao
from domain.entities.categorias import CategoriaDocumento

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

    print(f"API: Recebida requisição para processar {len(files)} arquivos.")
    
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
                
                print(f"API: Arquivo [{i+1}/{len(files)}] {file.filename} salvo em {temp_path}")
                
                # 4. Converter para entidade de domínio
                documento = DocumentoProcessar(
                    caminho_temporario=temp_path,
                    nome_arquivo_original=file.filename
                )
                documentos_para_processar.append(documento)
                caminhos_temporarios.append(temp_path)

            except Exception as e:
                print(f"API: Erro ao salvar arquivo temporário {file.filename}: {e}")
                # Se falhar ao salvar, limpa o que criou
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
        # Erro geral (ex: falha na factory, erro no usecase)
        print(f"API: Erro inesperado no endpoint /processar/: {e}")
        # Tenta criar um response de erro
        categoria_erro = CategoriaDocumento.ERRO_NO_PROCESSAMENTO_DA_API.value
        return {
            categoria_erro: [
                {
                    "categoria": categoria_erro,
                    "nome_arquivo": f.filename,
                    "formato_arquivo": os.path.splitext(f.filename)[1].replace('.',''),
                    "detalhe_erro": str(e)
                } for f in files
            ]
        }
    
    finally:
        # 7. Limpeza dos arquivos temporários
        print("API: Iniciando limpeza de arquivos temporários...")
        for path in caminhos_temporarios:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                    print(f"API: Arquivo temporário {path} deletado do disco.")
                except Exception as e:
                    print(f"API: AVISO - Falha ao deletar arquivo temporário {path}: {e}")
