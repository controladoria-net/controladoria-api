# Em: app/main.py

from fastapi import FastAPI, APIRouter  # 1. IMPORTAMOS O APIRouter
from app.models.schemas import PescadorInput, ClassificationResponse
from app.logic.classification import processar_classificacao

# -----------------------------------------------------------------
# ARQUIVO 4: A API (AJUSTADO PARA ARQUITETURA DO PO)
# -----------------------------------------------------------------

# Cria a instância da aplicação principal
app = FastAPI(
    title="API de Classificação - Seguro Defeso",
    description="Processa dados de pescadores (baseado nos critérios da Advocacia Cavaignac) e retorna a aptidão para o benefício.",
    version="1.0.0"
)

# 2. CRIAMOS O "ROTEADOR" DA NOSSA EQUIPE
# Vamos usar o prefixo "/score_aptidao" (seguindo o exemplo do PO)
# (Vocês podem mudar "score_aptidao" para o nome que o PO preferir)
router = APIRouter(
    prefix="/score_aptidao"
)


# 3. MUDAMOS DE @app.post PARA @router.post
@router.post("/classificar", 
             response_model=ClassificationResponse,
             summary="Classifica um Pescador como Apto ou Não Apto")
def endpoint_classificar(dados_do_pescador: PescadorInput):
    """
    Este endpoint recebe o JSON do pescador e 
    retorna o score de aptidão.
    """
    resultado = processar_classificacao(dados_do_pescador)
    return resultado

# (Podemos adicionar outros endpoints da nossa equipe aqui no futuro)
# @router.get("/status_criterios")
# def get_status():
#    return {"status": "ok"}


# 4. "PLUGAMOS" O NOSSO ROTEADOR NA API PRINCIPAL
app.include_router(router)


# O endpoint raiz continua na 'app' principal como um "health check"
@app.get("/", summary="Verifica status da API Principal")
def read_root():
    return {"status": "API de Classificação de Seguro Defeso está online."}