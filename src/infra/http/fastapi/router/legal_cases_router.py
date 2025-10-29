import logging
from fastapi import APIRouter, Body

from src.infra.http.dto.general_response_dto import GeneralResponseDTO
from src.infra.http.dto.legal_case_request_dto import LegalCaseRequestDTO
from src.infra.factories.create_find_legal_case_use_case import (
    create_find_legal_case_use_case,
)

router = APIRouter(prefix="/processos", tags=["Processos"])
logger = logging.getLogger(__name__)

# ajustar
# @router.get("/processos/atualizar")
# async def forcar_atualizacao():
#     """
#     Força atualização manual de todos os processos salvos.
#     """
#     await atualizar_processos()
#     return {"message": "Atualização forçada concluída"}


# revisar
# @router.get("/processos/{legal_case_id:regex(\d{20})}", response_model=LegalCase)
# async def obter_processo(legal_case_id: str):
#     """
#     Retorna os dados completos de um processo específico.
#     """
#     if legal_case_id not in processos_db:
#         raise HTTPException(status_code=404, detail="Processo não encontrado")
#     return processos_db[numero]


@router.post("/consultar", response_model=GeneralResponseDTO)
async def find_legal_cases(request_dto: LegalCaseRequestDTO = Body(...)):
    success_results = []
    error_list = []

    use_case = create_find_legal_case_use_case()

    for number in request_dto.process_numbers:
        logger.info("Consultando API externa para %s", number)
        try:
            legal_case = use_case.execute(number)

            if legal_case:
                success_results.append(legal_case)
            else:
                error_list.append(
                    {
                        "process_number": number,
                        "message": "Processo não encontrado em nenhuma das fontes de dados.",
                    }
                )

        except Exception as e:
            # Erro: falha na comunicação com a API ou outro erro inesperado
            logger.error("Falha ao consultar o gateway para %s: %s", number, e)
            error_list.append(
                {
                    "process_number": number,
                    "message": f"Ocorreu um erro inesperado ao consultar o processo. Detalhe: {str(e)}",
                }
            )

    return GeneralResponseDTO(
        data=success_results if success_results else None,
        errors=error_list if error_list else None,
    )
