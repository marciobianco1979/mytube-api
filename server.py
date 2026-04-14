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
        invoice_slug = data.get("invoice_slug")

        if not invoice_slug:
            print("❌ invoice_slug não veio")
            return "ok", 200

        # carregar pendentes
        pendentes = carregar(PENDENTES)

        if not pendentes:
            print("❌ nenhum pendente")
            return "ok", 200

        # 🔥 pega o PRIMEIRO da fila (mais seguro que antes)
        cliente = pendentes[0]
        email = cliente["email"]

        # remove da fila
        pendentes.pop(0)
        salvar(PENDENTES, pendentes)

        # carregar usuarios
        usuarios = carregar(USUARIOS)

        nova_data = (datetime.now() + timedelta(days=30)).isoformat()

        # verifica se já existe (renovação)
        encontrado = False
        for u in usuarios:
            if u["email"] == email:
                u["expira_em"] = nova_data
                encontrado = True
                print("🔁 Usuário renovado:", email)
                break

        if not encontrado:
            usuarios.append({
                "email": email,
                "expira_em": nova_data
            })
            print("✅ Novo usuário liberado:", email)

        salvar(USUARIOS, usuarios)

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

# ================= RUN (IMPORTANTE PARA RENDER) =================

import os
port = int(os.environ.get("PORT", 5000))

app.run(host="0.0.0.0", port=port)
