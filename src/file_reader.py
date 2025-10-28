"""
Script: file_reader.py
Autor: Walber Vidigal
Descrição:
  Lê PDFs/imagens, envia ao modelo Gemini 2.0 Flash‑Lite
  usando os Descriptors definidos em document.py,
  permite escolher o tipo de documento (ou detectar),
  e salva os resultados no Redis via GeminiAgent.
"""

import os
import json
import argparse
from typing import Optional, Tuple

from dotenv import load_dotenv
import google.generativeai as genai

from agent import GeminiAgent
from document import REGISTRY


# 1) Configuração do modelo e caminhos
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY não encontrada no .env")

genai.configure(api_key=API_KEY)
MODEL_NAME = "models/gemini-2.0-flash-lite"

# Por padrão, considera a pasta 'pasta envio' na raiz do projeto (fora de src)
DEFAULT_PASTA_ENVIO = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, "pasta envio")
)


def _build_generation_config(**overrides):
    base = dict(temperature=0.2, top_p=0.3, top_k=1, max_output_tokens=1024)
    base.update(overrides)
    return genai.types.GenerationConfig(**base)


# 2) Detecção automática do tipo de documento (opcional)
def detectar_tipo_documento(uploaded_file) -> Optional[str]:
    opcoes = list(REGISTRY.keys())
    lista_opcoes = "\n".join(f"- {k}" for k in opcoes)
    prompt = (
        "Você é um classificador de documentos. Escolha o tipo que melhor "
        "representa o arquivo enviado a partir da lista. Responda somente "
        "com JSON válido no formato {\"tipo\": <string ou null>} onde o valor "
        "de 'tipo' deve ser exatamente uma das chaves abaixo.\n\n"
        f"Tipos disponíveis:\n{lista_opcoes}\n"
    )

    model = genai.GenerativeModel(MODEL_NAME)
    try:
        response = model.generate_content(
            [prompt, uploaded_file],
            generation_config=_build_generation_config(
                temperature=0.0, response_mime_type="application/json"
            ),
        )
        texto = (response.text or "").strip()
        if texto.startswith("```"):
            texto = texto.replace("```json", "").replace("```", "").strip()
        data = json.loads(texto)
        tipo = data.get("tipo")
        if tipo in REGISTRY:
            return tipo
        return None
    except Exception:
        return None


# 3) Análise com um Descriptor específico
def analisar_com_descriptor(uploaded_file, descriptor) -> Tuple[dict, str]:
    # Ideal: usar system_instruction do Descriptor
    model = genai.GenerativeModel(
        MODEL_NAME, system_instruction=descriptor.system_instruction
    )

    # Tenta usar JSON mode (quando disponível); caso falhe, volta ao básico
    gen_cfg_kwargs = {}
    if getattr(descriptor, "response_mime_type", None):
        gen_cfg_kwargs["response_mime_type"] = descriptor.response_mime_type

    config = _build_generation_config(**gen_cfg_kwargs)

    response = model.generate_content([uploaded_file], generation_config=config)
    texto = (response.text or "").strip()
    if texto.startswith("```"):
        texto = texto.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(texto)
    except json.JSONDecodeError:
        parsed = {"raw": texto}

    return parsed, texto


# 4) Execução principal sobre a pasta
def analisar_arquivos(pasta_envio: str, tipo_forcado: Optional[str] = None, auto: bool = False):
    agente = GeminiAgent(user_id="walber_local")

    if not os.path.isdir(pasta_envio):
        raise FileNotFoundError(f"Pasta não encontrada: {pasta_envio}")

    arquivos = [
        f
        for f in os.listdir(pasta_envio)
        if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))
    ]

    if not arquivos:
        print(f"Nenhum arquivo encontrado em: {pasta_envio}")
        return

    resultados: dict[str, dict] = {}
    print(f"{len(arquivos)} arquivo(s) encontrados em '{pasta_envio}'.\n")

    for arquivo in arquivos:
        caminho = os.path.join(pasta_envio, arquivo)
        print(f"Enviando '{arquivo}' para análise...")

        try:
            uploaded = genai.upload_file(caminho)

            # Seleção do tipo
            tipo_escolhido = tipo_forcado
            if not tipo_escolhido and auto:
                tipo_escolhido = detectar_tipo_documento(uploaded)

            if not tipo_escolhido:
                print(
                    "Não foi possível detectar o tipo automaticamente ou nenhum tipo foi informado. "
                    "Pulando arquivo."
                )
                resultados[arquivo] = {"erro": "tipo não identificado"}
                continue

            descriptor = REGISTRY[tipo_escolhido]
            resultado_json, resposta_texto = analisar_com_descriptor(uploaded, descriptor)

            # Persistência de memória no agente (Redis)
            contexto = (
                f"O documento '{arquivo}' foi analisado como {descriptor.name}.\n"
                f"Resultado:\n{json.dumps(resultado_json, ensure_ascii=False, indent=2)}"
            )
            agente.agente_responde(contexto)

            resultados[arquivo] = {
                "tipo": tipo_escolhido,
                "resultado": resultado_json,
            }
            print(f"OK: '{arquivo}' analisado e registrado.\n")

        except Exception as e:
            resultados[arquivo] = {"erro": str(e)}
            print(f"Falha ao analisar '{arquivo}': {e}\n")

    # Salva resultados agregados
    with open("resultado_analise.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("Resultados salvos em 'resultado_analise.json'.")
    print("Contextos também armazenados na memória do agente (Redis).")


def _parse_args():
    parser = argparse.ArgumentParser(description="Analisa documentos usando Gemini e Descriptors.")
    parser.add_argument(
        "--pasta",
        default=DEFAULT_PASTA_ENVIO,
        help=f"Pasta com PDFs/Imagens (padrão: {DEFAULT_PASTA_ENVIO})",
    )
    parser.add_argument(
        "--tipo",
        choices=sorted(REGISTRY.keys()),
        help="Força o tipo de documento a ser usado na análise.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Detecta automaticamente o tipo por arquivo e analisa com o Descriptor correspondente.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    # Se nenhum tipo e sem auto, oferece seleção rápida via entrada padrão
    doc_type = args.tipo
    if not doc_type and not args.auto:
        chaves = list(REGISTRY.keys())
        print("Selecione o tipo de documento (ou 0 para Auto):")
        for i, k in enumerate(chaves, start=1):
            desc = REGISTRY[k]
            label = f"{k}"
            if getattr(desc, "sigla", None):
                label += f" ({desc.sigla})"
            print(f"[{i}] {label} - {desc.name}")
        print("[0] Auto-detectar por arquivo")
        try:
            escolha = int(input("Sua escolha: ").strip() or "0")
        except ValueError:
            escolha = 0
        if escolha == 0:
            doc_type = None
            auto = True
        elif 1 <= escolha <= len(chaves):
            doc_type = chaves[escolha - 1]
            auto = False
        else:
            doc_type = None
            auto = True
    else:
        auto = bool(args.auto)

    analisar_arquivos(pasta_envio=args.pasta, tipo_forcado=doc_type, auto=auto)
