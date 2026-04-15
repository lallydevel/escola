import json
import sqlite3
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "escola.db"

HOST = "127.0.0.1"
PORT = 8000

STATUS_VALIDOS = {"presente", "faltou", "atrasado"}


def conectar_banco():
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def iniciar_banco():
    with conectar_banco() as conexao:
        conexao.executescript(
            """
            CREATE TABLE IF NOT EXISTS alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                turma TEXT NOT NULL,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chamadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('presente', 'faltou', 'atrasado')),
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(aluno_id, data),
                FOREIGN KEY(aluno_id) REFERENCES alunos(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                concluida INTEGER NOT NULL DEFAULT 0 CHECK(concluida IN (0, 1)),
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def validar_data(data_texto):
    return date.fromisoformat(data_texto).isoformat()


def validar_id(texto_id):
    try:
        valor = int(texto_id)
        if valor <= 0:
            raise ValueError
        return valor
    except (TypeError, ValueError) as erro:
        raise ValueError("ID invalido.") from erro


def validar_concluida(valor):
    if isinstance(valor, bool):
        return 1 if valor else 0

    if isinstance(valor, int):
        if valor in (0, 1):
            return valor
        raise ValueError("Campo concluida deve ser 0 ou 1.")

    if isinstance(valor, str):
        texto = valor.strip().lower()
        if texto in ("0", "false", "falso", "nao", "não"):
            return 0
        if texto in ("1", "true", "verdadeiro", "sim"):
            return 1

    raise ValueError("Campo concluida invalido.")


def linha_tarefa(linha):
    if not linha:
        return None

    tarefa = dict(linha)
    tarefa["concluida"] = bool(tarefa["concluida"])
    return tarefa


def listar_alunos():
    with conectar_banco() as conexao:
        alunos = conexao.execute(
            """
            SELECT id, nome, turma
            FROM alunos
            ORDER BY turma, nome
            """
        ).fetchall()
    return [dict(aluno) for aluno in alunos]


def buscar_aluno(aluno_id):
    with conectar_banco() as conexao:
        aluno = conexao.execute(
            """
            SELECT id, nome, turma
            FROM alunos
            WHERE id = ?
            """,
            (aluno_id,),
        ).fetchone()
    return dict(aluno) if aluno else None


def criar_aluno(nome, turma):
    with conectar_banco() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO alunos (nome, turma)
            VALUES (?, ?)
            """,
            (nome, turma),
        )
        aluno = conexao.execute(
            """
            SELECT id, nome, turma
            FROM alunos
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return dict(aluno)


def atualizar_aluno(aluno_id, nome, turma):
    with conectar_banco() as conexao:
        cursor = conexao.execute(
            """
            UPDATE alunos
            SET nome = ?, turma = ?
            WHERE id = ?
            """,
            (nome, turma, aluno_id),
        )

        if cursor.rowcount == 0:
            return None

        aluno = conexao.execute(
            """
            SELECT id, nome, turma
            FROM alunos
            WHERE id = ?
            """,
            (aluno_id,),
        ).fetchone()

    return dict(aluno)


def remover_aluno(aluno_id):
    with conectar_banco() as conexao:
        cursor = conexao.execute(
            """
            DELETE FROM alunos
            WHERE id = ?
            """,
            (aluno_id,),
        )
    return cursor.rowcount > 0


def buscar_chamada(data):
    with conectar_banco() as conexao:
        registros = conexao.execute(
            """
            SELECT aluno_id, status
            FROM chamadas
            WHERE data = ?
            """,
            (data,),
        ).fetchall()
    return {registro["aluno_id"]: registro["status"] for registro in registros}


def salvar_chamada(data, registros):
    with conectar_banco() as conexao:
        conexao.executemany(
            """
            INSERT INTO chamadas (aluno_id, data, status)
            VALUES (?, ?, ?)
            ON CONFLICT(aluno_id, data) DO UPDATE SET
                status = excluded.status,
                atualizado_em = CURRENT_TIMESTAMP
            """,
            [(registro["aluno_id"], data, registro["status"]) for registro in registros],
        )


def gerar_resumo(alunos, chamada_atual):
    resumo = {"presente": 0, "faltou": 0, "atrasado": 0}

    for aluno in alunos:
        status = chamada_atual.get(aluno["id"], "presente")
        resumo[status] += 1

    return resumo


def listar_tarefas():
    with conectar_banco() as conexao:
        tarefas = conexao.execute(
            """
            SELECT id, titulo, descricao, concluida, criado_em, atualizado_em
            FROM tarefas
            ORDER BY id DESC
            """
        ).fetchall()
    return [linha_tarefa(tarefa) for tarefa in tarefas]


def buscar_tarefa(tarefa_id):
    with conectar_banco() as conexao:
        tarefa = conexao.execute(
            """
            SELECT id, titulo, descricao, concluida, criado_em, atualizado_em
            FROM tarefas
            WHERE id = ?
            """,
            (tarefa_id,),
        ).fetchone()
    return linha_tarefa(tarefa)


def criar_tarefa(titulo, descricao, concluida):
    with conectar_banco() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO tarefas (titulo, descricao, concluida)
            VALUES (?, ?, ?)
            """,
            (titulo, descricao, concluida),
        )
        tarefa = conexao.execute(
            """
            SELECT id, titulo, descricao, concluida, criado_em, atualizado_em
            FROM tarefas
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return linha_tarefa(tarefa)


def atualizar_tarefa(tarefa_id, titulo, descricao, concluida):
    with conectar_banco() as conexao:
        cursor = conexao.execute(
            """
            UPDATE tarefas
            SET titulo = ?,
                descricao = ?,
                concluida = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (titulo, descricao, concluida, tarefa_id),
        )

        if cursor.rowcount == 0:
            return None

        tarefa = conexao.execute(
            """
            SELECT id, titulo, descricao, concluida, criado_em, atualizado_em
            FROM tarefas
            WHERE id = ?
            """,
            (tarefa_id,),
        ).fetchone()

    return linha_tarefa(tarefa)


def remover_tarefa(tarefa_id):
    with conectar_banco() as conexao:
        cursor = conexao.execute(
            """
            DELETE FROM tarefas
            WHERE id = ?
            """,
            (tarefa_id,),
        )
    return cursor.rowcount > 0


class ListaChamadaHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.enviar_cabecalhos_cors()
        self.end_headers()

    def do_GET(self):
        try:
            rota = urlparse(self.path)

            if rota.path == "/":
                return self.servir_arquivo("index.html", "text/html; charset=utf-8")

            if rota.path == "/style.css":
                return self.servir_arquivo("style.css", "text/css; charset=utf-8")

            if rota.path == "/app.js":
                return self.servir_arquivo("app.js", "application/javascript; charset=utf-8")

            if rota.path == "/api/alunos":
                return self.api_listar_alunos()

            if rota.path.startswith("/api/alunos/"):
                return self.api_buscar_aluno_por_id(rota.path)

            if rota.path == "/api/chamada":
                return self.api_buscar_chamada(rota.query)

            if rota.path == "/tarefas":
                return self.api_listar_tarefas()

            if rota.path.startswith("/tarefas/"):
                return self.api_buscar_tarefa_por_id(rota.path)

            if rota.path == "/favicon.ico":
                self.send_response(204)
                self.enviar_cabecalhos_cors()
                self.end_headers()
                return

            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
        except Exception:
            self.enviar_json({"erro": "Erro interno do servidor."}, status=500)

    def do_POST(self):
        try:
            rota = urlparse(self.path)

            if rota.path == "/api/alunos":
                return self.api_criar_aluno()

            if rota.path == "/api/chamada":
                return self.api_salvar_chamada()

            if rota.path == "/tarefas":
                return self.api_criar_tarefa()

            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
        except Exception:
            self.enviar_json({"erro": "Erro interno do servidor."}, status=500)

    def do_PUT(self):
        try:
            rota = urlparse(self.path)

            if rota.path.startswith("/tarefas/"):
                return self.api_atualizar_tarefa(rota.path)

            if rota.path.startswith("/api/alunos/"):
                return self.api_atualizar_aluno(rota.path)

            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
        except Exception:
            self.enviar_json({"erro": "Erro interno do servidor."}, status=500)

    def do_DELETE(self):
        try:
            rota = urlparse(self.path)

            if rota.path.startswith("/tarefas/"):
                return self.api_remover_tarefa(rota.path)

            if rota.path.startswith("/api/alunos/"):
                return self.api_remover_aluno(rota.path)

            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
        except Exception:
            self.enviar_json({"erro": "Erro interno do servidor."}, status=500)

    def log_message(self, format, *args):
        return

    def enviar_cabecalhos_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def servir_arquivo(self, nome_arquivo, content_type):
        caminho = STATIC_DIR / nome_arquivo

        if not caminho.exists():
            self.enviar_json({"erro": "Arquivo nao encontrado."}, status=404)
            return

        conteudo = caminho.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(conteudo)))
        self.enviar_cabecalhos_cors()
        self.end_headers()
        self.wfile.write(conteudo)

    def ler_json(self):
        tamanho = int(self.headers.get("Content-Length", 0))

        if tamanho == 0:
            raise ValueError("O corpo da requisicao esta vazio.")

        corpo = self.rfile.read(tamanho).decode("utf-8")

        try:
            return json.loads(corpo)
        except json.JSONDecodeError as erro:
            raise ValueError("JSON invalido.") from erro

    def enviar_json(self, dados, status=200):
        resposta = json.dumps(dados, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resposta)))
        self.enviar_cabecalhos_cors()
        self.end_headers()
        self.wfile.write(resposta)

    def id_da_rota(self, path, prefixo):
        base = prefixo.rstrip("/")
        inicio = f"{base}/"

        if not path.startswith(inicio):
            return None

        trecho_id = path[len(inicio):]
        if not trecho_id or "/" in trecho_id:
            return None

        return trecho_id

    # ----- API ALUNOS (compatibilidade com front) -----

    def api_listar_alunos(self):
        alunos = listar_alunos()
        turmas = sorted({aluno["turma"] for aluno in alunos})

        turma_filtro = parse_qs(urlparse(self.path).query).get("turma", [""])[0].strip()
        if turma_filtro:
            alunos_filtrados = [aluno for aluno in alunos if aluno["turma"] == turma_filtro]
            self.enviar_json(alunos_filtrados)
            return

        self.enviar_json({"alunos": alunos, "turmas": turmas})

    def api_buscar_aluno_por_id(self, path):
        aluno_id_texto = self.id_da_rota(path, "/api/alunos")

        if not aluno_id_texto:
            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
            return

        try:
            aluno_id = validar_id(aluno_id_texto)
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        aluno = buscar_aluno(aluno_id)

        if not aluno:
            self.enviar_json({"erro": "Aluno nao encontrado."}, status=404)
            return

        self.enviar_json({"aluno": aluno})

    def api_criar_aluno(self):
        try:
            dados = self.ler_json()
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        nome = str(dados.get("nome", "")).strip()
        turma = str(dados.get("turma", "")).strip()

        if not nome or not turma:
            self.enviar_json({"erro": "Informe o nome do aluno e a turma."}, status=400)
            return

        aluno = criar_aluno(nome, turma)
        self.enviar_json({"mensagem": "Aluno cadastrado com sucesso.", "aluno": aluno}, status=201)

    def api_atualizar_aluno(self, path):
        aluno_id_texto = self.id_da_rota(path, "/api/alunos")

        if not aluno_id_texto:
            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
            return

        try:
            aluno_id = validar_id(aluno_id_texto)
            dados = self.ler_json()
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        nome = str(dados.get("nome", "")).strip()
        turma = str(dados.get("turma", "")).strip()

        if not nome or not turma:
            self.enviar_json({"erro": "Informe o nome do aluno e a turma."}, status=400)
            return

        aluno = atualizar_aluno(aluno_id, nome, turma)

        if not aluno:
            self.enviar_json({"erro": "Aluno nao encontrado."}, status=404)
            return

        self.enviar_json({"mensagem": "Aluno atualizado com sucesso.", "aluno": aluno})

    def api_remover_aluno(self, path):
        aluno_id_texto = self.id_da_rota(path, "/api/alunos")

        if not aluno_id_texto:
            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
            return

        try:
            aluno_id = validar_id(aluno_id_texto)
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        removido = remover_aluno(aluno_id)

        if not removido:
            self.enviar_json({"erro": "Aluno nao encontrado."}, status=404)
            return

        self.enviar_json({"mensagem": "Aluno removido com sucesso."})

    # ----- API CHAMADA (compatibilidade com front) -----

    def api_buscar_chamada(self, query_string):
        parametros = parse_qs(query_string)
        data = parametros.get("data", [""])[0]

        if not data:
            self.enviar_json({"erro": "Informe a data da chamada."}, status=400)
            return

        try:
            data = validar_data(data)
        except ValueError:
            self.enviar_json({"erro": "Data invalida. Use o formato AAAA-MM-DD."}, status=400)
            return

        alunos = listar_alunos()
        chamada_atual = buscar_chamada(data)
        resumo = gerar_resumo(alunos, chamada_atual)

        registros = [
            {"aluno_id": aluno_id, "status": status}
            for aluno_id, status in chamada_atual.items()
        ]

        self.enviar_json({"data": data, "registros": registros, "resumo": resumo})

    def api_salvar_chamada(self):
        try:
            dados = self.ler_json()
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        data = str(dados.get("data", "")).strip()
        registros = dados.get("registros", [])

        if not data:
            self.enviar_json({"erro": "Informe a data da chamada."}, status=400)
            return

        try:
            data = validar_data(data)
        except ValueError:
            self.enviar_json({"erro": "Data invalida. Use o formato AAAA-MM-DD."}, status=400)
            return

        if not isinstance(registros, list) or not registros:
            self.enviar_json({"erro": "Envie pelo menos um registro de chamada."}, status=400)
            return

        registros_limpos = []

        for registro in registros:
            try:
                aluno_id = validar_id(registro.get("aluno_id"))
            except ValueError:
                self.enviar_json({"erro": "Aluno invalido enviado para a API."}, status=400)
                return

            status = str(registro.get("status", "")).strip().lower()
            if status not in STATUS_VALIDOS:
                self.enviar_json({"erro": "Status invalido. Use presente, faltou ou atrasado."}, status=400)
                return

            registros_limpos.append({"aluno_id": aluno_id, "status": status})

        try:
            salvar_chamada(data, registros_limpos)
        except sqlite3.IntegrityError:
            self.enviar_json({"erro": "Um ou mais alunos enviados nao existem mais no banco."}, status=400)
            return

        alunos = listar_alunos()
        chamada_atual = buscar_chamada(data)
        resumo = gerar_resumo(alunos, chamada_atual)

        self.enviar_json({"mensagem": "Chamada salva com sucesso.", "resumo": resumo})

    # ----- API TAREFAS (CRUD obrigatorio) -----

    def api_listar_tarefas(self):
        tarefas = listar_tarefas()
        self.enviar_json({"tarefas": tarefas})

    def api_buscar_tarefa_por_id(self, path):
        tarefa_id_texto = self.id_da_rota(path, "/tarefas")

        if not tarefa_id_texto:
            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
            return

        try:
            tarefa_id = validar_id(tarefa_id_texto)
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        tarefa = buscar_tarefa(tarefa_id)

        if not tarefa:
            self.enviar_json({"erro": "Tarefa nao encontrada."}, status=404)
            return

        self.enviar_json({"tarefa": tarefa})

    def api_criar_tarefa(self):
        try:
            dados = self.ler_json()
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        titulo = str(dados.get("titulo", "")).strip()
        descricao = str(dados.get("descricao", "")).strip()

        if not titulo or not descricao:
            self.enviar_json({"erro": "Campos obrigatorios: titulo e descricao."}, status=400)
            return

        try:
            concluida = validar_concluida(dados.get("concluida", 0))
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        tarefa = criar_tarefa(titulo, descricao, concluida)
        self.enviar_json({"mensagem": "Tarefa criada com sucesso.", "tarefa": tarefa}, status=201)

    def api_atualizar_tarefa(self, path):
        tarefa_id_texto = self.id_da_rota(path, "/tarefas")

        if not tarefa_id_texto:
            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
            return

        try:
            tarefa_id = validar_id(tarefa_id_texto)
            dados = self.ler_json()
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        titulo = str(dados.get("titulo", "")).strip()
        descricao = str(dados.get("descricao", "")).strip()

        if not titulo or not descricao:
            self.enviar_json({"erro": "Campos obrigatorios: titulo e descricao."}, status=400)
            return

        try:
            concluida = validar_concluida(dados.get("concluida", 0))
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        tarefa = atualizar_tarefa(tarefa_id, titulo, descricao, concluida)

        if not tarefa:
            self.enviar_json({"erro": "Tarefa nao encontrada."}, status=404)
            return

        self.enviar_json({"mensagem": "Tarefa atualizada com sucesso.", "tarefa": tarefa})

    def api_remover_tarefa(self, path):
        tarefa_id_texto = self.id_da_rota(path, "/tarefas")

        if not tarefa_id_texto:
            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
            return

        try:
            tarefa_id = validar_id(tarefa_id_texto)
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        removida = remover_tarefa(tarefa_id)

        if not removida:
            self.enviar_json({"erro": "Tarefa nao encontrada."}, status=404)
            return

        self.enviar_json({"mensagem": "Tarefa removida com sucesso."})


def executar():
    iniciar_banco()
    servidor = ThreadingHTTPServer((HOST, PORT), ListaChamadaHandler)
    print(f"Servidor rodando em http://{HOST}:{PORT}")
    servidor.serve_forever()


if __name__ == "__main__":
    executar()
