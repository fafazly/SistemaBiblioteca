"""
Projeto 4.1: Aplicação CRUD - Sistema de Biblioteca (versão SQLite)

Os dados agora ficam salvos no arquivo "biblioteca.db", criado automaticamente
na mesma pasta do script. Ao fechar e abrir o programa, tudo continua lá.

Para executar:  python biblioteca_sqlite.py
"""

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).with_name("biblioteca.db")

DISPONIVEL = "Disponível"
EMPRESTADO = "Emprestado"


# ----------------------------------------------------------------------
# ENTIDADES
# ----------------------------------------------------------------------
@dataclass
class Livro:
    id: int
    titulo: str
    autor: str
    editora: str
    ano: int
    status: str = DISPONIVEL


@dataclass
class Usuario:
    id: int
    nome: str
    matricula: str
    email: str
    telefone: str


# ----------------------------------------------------------------------
# BANCO DE DADOS (SQLite)
# ----------------------------------------------------------------------
class Biblioteca:
    def __init__(self, caminho=DB_PATH):
        self.conn = sqlite3.connect(caminho)
        self.conn.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
        self._criar_tabelas()

    def _criar_tabelas(self):
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS livros (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo  TEXT    NOT NULL,
                    autor   TEXT    NOT NULL,
                    editora TEXT    NOT NULL,
                    ano     INTEGER NOT NULL,
                    status  TEXT    NOT NULL DEFAULT 'Disponível'
                );

                CREATE TABLE IF NOT EXISTS usuarios (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome      TEXT NOT NULL,
                    matricula TEXT NOT NULL UNIQUE,
                    email     TEXT NOT NULL,
                    telefone  TEXT NOT NULL
                );
                """
            )

    def fechar(self):
        self.conn.close()

    # ---- Livros ----
    def adicionar_livro(self, titulo, autor, editora, ano):
        with self.conn:  # faz commit automático (ou rollback se der erro)
            cur = self.conn.execute(
                "INSERT INTO livros (titulo, autor, editora, ano) VALUES (?, ?, ?, ?)",
                (titulo, autor, editora, ano),
            )
        return self.buscar_livro(cur.lastrowid)

    def listar_livros(self):
        linhas = self.conn.execute("SELECT * FROM livros ORDER BY id").fetchall()
        return [Livro(**dict(linha)) for linha in linhas]

    def buscar_livro(self, id_livro):
        linha = self.conn.execute(
            "SELECT * FROM livros WHERE id = ?", (id_livro,)
        ).fetchone()
        return Livro(**dict(linha)) if linha else None

    def atualizar_livro(self, livro):
        with self.conn:
            self.conn.execute(
                """UPDATE livros
                   SET titulo = ?, autor = ?, editora = ?, ano = ?, status = ?
                   WHERE id = ?""",
                (livro.titulo, livro.autor, livro.editora, livro.ano,
                 livro.status, livro.id),
            )

    def remover_livro(self, id_livro):
        with self.conn:
            cur = self.conn.execute("DELETE FROM livros WHERE id = ?", (id_livro,))
        return cur.rowcount > 0

    # ---- Usuários ----
    def adicionar_usuario(self, nome, matricula, email, telefone):
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO usuarios (nome, matricula, email, telefone) "
                "VALUES (?, ?, ?, ?)",
                (nome, matricula, email, telefone),
            )
        return self.buscar_usuario(cur.lastrowid)

    def listar_usuarios(self):
        linhas = self.conn.execute("SELECT * FROM usuarios ORDER BY id").fetchall()
        return [Usuario(**dict(linha)) for linha in linhas]

    def buscar_usuario(self, id_usuario):
        linha = self.conn.execute(
            "SELECT * FROM usuarios WHERE id = ?", (id_usuario,)
        ).fetchone()
        return Usuario(**dict(linha)) if linha else None

    def atualizar_usuario(self, usuario):
        with self.conn:
            self.conn.execute(
                """UPDATE usuarios
                   SET nome = ?, matricula = ?, email = ?, telefone = ?
                   WHERE id = ?""",
                (usuario.nome, usuario.matricula, usuario.email,
                 usuario.telefone, usuario.id),
            )

    def remover_usuario(self, id_usuario):
        with self.conn:
            cur = self.conn.execute(
                "DELETE FROM usuarios WHERE id = ?", (id_usuario,)
            )
        return cur.rowcount > 0

    def matricula_existe(self, matricula, ignorar_id=None):
        linha = self.conn.execute(
            "SELECT 1 FROM usuarios WHERE matricula = ? AND id != ?",
            (matricula, ignorar_id or 0),
        ).fetchone()
        return linha is not None


# ----------------------------------------------------------------------
# FUNÇÕES AUXILIARES DE ENTRADA
# (se "atual" for informado, apertar Enter mantém o valor antigo)
# ----------------------------------------------------------------------
def ler_texto(msg, atual=None):
    while True:
        dica = f" [{atual}]" if atual is not None else ""
        valor = input(f"{msg}{dica}: ").strip()
        if valor:
            return valor
        if atual is not None:
            return atual
        print("  ! Campo obrigatório.")


def ler_ano(atual=None):
    ano_max = date.today().year
    while True:
        dica = f" [{atual}]" if atual is not None else ""
        valor = input(f"Ano de publicação{dica}: ").strip()
        if not valor and atual is not None:
            return atual
        if valor.isdigit() and 1000 <= int(valor) <= ano_max:
            return int(valor)
        print(f"  ! Digite um ano válido (1000 a {ano_max}).")


def ler_email(atual=None):
    while True:
        dica = f" [{atual}]" if atual is not None else ""
        valor = input(f"E-mail{dica}: ").strip()
        if not valor and atual is not None:
            return atual
        if "@" in valor and "." in valor.split("@")[-1]:
            return valor
        print("  ! E-mail inválido (exemplo: nome@email.com).")


def ler_matricula(biblioteca, atual=None, id_usuario=None):
    while True:
        matricula = ler_texto("Matrícula", atual)
        if biblioteca.matricula_existe(matricula, ignorar_id=id_usuario):
            print("  ! Já existe um usuário com essa matrícula.")
        else:
            return matricula


def ler_status(atual):
    print(f"  Status atual: {atual}")
    op = input("  Novo status - 1) Disponível  2) Emprestado (Enter mantém): ").strip()
    if op == "1":
        return DISPONIVEL
    if op == "2":
        return EMPRESTADO
    return atual


def ler_id(msg):
    valor = input(msg).strip()
    if valor.isdigit():
        return int(valor)
    print("  ! ID inválido.")
    return None


def confirmar(msg):
    return input(f"{msg} (s/n): ").strip().lower() == "s"


def titulo(texto):
    print(f"\n--- {texto} ---")


def cortar(texto, tamanho):
    texto = str(texto)
    return texto if len(texto) <= tamanho else texto[: tamanho - 1] + "…"


# ----------------------------------------------------------------------
# OPERAÇÕES COM LIVROS (CRUD)
# ----------------------------------------------------------------------
def cadastrar_livro(biblioteca):
    titulo("CADASTRAR LIVRO")
    livro = biblioteca.adicionar_livro(
        titulo=ler_texto("Título"),
        autor=ler_texto("Autor"),
        editora=ler_texto("Editora"),
        ano=ler_ano(),
    )
    print(f"\n✔ Livro cadastrado com sucesso! (ID {livro.id})")


def listar_livros(biblioteca):
    titulo("LIVROS CADASTRADOS")
    livros = biblioteca.listar_livros()
    if not livros:
        print("Nenhum livro cadastrado.")
        return
    print(f"{'ID':<4} {'Título':<28} {'Autor':<20} {'Editora':<16} {'Ano':<5} Status")
    print("-" * 85)
    for l in livros:
        print(
            f"{l.id:<4} {cortar(l.titulo, 28):<28} {cortar(l.autor, 20):<20} "
            f"{cortar(l.editora, 16):<16} {l.ano:<5} {l.status}"
        )
    print(f"\nTotal: {len(livros)} livro(s)")


def atualizar_livro(biblioteca):
    titulo("ATUALIZAR LIVRO")
    id_livro = ler_id("ID do livro: ")
    if id_livro is None:
        return
    livro = biblioteca.buscar_livro(id_livro)
    if livro is None:
        print("  ! Livro não encontrado.")
        return
    print("Deixe em branco e aperte Enter para manter o valor atual.")
    livro.titulo = ler_texto("Título", livro.titulo)
    livro.autor = ler_texto("Autor", livro.autor)
    livro.editora = ler_texto("Editora", livro.editora)
    livro.ano = ler_ano(livro.ano)
    livro.status = ler_status(livro.status)
    biblioteca.atualizar_livro(livro)  # grava no banco
    print("\n✔ Livro atualizado com sucesso!")


def excluir_livro(biblioteca):
    titulo("EXCLUIR LIVRO")
    id_livro = ler_id("ID do livro: ")
    if id_livro is None:
        return
    livro = biblioteca.buscar_livro(id_livro)
    if livro is None:
        print("  ! Livro não encontrado.")
        return
    if livro.status == EMPRESTADO:
        print("  ! Atenção: este livro está emprestado.")
    if confirmar(f"Excluir '{livro.titulo}'?"):
        biblioteca.remover_livro(id_livro)
        print("\n✔ Livro excluído com sucesso!")
    else:
        print("Operação cancelada.")


# ----------------------------------------------------------------------
# OPERAÇÕES COM USUÁRIOS (CRUD)
# ----------------------------------------------------------------------
def cadastrar_usuario(biblioteca):
    titulo("CADASTRAR USUÁRIO")
    usuario = biblioteca.adicionar_usuario(
        nome=ler_texto("Nome"),
        matricula=ler_matricula(biblioteca),
        email=ler_email(),
        telefone=ler_texto("Telefone"),
    )
    print(f"\n✔ Usuário cadastrado com sucesso! (ID {usuario.id})")


def listar_usuarios(biblioteca):
    titulo("USUÁRIOS CADASTRADOS")
    usuarios = biblioteca.listar_usuarios()
    if not usuarios:
        print("Nenhum usuário cadastrado.")
        return
    print(f"{'ID':<4} {'Nome':<24} {'Matrícula':<12} {'E-mail':<28} Telefone")
    print("-" * 85)
    for u in usuarios:
        print(
            f"{u.id:<4} {cortar(u.nome, 24):<24} {cortar(u.matricula, 12):<12} "
            f"{cortar(u.email, 28):<28} {u.telefone}"
        )
    print(f"\nTotal: {len(usuarios)} usuário(s)")


def atualizar_usuario(biblioteca):
    titulo("ATUALIZAR USUÁRIO")
    id_usuario = ler_id("ID do usuário: ")
    if id_usuario is None:
        return
    usuario = biblioteca.buscar_usuario(id_usuario)
    if usuario is None:
        print("  ! Usuário não encontrado.")
        return
    print("Deixe em branco e aperte Enter para manter o valor atual.")
    usuario.nome = ler_texto("Nome", usuario.nome)
    usuario.matricula = ler_matricula(biblioteca, usuario.matricula, usuario.id)
    usuario.email = ler_email(usuario.email)
    usuario.telefone = ler_texto("Telefone", usuario.telefone)
    biblioteca.atualizar_usuario(usuario)  # grava no banco
    print("\n✔ Usuário atualizado com sucesso!")


def excluir_usuario(biblioteca):
    titulo("EXCLUIR USUÁRIO")
    id_usuario = ler_id("ID do usuário: ")
    if id_usuario is None:
        return
    usuario = biblioteca.buscar_usuario(id_usuario)
    if usuario is None:
        print("  ! Usuário não encontrado.")
        return
    if confirmar(f"Excluir '{usuario.nome}'?"):
        biblioteca.remover_usuario(id_usuario)
        print("\n✔ Usuário excluído com sucesso!")
    else:
        print("Operação cancelada.")


# ----------------------------------------------------------------------
# MENU PRINCIPAL
# ----------------------------------------------------------------------
MENU = """
===== SISTEMA DE BIBLIOTECA =====

1 - Cadastrar livro
2 - Listar livros
3 - Atualizar livro
4 - Excluir livro

5 - Cadastrar usuário
6 - Listar usuários
7 - Atualizar usuário
8 - Excluir usuário

0 - Sair
"""


def main():
    biblioteca = Biblioteca()

    opcoes = {
        "1": cadastrar_livro,
        "2": listar_livros,
        "3": atualizar_livro,
        "4": excluir_livro,
        "5": cadastrar_usuario,
        "6": listar_usuarios,
        "7": atualizar_usuario,
        "8": excluir_usuario,
    }

    try:
        while True:
            print(MENU)
            escolha = input("Escolha uma opção: ").strip()
            if escolha == "0":
                print("\nEncerrando o sistema. Até logo!")
                break
            acao = opcoes.get(escolha)
            if acao is None:
                print("\n  ! Opção inválida, tente novamente.")
            else:
                acao(biblioteca)
    except (KeyboardInterrupt, EOFError):
        print("\n\nSistema encerrado.")
    finally:
        biblioteca.fechar()


if __name__ == "__main__":
    main()
