from fastapi import APIRouter, Body

from infra.factories.create_legal_case_gateway import create_legal_case_gateway
from infra.http.dto.general_response_dto import GeneralResponseDTO
from infra.http.dto.legal_case_request_dto import LegalCaseRequestDTO

router = APIRouter(prefix="/processos", tags=["Processos"])

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

    gateway = create_legal_case_gateway()

    for number in request_dto.process_numbers:
        print(f"INFO: Consultando API externa para {number}")
        try:
            legal_case = gateway.find_case_by_number(number)

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
            print(f"ERROR: Falha ao consultar o gateway para {number}: {e}")
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
