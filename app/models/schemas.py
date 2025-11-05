# Em: app/models/schemas.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import date

# -----------------------------------------------------------------
# ARQUIVO 1: OS "MOLDES" (AJUSTADO SEM O REQUISITO DE PENA)
# -----------------------------------------------------------------

class PescadorInput(BaseModel):
    """
    Define a estrutura do JSON que esperamos receber.
    O campo 'possui_pena_privativa_liberdade' FOI REMOVIDO.
    """
    
    # --- Dados que assumimos que a extração JÁ TEM ---
    rgp_ativo: bool
    rgp_data_emissao: date
    comprovou_atividade_ultimos_12m: bool
    pesca_e_principal_renda: bool
    possui_vinculo_emprego_ativo: bool
    
    
    # --- PONTO DE ADAPTAÇÃO 1 (Extração) ---
    lista_beneficios_ativos: Optional[List[str]] = None

    # --- PONTO DE ADAPTAÇÃO 2 (Front-end) ---
    defeso_data_inicio: Optional[date] = None
    requerimento_data: Optional[date] = None


class ClassificationResponse(BaseModel):
    """
    Define a estrutura EXATA do JSON que vamos responder.
    """
    status: str
    score_texto: str
    pendencias: List[str]