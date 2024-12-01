# database.py
import sqlite3


# Database connection
def get_db_connection():
    conn = sqlite3.connect("estoque.db", timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


# Create a new table in database
def create_tables():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                categoria TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                preco REAL NOT NULL,
                localizacao TEXT NOT NULL,
                nota_fiscal TEXT NOT NULL,
                quantidade_minima INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                tipo TEXT CHECK(tipo IN ('entrada', 'saida')) NOT NULL,
                quantidade INTEGER NOT NULL,
                data DATETIME NOT NULL,
                pedido_id INTEGER,
                observacao TEXT,
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS solicitacoes_compra (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                status TEXT DEFAULT 'pendente',
                usuario TEXT NOT NULL,
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
            """
        )


create_tables()
