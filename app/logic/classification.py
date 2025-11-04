# Em: app/logic/classification.py

from app.models.schemas import PescadorInput
from datetime import date
from dateutil.relativedelta import relativedelta

# -----------------------------------------------------------------
# ARQUIVO 2: O MÓDULO DE SCORE (LÓGICA AJUSTADA SEM O REQUISITO DE PENA)
# -----------------------------------------------------------------

# Requisitos #12 e #13: Define as exceções de benefícios permitidas 
BENEFICIOS_PERMITIDOS = ["pensao_por_morte", "auxilio_acidente"]

def processar_classificacao(dados: PescadorInput) -> dict:
    
    score = 0
    # MUDANÇA IMPORTANTE: O total de critérios agora é 7
    total_criterios = 7
    pendencias = []
    
    # --- Checagens com dados que JÁ TEMOS ---

    # 1. RGP Ativo (Requisito #4)
    if dados.rgp_ativo:
        score += 1
    else:
        pendencias.append("RGP não está ativo ou é inválido.")

    # 3. Comprovação 12m (Requisitos #1, #6, #7) [cite: 47, 86-87]
    if dados.comprovou_atividade_ultimos_12m:
        score += 1
    else:
        pendencias.append("Não comprovou atividade pesqueira nos últimos 12 meses.")

    # 4. Pesca como Renda Principal (Requisitos #3, #9)
    if dados.pesca_e_principal_renda:
        score += 1
    else:
        pendencias.append("Pesca não é a principal fonte de renda.")

    # 5. Sem Vínculo Empregatício (Requisito #8)
    if not dados.possui_vinculo_emprego_ativo:
        score += 1
    else:
        pendencias.append("Possui vínculo de emprego formal ativo.")

    # --- Checagens que dependem dos DADOS FALTANTES ---

    # 2. RGP Antiguidade 1 ano (Requisito #5)
    if dados.defeso_data_inicio is not None:
        data_limite_rgp = dados.defeso_data_inicio - relativedelta(years=1)
        if dados.rgp_data_emissao <= data_limite_rgp:
            score += 1
        else:
            pendencias.append(f"RGP com menos de 1 ano (data limite era: {data_limite_rgp}).")
    else:
        pendencias.append("Não foi possível checar a antiguidade do RGP (data do defeso ausente).")

    # 6. Sem Benefício Incompatível (Requisitos #10, #12, #13) 
    if dados.lista_beneficios_ativos is not None:
        incompativel_encontrado = False
        for beneficio in dados.lista_beneficios_ativos:
            if beneficio.lower().strip() not in BENEFICIOS_PERMITIDOS:
                incompativel_encontrado = True
                pendencias.append(f"Recebe benefício incompatível: {beneficio}.")
                break
        if not incompativel_encontrado:
            score += 1
    else:
        pendencias.append("Não foi possível checar benefícios (lista de benefícios ausente).")

    # 7. (ERA A CHECAGEM DE PENA) - REMOVIDO
    
    # 8. (AGORA É A CHECAGEM 7) Prazo do Requerimento (Requisito #14)
    if dados.requerimento_data is not None and dados.defeso_data_inicio is not None:
        if dados.requerimento_data >= dados.defeso_data_inicio:
            score += 1
        else:
            pendencias.append("Requerimento feito fora do prazo legal do defeso.")
    else:
        pendencias.append("Não foi possível checar o prazo do requerimento (datas ausentes).")
        
    # --- Classificação Final (COM MUDANÇA PARA %) ---
    
    # Cálculo da Porcentagem
    porcentagem = 0
    if total_criterios > 0:
        porcentagem = (score / total_criterios) * 100
    else:
        porcentagem = 0 # Evita divisão por zero

    status_final = "Apto" if score == total_criterios else "Não Apto"
    
    return {
        "status": status_final,
        "score_texto": f"{porcentagem:.0f}%", # Formata para "57%", "100%", etc.
        "pendencias": pendencias
    }