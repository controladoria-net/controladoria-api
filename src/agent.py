# =====================================================
# Classe: GeminiAgent
# Modelo: gemini-2.0-flash-lite
# Descrição: Agente com memória persistente via Redis
# =====================================================

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from redis_config import get_redis_connection

class GeminiAgent:
    def __init__(
        self,
        user_id: str,
        model_name: str = "models/gemini-2.0-flash-lite",
        temperature: float = 0.2,
        top_k: int = 1,
        top_p: float = 0.3,
        max_output_tokens: int = 512
    ):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY não encontrada no .env")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.config = genai.types.GenerationConfig(
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            max_output_tokens=max_output_tokens
        )

        # 🔗 Conexão Redis
        self.redis = get_redis_connection()
        self.user_id = user_id
        self.key = f"memoria:{self.user_id}"

    # 🧠 Carregar memória do Redis
    def _carregar_memoria(self):
        memoria_json = self.redis.get(self.key)
        return json.loads(memoria_json) if memoria_json else []

    # 💾 Salvar memória no Redis
    def _salvar_memoria(self, memoria):
        self.redis.set(self.key, json.dumps(memoria))

    def agente_responde(self, prompt: str) -> str:
        memoria = self._carregar_memoria()

        # Monta o contexto conversacional
        contexto = "\n".join([
            f"Usuário: {m['usuario']}\nAgente: {m['agente']}"
            for m in memoria
        ])
        mensagem = f"{contexto}\nUsuário: {prompt}\nAgente:"

        response = self.model.generate_content(mensagem, generation_config=self.config)
        resposta = response.text.strip() if response.text else ""

        # Atualiza a memória e salva no Redis
        memoria.append({"usuario": prompt, "agente": resposta})
        if len(memoria) > 15:
            memoria.pop(0)
        self._salvar_memoria(memoria)

        return resposta

    def limpar_memoria(self):
        self.redis.delete(self.key)
