from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from database import get_db_connection
from typing import List
from datetime import datetime, timedelta

app = FastAPI()


# Modelos
class Produto(BaseModel):
    nome: str
    categoria: str
    quantidade: int
    preco: float
    localizacao: str
    nota_fiscal: str


class SolicitarCompra(BaseModel):
    produto_id: int
    quantidade: int


class Movimentacao(BaseModel):
    produto_id: int
    tipo: str
    quantidade: int
    pedido_id: int
    observacao: str


class Usuario(BaseModel):
    username: str
    password: str
    role: str


class AutorizarCompra(BaseModel):
    produto_id: int
    quantidade: int


# Simulação de usuários
USUARIOS = {
    "estoquista": {"username": "estoquista", "password": "senha", "role": "estoquista"},
    "usuario": {"username": "usuario", "password": "senha", "role": "usuario"},
    "gerente": {"username": "gerente", "password": "senha", "role": "gerente"},
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Rota de token de acesso: gerente, estoquista e usuário
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USUARIOS.get(form_data.username)
    if user and user["password"] == form_data.password:
        return {
            "access_token": f"{user['role']}:{form_data.username}",
            "token_type": "bearer",
        }
    raise HTTPException(status_code=400, detail="Usuário ou senha incorretos.")


def get_user_role(token: str):
    return token.split(":")[0]


# Rota de criação de produto: estoquista
@app.post("/produtos/", response_model=dict)
async def create_produto(produto: Produto, token: str = Depends(oauth2_scheme)):
    role = get_user_role(token)
    if role != "estoquista":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    if not produto.nota_fiscal:
        raise HTTPException(status_code=400, detail="Nota fiscal é obrigatória.")

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO produtos (nome, categoria, quantidade, preco, localizacao, nota_fiscal) VALUES (?, ?, ?, ?, ?, ?)",
            (
                produto.nome,
                produto.categoria,
                produto.quantidade,
                produto.preco,
                produto.localizacao,
                produto.nota_fiscal,
            ),
        )
        conn.commit()
        return {"mensagem": "Produto cadastrado com sucesso!"}


# Rota de leitura de produto: estoquista e usuário
@app.get("/produtos/", response_model=List[dict])
async def read_produtos(token: str = Depends(oauth2_scheme)):
    with get_db_connection() as conn:
        produtos = conn.execute("SELECT * FROM produtos").fetchall()
        return [dict(produto) for produto in produtos]


# Rota de leitura de produto: estoquista
@app.put("/produtos/{produto_id}", response_model=dict)
async def update_produto(
    produto_id: int, produto: Produto, token: str = Depends(oauth2_scheme)
):
    role = get_user_role(token)
    if role != "estoquista":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE produtos SET nome = ?, categoria = ?, quantidade = ?, preco = ?, localizacao = ?, nota_fiscal = ? WHERE id = ?",
            (
                produto.nome,
                produto.categoria,
                produto.quantidade,
                produto.preco,
                produto.localizacao,
                produto.nota_fiscal,
                produto_id,
            ),
        )
        conn.commit()
    return {"mensagem": "Produto atualizado com sucesso!"}


# Rota de exclusação de produto: gerente
@app.delete("/produtos/{produto_id}", response_model=dict)
async def delete_produto(produto_id: int, token: str = Depends(oauth2_scheme)):
    role = get_user_role(token)
    if role != "estoquista":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    with get_db_connection() as conn:
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conn.commit()
    return {"mensagem": "Produto deletado com sucesso!"}


# Rota de criação de movimentação de produto: estoquista
@app.post("/movimentacoes/", response_model=dict)
async def create_movimentacao(
    movimentacao: Movimentacao, token: str = Depends(oauth2_scheme)
):
    role = get_user_role(token)
    if role != "estoquista":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO movimentacoes (produto_id, tipo, quantidade, data, pedido_id, observacao) VALUES (?, ?, ?, ?, ?, ?)",
            (
                movimentacao.produto_id,
                movimentacao.tipo,
                movimentacao.quantidade,
                datetime.now().isoformat(),
                movimentacao.pedido_id,
                movimentacao.observacao,
            ),
        )
        conn.commit()
        return {"mensagem": "Movimentação cadastrada com sucesso!"}


# Rota de solicitação de compra: usuario
@app.post("/compras/solicitar/", response_model=dict)
async def solicitar_compra(
    solicitacao: SolicitarCompra, token: str = Depends(oauth2_scheme)
):
    role = get_user_role(token)
    if role != "usuario":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    usuario = token.split(":")[0]
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO solicitacoes_compra (produto_id, quantidade, status, usuario) VALUES (?, ?, ?, ?)",
            (solicitacao.produto_id, solicitacao.quantidade, "PENDENTE", usuario),
        )
        conn.commit()
    return {"mensagem": "Solicitação de compra registrada com sucesso!"}


# Rota de autorização de compra: gerente
@app.post("/compras/autorizar/", response_model=dict)
async def autorizar_compra(
    solicitacao: AutorizarCompra, token: str = Depends(oauth2_scheme)
):
    role = get_user_role(token)
    if role != "gerente":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE solicitacoes_compra SET status = 'AUTORIZADA' WHERE produto_id = ? AND quantidade = ?",
            (solicitacao.produto_id, solicitacao.quantidade),
        )
        conn.commit()
    return {"mensagem": "Compra autorizada com sucesso!"}


# Rota de listar solicitações: gerente
@app.get("/compras/solicitacoes/", response_model=List[dict])
async def listar_solicitacoes(token: str = Depends(oauth2_scheme)):
    role = get_user_role(token)
    if role != "gerente":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    with get_db_connection() as conn:
        solicitacoes = conn.execute("SELECT * FROM solicitacoes_compra").fetchall()
    return [dict(solicitacao) for solicitacao in solicitacoes]


# Rota para listar as solicitações do usuario: usuario
@app.get("/compras/solicitacoes/meus/", response_model=List[dict])
async def listar_minhas_solicitacoes(token: str = Depends(oauth2_scheme)):
    role = get_user_role(token)
    if role != "usuario":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    usuario = token.split(":")[0]  # Obtém o nome do usuário do token
    with get_db_connection() as conn:
        solicitacoes = conn.execute(
            "SELECT produto_id, quantidade, status FROM solicitacoes_compra WHERE usuario = ?",
            (usuario,),
        ).fetchall()
    return [dict(solicitacao) for solicitacao in solicitacoes]


# Rota para ver as movimentações
@app.get("/movimentacoes/", response_model=List[dict])
async def read_movimentacoes(token: str = Depends(oauth2_scheme)):
    with get_db_connection() as conn:
        movimentacoes = conn.execute("SELECT * FROM movimentacoes").fetchall()
        return [dict(movimentacao) for movimentacao in movimentacoes]


# Rota para ver as solicitações de compra do usuario: usuario
@app.get("/movimentacoes/", response_model=List[dict])
async def my_movimentacoes(token: str = Depends(oauth2_scheme)):
    usuario = token.split(":")[0]  # Obtém o nome do usuário do token

    with get_db_connection() as conn:
        movimentacoes = conn.execute(
            "SELECT * FROM movimentacoes WHERE pedido_id IN (SELECT id FROM solicitacoes_compra WHERE usuario = ?)",
            (usuario,),
        ).fetchall()
        return [dict(movimentacao) for movimentacao in movimentacoes]


# Rota para o usuario ver seu relatório semanal
@app.get("/relatorios/semanal/", response_model=List[dict])
async def relatorio_semanal(token: str = Depends(oauth2_scheme)):
    role = get_user_role(token)
    if role != "usuario":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    # Obtém a data da semana atual
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())  # Início da semana
    end_of_week = start_of_week + timedelta(days=7)  # Fim da semana

    with get_db_connection() as conn:
        # Seleciona as movimentações da semana atual
        movimentacoes = conn.execute(
            """
            SELECT produto_id, SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE 0 END) AS total_entrada,
                   SUM(CASE WHEN tipo = 'saida' THEN quantidade ELSE 0 END) AS total_saida
            FROM movimentacoes
            WHERE data BETWEEN ? AND ?
            GROUP BY produto_id
            """,
            (start_of_week.isoformat(), end_of_week.isoformat()),
        ).fetchall()

        # Para cada produto, obtém a quantidade atual e calcula a posição
        relatorio = []
        for mov in movimentacoes:
            produto = conn.execute(
                "SELECT nome, quantidade FROM produtos WHERE id = ?",
                (mov["produto_id"],),
            ).fetchone()
            if produto:
                relatorio.append(
                    {
                        "produto_id": mov["produto_id"],
                        "nome": produto["nome"],
                        "quantidade_atual": produto["quantidade"],
                        "total_entrada": mov["total_entrada"],
                        "total_saida": mov["total_saida"],
                        "quantidade_final": produto["quantidade"]
                        + mov["total_entrada"]
                        - mov["total_saida"],
                    }
                )
    return relatorio


# Rota para o estoquista registrar as entradas
@app.post("/produtos/entrada/", response_model=dict)
async def registrar_entrada(
    produto_id: int, quantidade: int, token: str = Depends(oauth2_scheme)
):
    role = get_user_role(token)
    if role != "estoquista":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?",
            (quantidade, produto_id),
        )
        conn.commit()
    return {"mensagem": "Entrada de produto registrada com sucesso!"}


@app.post("/produtos/saida/", response_model=dict)
async def registrar_saida(
    produto_id: int, quantidade: int, token: str = Depends(oauth2_scheme)
):
    role = get_user_role(token)
    if role != "estoquista":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE produtos SET quantidade = quantidade - ? WHERE id = ? AND quantidade >= ?",
            (quantidade, produto_id, quantidade),
        )
        conn.commit()
    return {"mensagem": "Saída de produto registrada com sucesso!"}
