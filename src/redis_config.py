import os
from dotenv import load_dotenv
import redis

load_dotenv()

def get_redis_connection():
    return redis.StrictRedis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        password=os.getenv("REDIS_PASSWORD", None),
        decode_responses=True
    )

def echo_test():
    """
    Testa a conexão com o Redis local.
    Retorna 'PONG' se estiver funcionando corretamente.
    """
    try:
        r = get_redis_connection()
        resposta = r.ping()
        if resposta:
            print("✅ Conexão com Redis bem-sucedida! (respondeu PONG)")
        else:
            print("⚠️ Redis respondeu algo inesperado.")
    except Exception as e:
        print("❌ Erro ao conectar com Redis:", str(e))


# Teste manual (executado apenas se rodar diretamente este arquivo)
if __name__ == "__main__":
    echo_test()
