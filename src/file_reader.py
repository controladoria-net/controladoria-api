# =====================================================
# Script: file_reader.py
# Autor: Walber Vidigal
# Descrição:
#   Lê todos os PDFs e imagens da pasta "pasta envio",
#   envia diretamente para o modelo Gemini 2.0 Flash-Lite
#   e salva as respostas na memória do agente (Redis),
#   permitindo perguntas posteriores sobre os documentos.
# =====================================================

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from agent import GeminiAgent  # Importa o agente com memória

# 1️⃣ Carrega variáveis de ambiente
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ Chave GEMINI_API_KEY não encontrada no .env")

# 2️⃣ Configura o modelo Gemini 2.0 Flash-Lite
genai.configure(api_key=API_KEY)
MODEL_NAME = "models/gemini-2.0-flash-lite"

# 3️⃣ Pasta onde estão os arquivos
PASTA_ENVIO = "pasta envio"

# 4️⃣ Prompt aprimorado de instruções
PROMPT_BASE = """
  Você é um analista jurídico especializado em processos de pescadores profissionais.
  Analise o documento enviado (PDF ou imagem) e identifique se ele é um:
  1️⃣ Certificado de Regularidade / Carteira RGP, ou
  2️⃣ CAEPF (Cadastro de Atividade Econômica da Pessoa Física), ou
  3️⃣ Comprovante de Residência, ou
  4️⃣ CNIS (Cadastro Nacional de Informações Sociais).

  ⚠️ Regras Gerais:
  - Responda apenas com JSON válido.
  - Se a informação não aparecer, escreva "Não disponível".
  - Utilize datas no formato DD/MM/AAAA.
  - Os documentos podem estar em formato PDF ou imagem (JPG/PNG).
  - Sempre identifique o tipo de documento com base nos termos mais evidentes no conteúdo.

  📜 Regras específicas:

  - Para Certificado de Regularidade (Carteira RGP):
    - Procure expressões como "Certificado de Registro", "RGP", "Registro Geral da Pesca".
    - Retorne apenas a data do primeiro registro, normalmente indicada por "Data do Primeiro Registro" ou similar.

  - Para CAEPF:
    - Procure expressões como "Cadastro de Atividade Econômica da Pessoa Física" ou "CAEPF".
    - Identifique a data de início da atividade e, se disponível, o tipo de pesca (Água Doce, Água Salgada, etc.).

  - Para Comprovantes de Residência (contas de energia, água, telefone, etc.):
    - Procure e retorne **a data de vencimento da fatura** como `Data_vencimento`.
    - Use expressões como “Vencimento”, “Venc.”, “Data de Venc.” ou similares.
    - Priorize essa data mesmo que haja outras datas (emissão, leitura, referência, etc.).
    - Inclua também nome do titular e endereço se disponíveis.

  - Para CNIS (Cadastro Nacional de Informações Sociais):
    - Procure expressões como "CNIS", "Cadastro Nacional de Informações Sociais", "Extrato Previdenciário" ou "INSS".
    - Extraia:
      - Nome completo do segurado.
      - CPF e NIT.
      - Vínculos empregatícios, incluindo nome da empresa, CNPJ, e datas de início e fim.
      - Indicação de segurado especial, se constar.
    - Verifique se há **período aquisitivo do defeso**, considerando os 12 meses anteriores à data mais recente do extrato.
    - Utilize a data mais recente do documento (ex: data do extrato ou data final de vínculo) como referência para cálculo do período aquisitivo.
    - Caso apareçam benefícios ativos ou outros vínculos, liste-os.

  📘 Campos esperados:

  - Se for um Certificado de Regularidade:
    {
      "CERTIFICADO_DE_REGULARIDADE": {
        "Data_primeiro_registro": "..."
      }
    }

  - Se for um CAEPF:
    {
      "CAEPF": {
        "Data_inicio_atividade": "...",
        "Tipo_pesca": "(Água doce, Água salgada, ou Não disponível)"
      }
    }

  - Se for um Comprovante de Residência (como contas de energia, água, telefone, etc.):
    {
      "COMPROVANTE_DE_RESIDENCIA": {
        "Data_vencimento": "..."
      }
    }

  - Se for um CNIS (Cadastro Nacional de Informações Sociais):
    {
      "CNIS": {
        "Nome": "...",
        "CPF": "...",
        "NIT": "...",
        "Vinculos_empregaticios": [
          {
            "Empresa": "...",
            "CNPJ": "...",
            "Data_inicio": "...",
            "Data_fim": "...",
            "Tipo_vinculo": "(Empregado, Segurado Especial, etc.)"
          }
        ],
        "Possui_beneficio_ativo": "(Sim ou Não)",
        "Periodo_aquisitivo_defeso": {
          "Data_inicio": "...",
          "Data_fim": "..."
        }
      }
    }
"""



# 5️⃣ Função principal
def analisar_arquivos():
    # Inicializa o agente com memória
    agente = GeminiAgent(user_id="walber_local")

    resultados = {}
    arquivos = [f for f in os.listdir(PASTA_ENVIO) if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))]

    if not arquivos:
        print("⚠️ Nenhum arquivo encontrado na pasta:", PASTA_ENVIO)
        return

    print(f"📂 {len(arquivos)} arquivo(s) encontrados na pasta '{PASTA_ENVIO}'. Enviando para análise...\n")

    for arquivo in arquivos:
        caminho = os.path.join(PASTA_ENVIO, arquivo)
        print(f"📤 Enviando '{arquivo}' para o modelo...")

        try:
            # Faz upload do arquivo para o Gemini
            uploaded_file = genai.upload_file(caminho)

            # Envia o arquivo + prompt ao modelo
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content(
                [PROMPT_BASE, uploaded_file],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    top_p=0.3,
                    top_k=1,
                    max_output_tokens=1024
                )
            )

            resposta = response.text.strip() if response.text else "Sem resposta"

            # 🧩 Limpa blocos de código Markdown
            if resposta.startswith("```"):
                resposta = resposta.replace("```json", "").replace("```", "").strip()

            # 🧠 Tenta converter em JSON válido
            try:
                resposta_json = json.loads(resposta)
                resultados[arquivo] = resposta_json
            except json.JSONDecodeError:
                resultados[arquivo] = resposta

            # 🔹 Armazena o contexto no Redis via agente
            contexto_memoria = f"O documento '{arquivo}' foi analisado e retornou os seguintes dados:\n{resposta}"
            agente.agente_responde(contexto_memoria)

            print(f"✅ Análise concluída e registrada na memória para '{arquivo}'.\n")


        except Exception as e:
            resultados[arquivo] = f"❌ Erro: {str(e)}"
            print(f"❌ Falha ao analisar '{arquivo}': {str(e)}\n")

    # Salva resultados em JSON local
    with open("resultado_analise.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("📑 Análises concluídas e salvas em 'resultado_analise.json'.")
    print("🧠 Contextos também armazenados na memória do agente (Redis).")


# 6️⃣ Executar script diretamente
if __name__ == "__main__":
    analisar_arquivos()
