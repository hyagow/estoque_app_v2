import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"

# Função para obter o tipo de usuário do token
def get_user_role(token):
    return token.split(":")[0]  # Exemplo de token no formato "role:token"

# Função para cadastrar o estoquista cadastrar os produtos
def cadastrar_produto(token):
    st.header("Cadastro de Produto")
    nome = st.text_input("Nome")
    categoria = st.text_input("Categoria")
    quantidade = st.number_input("Quantidade", min_value=0)
    preco = st.number_input("Preço", min_value=0.0)
    localizacao = st.text_input("Localização")
    nota_fiscal = st.text_input("Nota Fiscal")

    if st.button("Cadastrar"):
        produto = {
            "nome": nome,
            "categoria": categoria,
            "quantidade": quantidade,
            "preco": preco,
            "localizacao": localizacao,
            "nota_fiscal": nota_fiscal,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_URL}/produtos/", json=produto, headers=headers)
        if response.status_code == 200:
            st.success(response.json()["mensagem"])
        else:
            st.error("Erro ao cadastrar produto.")


# Função para listar os produtos que foram cadastrados pelo estoquista
def listar_produtos(token):
    st.header("Lista de Produtos")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/produtos/", headers=headers)
    if response.status_code == 200:
        produtos = response.json()
        for produto in produtos:
            st.write(
                f"**ID:** {produto['id']}, **Nome:** {produto['nome']}, **Categoria:** {produto['categoria']}, **Quantidade:** {produto['quantidade']}, **Preço:** {produto['preco']}, **Localização:** {produto['localizacao']}, **Nota Fiscal:** {produto['nota_fiscal']}"
            )
    else:
        st.error("Erro ao buscar produtos.")

# Função para o estoquista atualizar o estoque 
def atualizar_estoque(token):
    st.header("Atualizar Estoque")
    produto_id = st.number_input("ID do Produto", min_value=1)
    quantidade = st.number_input("Nova Quantidade", min_value=0)

    if st.button("Atualizar"):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(f"{API_URL}/produtos/{produto_id}", json={"quantidade": quantidade}, headers=headers)
        if response.status_code == 200:
            st.success(response.json()["mensagem"])
        else:
            st.error("Erro ao atualizar estoque.")

# Função para o estoquista cadastrar a movimentação
def cadastrar_movimentacao(token):
    st.header("Cadastro de Movimentação")

    produto_id = st.number_input("ID do Produto", min_value=1)
    quantidade = st.number_input("Quantidade", min_value=1)
    tipo = st.selectbox("Tipo", options=["entrada", "saida"])
    observacao = st.text_area("Observação")
    pedido_id = st.number_input("ID do Pedido", min_value=1)

    if st.button("Cadastrar Movimentação"):
        movimentacao = {
            "produto_id": produto_id,
            "quantidade": quantidade,
            "tipo": tipo,
            "observacao": observacao,
            "pedido_id": pedido_id,
            "data": datetime.now().isoformat(),
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_URL}/movimentacoes/", json=movimentacao, headers=headers)

        if response.status_code == 200:
            st.success(response.json()["mensagem"])
        else:
            st.error(f"Erro ao cadastrar movimentação: {response.json()}")

def solicitar_compra(token):
    st.header("Solicitar Compra")

    # Listar produtos disponíveis para solicitação
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/produtos/", headers=headers)
    if response.status_code == 200:
        produtos = response.json()
        produto_options = {produto['nome']: produto['id'] for produto in produtos}
        
        produto_selecionado = st.selectbox("Escolha um Produto", options=list(produto_options.keys()))
        quantidade = st.number_input("Quantidade", min_value=1)

        if st.button("Solicitar Compra"):
            solicitacao = {
                "produto_id": produto_options[produto_selecionado],
                "quantidade": quantidade,
            }
            response = requests.post(f"{API_URL}/compras/solicitar", json=solicitacao, headers=headers)
            if response.status_code == 200:
                st.success(response.json()["mensagem"])
            else:
                st.error("Erro ao solicitar compra.")
    else:
        st.error("Erro ao buscar produtos.")

def autorizar_compra(token):
    st.header("Autorizar Compra")

    # Listar as solicitações de compra
    solicitacoes = listar_solicitacoes(token)
    
    if not solicitacoes:
        st.warning("Nenhuma solicitação de compra encontrada.")
        return
    
    # Criar um seletor para escolher uma solicitação
    solicitacao_options = {f"ID: {solicitacao['id']} - Produto ID: {solicitacao['produto_id']} - Quantidade: {solicitacao['quantidade']}": solicitacao['id'] for solicitacao in solicitacoes}
    solicitacao_id = st.selectbox("Escolha uma Solicitação", options=list(solicitacao_options.keys()))

    # Obter o ID da solicitação selecionada
    selected_solicitacao_id = solicitacao_options[solicitacao_id]

    # Obter a quantidade da solicitação selecionada
    quantidade = next(sol['quantidade'] for sol in solicitacoes if sol['id'] == selected_solicitacao_id)

    if st.button("Autorizar Compra"):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_URL}/compras/autorizar", json={"produto_id": selected_solicitacao_id, "quantidade": quantidade}, headers=headers)
        
        if response.status_code == 200:
            st.success(response.json()["mensagem"])
        else:
            error_message = response.json().get("mensagem", "Erro desconhecido.")
            st.error(f"Erro ao autorizar compra: {error_message} (Código: {response.status_code})")


def relatorio_posicao_semanal(token):
    st.header("Relatório de Posição Semanal")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/relatorios/semanal/", headers=headers)
    
    if response.status_code == 200:
        relatorio = response.json()
        for item in relatorio:
            st.write(
                f"**Produto ID:** {item['produto_id']}, **Nome:** {item['nome']}, **Quantidade Atual:** {item['quantidade_atual']}, **Total Entrada:** {item['total_entrada']}, **Total Saída:** {item['total_saida']}, **Quantidade Final:** {item['quantidade_final']}"
            )
    else:
        st.error("Erro ao buscar relatório de posição semanal.")


def listar_movimentacoes(token):
    st.header("Movimentações de Produtos")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/movimentacoes/", headers=headers)
    if response.status_code == 200:
        movimentacoes = response.json()
        for mov in movimentacoes:
            st.write(
                f"**ID:** {mov['id']}, **Produto ID:** {mov['produto_id']}, **Tipo:** {mov['tipo']}, **Quantidade:** {mov['quantidade']}, **Data:** {mov['data']}"
            )
    else:
        st.error("Erro ao buscar movimentações.")


def listar_solicitacoes(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/compras/solicitacoes", headers=headers)
    
    if response.status_code == 200:
        return response.json()  # Retorna a lista de solicitações
    else:
        st.error("Erro ao listar solicitações de compra.")
        return []

def listar_minhas_solicitacoes(token):
    st.header("Minhas Solicitações de Compra")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/compras/solicitacoes/meus/", headers=headers)
    
    if response.status_code == 200:
        solicitacoes = response.json()
        if not solicitacoes:
            st.warning("Nenhuma solicitação de compra encontrada.")
            return
        
        for solicitacao in solicitacoes:
            st.write(
                f"**Produto ID:** {solicitacao['produto_id']}, **Quantidade:** {solicitacao['quantidade']}, **Status:** {solicitacao['status']}"
            )
    else:
        st.error("Erro ao buscar suas solicitações de compra.")


# Menu
st.sidebar.title("Menu")

# Simulação de autenticação
token = st.sidebar.text_input("Token de Acesso", type="password")  # Para simular a entrada do token
role = get_user_role(token) if token else None

if role == "estoquista":
    menu = st.sidebar.radio("Escolha uma opção:", [
        "Cadastrar Produto", 
        "Listar Produtos", 
        "Atualizar Estoque", 
        "Cadastrar Movimentação", 
        "Listar Movimentações"
    ])
    if menu == "Cadastrar Produto":
        cadastrar_produto(token)
    elif menu == "Listar Produtos":
        listar_produtos(token)
    elif menu == "Atualizar Estoque":
        atualizar_estoque(token)
    elif menu == "Cadastrar Movimentação":
        cadastrar_movimentacao(token)
    elif menu == "Listar Movimentações":
        listar_movimentacoes(token)

elif role == "usuario":
    menu = st.sidebar.radio("Escolha uma opção:", [
        "Solicitar Compra", 
        "Listar Minhas Solicitações",
        "Relatório de Posição Semanal",  # Nova opção
    ])
    if menu == "Solicitar Compra":
        solicitar_compra(token)
    elif menu == "Listar Produtos":
        listar_produtos(token)
    elif menu == "Listar Minhas Solicitações":
        listar_minhas_solicitacoes(token)
    elif menu == "Relatório de Posição Semanal":  # Nova opção
        relatorio_posicao_semanal(token)

elif role == "gerente":
    menu = st.sidebar.radio("Escolha uma opção:", [
        "Autorizar Compra", 
        "Listar Produtos", 
        "Listar Movimentações"
    ])
    if menu == "Autorizar Compra":
        autorizar_compra(token)
    elif menu == "Listar Produtos":
        listar_produtos(token)
    elif menu == "Listar Movimentações":
        listar_movimentacoes(token)

else:
    st.sidebar.warning("Por favor, insira um token de acesso válido.")
