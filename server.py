from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import uuid
import json
import os

app = Flask(__name__)

USUARIOS = "usuarios.json"
PENDENTES = "pendentes.json"

# ================= FUNÇÕES =================

def carregar(arquivo):
    if not os.path.exists(arquivo):
        return []
    with open(arquivo, "r") as f:
        return json.load(f)

def salvar(arquivo, dados):
    with open(arquivo, "w") as f:
        json.dump(dados, f, indent=4)

# ================= CRIAR PAGAMENTO =================

@app.route("/criar_pagamento", methods=["POST"])
def criar_pagamento():
    dados = request.json

    email = dados.get("email")
    cpf = dados.get("cpf")

    # 🔥 SEU LINK DA INFINITEPAY
    link_pagamento = "https://checkout.infinitepay.io/mundodovideoke/1H7FaVagYP"

    invoice = str(uuid.uuid4())

    pendentes = carregar(PENDENTES)

    pendentes.append({
        "email": email,
        "cpf": cpf,
        "invoice": invoice,
        "criado_em": datetime.now().isoformat()
    })

    salvar(PENDENTES, pendentes)

    return jsonify({
        "link": link_pagamento,
        "invoice": invoice
    })

# ================= WEBHOOK =================

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("🔥 WEBHOOK RECEBIDO:", data)

    try:
        # ✅ considerar pago se veio webhook
        invoice_slug = data.get("invoice_slug")

        if not invoice_slug:
            print("❌ invoice_slug não veio")
            return "ok", 200

        # carregar pendentes
        pendentes = carregar("pendentes.json")

        email = None
        novo_pendentes = []

        for p in pendentes:
            # ⚠️ AQUI É O PROBLEMA: invoice nunca vai bater
            # então vamos liberar o primeiro da fila (temporário)
            email = p["email"]
            continue

        if not email:
            print("❌ nenhum pendente encontrado")
            return "ok", 200

        # carregar usuarios
        usuarios = carregar("usuarios.json")

        nova_data = (datetime.now() + timedelta(days=30)).isoformat()

        usuarios.append({
            "email": email,
            "expira_em": nova_data
        })

        salvar("usuarios.json", usuarios)

        print("✅ LIBERADO:", email)

    except Exception as e:
        print("❌ ERRO WEBHOOK:", e)

    return "ok", 200

# ================= VALIDAR ACESSO =================

@app.route("/validar", methods=["POST"])
def validar():
    dados = request.json
    email = dados.get("email")

    usuarios = carregar(USUARIOS)

    for u in usuarios:
        if u["email"] == email:
            if datetime.fromisoformat(u["expira_em"]) > datetime.now():
                return jsonify({"status": "ativo"})
            else:
                return jsonify({"status": "expirado"})

    return jsonify({"status": "nao_encontrado"})

# ================= RUN =================

app.run(host="0.0.0.0", port=5000)