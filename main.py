from agent import GeminiAgent

# Identificação do usuário (pode ser ID, e-mail, etc.)
agente = GeminiAgent(user_id="walber_local")

print("🤖 Agente com memória via Redis iniciado (localhost).")
print("Digite 'limpar' para apagar memória ou 'sair' para encerrar.\n")

while True:
    user_input = input("Você: ")
    if user_input.lower() == "sair":
        break
    if user_input.lower() == "limpar":
        agente.limpar_memoria()
        print("🧹 Memória limpa!\n")
        continue

    resposta = agente.agente_responde(user_input)
    print("Agente:", resposta, "\n")
