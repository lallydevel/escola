#
# Importacoes usadas no servidor.
# Cada modulo tem uma funcao especifica dentro do projeto.
#

# json: converte dados Python para JSON e JSON para Python.
import json

# sqlite3: permite usar o banco SQLite sem instalar nada extra.
import sqlite3

# date: ajuda a validar datas no formato AAAA-MM-DD.
from datetime import date

# BaseHTTPRequestHandler: classe base para criar as rotas do servidor.
# ThreadingHTTPServer: servidor HTTP simples que aceita varias requisicoes.
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Path: facilita trabalhar com caminhos de pastas e arquivos.
from pathlib import Path

# parse_qs: le parametros da URL, como ?data=2026-04-10
# urlparse: separa o caminho da rota e os parametros.
from urllib.parse import parse_qs, urlparse


#
# Constantes do projeto.
# Aqui ficam valores fixos usados em varias partes do codigo.
#

# BASE_DIR aponta para a pasta principal do projeto.
BASE_DIR = Path(__file__).resolve().parent

# STATIC_DIR aponta para a pasta onde ficam HTML, CSS e JavaScript.
STATIC_DIR = BASE_DIR / "static"

# DB_PATH define o caminho do banco SQLite.
DB_PATH = BASE_DIR / "db.sqlite3"

# HOST e PORT definem onde o servidor vai rodar localmente.
HOST = "127.0.0.1"
PORT = 8000

# STATUS_VALIDOS guarda os tres tipos permitidos para a chamada.
STATUS_VALIDOS = {"presente", "faltou", "atrasado"}


def conectar_banco():
    """
    Esta funcao abre a conexao com o banco SQLite.

    O SQLite usa um arquivo local, entao nao precisamos instalar um banco
    separado. Isso deixa o trabalho mais simples para apresentar.
    """

    # Abre ou cria o arquivo do banco.
    conexao = sqlite3.connect(DB_PATH)

    # Faz cada linha do resultado funcionar como um dicionario.
    # Assim fica mais facil acessar por nome, por exemplo: linha["nome"].
    conexao.row_factory = sqlite3.Row

    # Ativa o controle de chave estrangeira no SQLite.
    # Isso garante que uma chamada sempre aponte para um aluno existente.
    conexao.execute("PRAGMA foreign_keys = ON")

    # Devolve a conexao pronta para uso.
    return conexao


def iniciar_banco():
    """
    Esta funcao cria as tabelas do banco na primeira execucao.

    Se elas ja existirem, nada e apagado.
    """

    # Abre a conexao com o banco.
    with conectar_banco() as conexao:
        # executescript permite executar varios comandos SQL de uma vez.
        conexao.executescript(
            """
            -- Tabela de alunos.
            -- Guarda os dados basicos de cada estudante.
            CREATE TABLE IF NOT EXISTS alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                turma TEXT NOT NULL,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Tabela de chamadas.
            -- Guarda a presenca do aluno em uma data especifica.
            CREATE TABLE IF NOT EXISTS chamadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('presente', 'faltou', 'atrasado')),
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(aluno_id, data),
                FOREIGN KEY(aluno_id) REFERENCES alunos(id) ON DELETE CASCADE
            );
            """
        )


def validar_data(data_texto):
    """
    Valida se a data recebida esta no formato correto.

    Exemplo valido:
    2026-04-10
    """

    # Se a data for invalida, o Python vai gerar erro automaticamente.
    # Se for valida, ela volta formatada em padrao ISO.
    return date.fromisoformat(data_texto).isoformat()


def listar_alunos():
    """
    Busca todos os alunos cadastrados no banco.

    O retorno sai como lista de dicionarios para facilitar o envio em JSON.
    """

    # Abre a conexao com o banco.
    with conectar_banco() as conexao:
        # Busca id, nome e turma de todos os alunos.
        alunos = conexao.execute(
            """
            SELECT id, nome, turma
            FROM alunos
            ORDER BY turma, nome
            """
        ).fetchall()

    # Converte cada linha do banco em dicionario comum do Python.
    return [dict(aluno) for aluno in alunos]


def criar_aluno(nome, turma):
    """
    Insere um novo aluno no banco.

    Depois da insercao, a funcao busca o aluno recem-criado e devolve
    os dados prontos para a API responder.
    """

    # Abre a conexao com o banco.
    with conectar_banco() as conexao:
        # INSERT grava o novo aluno.
        # Os pontos de interrogacao evitam erro e ajudam na seguranca.
        cursor = conexao.execute(
            """
            INSERT INTO alunos (nome, turma)
            VALUES (?, ?)
            """,
            (nome, turma),
        )

        # lastrowid pega o id gerado automaticamente pelo banco.
        aluno_id = cursor.lastrowid

        # Busca o aluno completo logo depois de salvar.
        aluno = conexao.execute(
            """
            SELECT id, nome, turma
            FROM alunos
            WHERE id = ?
            """,
            (aluno_id,),
        ).fetchone()

    # Devolve o aluno em formato de dicionario.
    return dict(aluno)


def buscar_chamada(data):
    """
    Busca no banco os registros de chamada de uma data especifica.

    O retorno vira um dicionario no formato:
    {id_do_aluno: "status"}
    """

    # Abre a conexao com o banco.
    with conectar_banco() as conexao:
        # Busca apenas os registros daquele dia.
        registros = conexao.execute(
            """
            SELECT aluno_id, status
            FROM chamadas
            WHERE data = ?
            """,
            (data,),
        ).fetchall()

    # Monta um dicionario para o front-end consultar rapido.
    return {registro["aluno_id"]: registro["status"] for registro in registros}


def salvar_chamada(data, registros):
    """
    Salva ou atualiza a chamada do dia.

    Se o aluno ainda nao tiver chamada naquela data, o sistema cria.
    Se ja tiver, o sistema apenas atualiza o status.
    """

    # Abre a conexao com o banco.
    with conectar_banco() as conexao:
        # executemany repete o mesmo INSERT para varios registros.
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
    """
    Conta quantos alunos estao presentes, faltaram ou chegaram atrasados.

    Esse resumo aparece na tela em forma de tres blocos coloridos.
    """

    # Comeca com tudo zerado.
    resumo = {"presente": 0, "faltou": 0, "atrasado": 0}

    # Passa por cada aluno para descobrir o status atual dele.
    for aluno in alunos:
        # Se o aluno ainda nao tiver registro salvo, ele aparece como presente.
        status = chamada_atual.get(aluno["id"], "presente")

        # Soma 1 no contador correspondente.
        resumo[status] += 1

    # Devolve o resumo final.
    return resumo


class ListaChamadaHandler(BaseHTTPRequestHandler):
    """
    Esta classe controla as rotas do servidor.

    Ela decide o que fazer quando o navegador envia GET ou POST.
    """

    def do_GET(self):
        """
        Trata requisicoes do tipo GET.

        GET normalmente serve para buscar dados ou abrir paginas.
        """

        # Separa a rota da URL.
        rota = urlparse(self.path)

        # Quando o usuario abre a raiz do site, devolvemos o HTML principal.
        if rota.path == "/":
            return self.servir_arquivo("index.html", "text/html; charset=utf-8")

        # Entrega o arquivo CSS.
        if rota.path == "/style.css":
            return self.servir_arquivo("style.css", "text/css; charset=utf-8")

        # Entrega o arquivo JavaScript.
        if rota.path == "/app.js":
            return self.servir_arquivo("app.js", "application/javascript; charset=utf-8")

        # Rota da API para listar alunos.
        if rota.path == "/api/alunos":
            return self.api_listar_alunos()

        # Rota da API para consultar a chamada de uma data.
        if rota.path == "/api/chamada":
            return self.api_buscar_chamada(rota.query)

        # Navegadores costumam pedir favicon automaticamente.
        # Aqui devolvemos 204, que significa "sem conteudo".
        if rota.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        # Se nenhuma rota conhecida bater, devolvemos erro 404.
        self.enviar_json({"erro": "Rota nao encontrada."}, status=404)

    def do_POST(self):
        """
        Trata requisicoes do tipo POST.

        POST normalmente serve para enviar dados para o servidor.
        """

        # Separa a rota da URL.
        rota = urlparse(self.path)

        # Rota para cadastrar um novo aluno.
        if rota.path == "/api/alunos":
            return self.api_criar_aluno()

        # Rota para salvar a chamada do dia.
        if rota.path == "/api/chamada":
            return self.api_salvar_chamada()

        # Se a rota nao existir, devolvemos erro 404.
        self.enviar_json({"erro": "Rota nao encontrada."}, status=404)

    def log_message(self, format, *args):
        """
        Sobrescreve o log padrao do servidor.

        Isso deixa o terminal mais limpo na hora da apresentacao.
        """

        return

    def servir_arquivo(self, nome_arquivo, content_type):
        """
        Envia um arquivo estatico para o navegador.

        Exemplo:
        - index.html
        - style.css
        - app.js
        """

        # Monta o caminho completo do arquivo dentro da pasta static.
        caminho = STATIC_DIR / nome_arquivo

        # Se o arquivo nao existir, devolvemos erro 404 em JSON.
        if not caminho.exists():
            self.enviar_json({"erro": "Arquivo nao encontrado."}, status=404)
            return

        # Le todo o arquivo em bytes.
        conteudo = caminho.read_bytes()

        # Codigo 200 significa sucesso.
        self.send_response(200)

        # Informa ao navegador qual o tipo do arquivo.
        self.send_header("Content-Type", content_type)

        # Informa o tamanho do conteudo.
        self.send_header("Content-Length", str(len(conteudo)))

        # Finaliza os cabecalhos.
        self.end_headers()

        # Envia o arquivo para o navegador.
        self.wfile.write(conteudo)

    def ler_json(self):
        """
        Le o corpo da requisicao e converte de JSON para Python.
        """

        # Descobre quantos bytes vieram na requisicao.
        tamanho = int(self.headers.get("Content-Length", 0))

        # Se vier vazio, devolvemos erro.
        if tamanho == 0:
            raise ValueError("O corpo da requisicao esta vazio.")

        # Le os bytes do corpo e converte para texto UTF-8.
        corpo = self.rfile.read(tamanho).decode("utf-8")

        # Converte o texto JSON para objeto Python.
        return json.loads(corpo)

    def enviar_json(self, dados, status=200):
        """
        Envia uma resposta JSON para o navegador ou para o front-end.
        """

        # Converte o dicionario Python para JSON em bytes.
        resposta = json.dumps(dados, ensure_ascii=False).encode("utf-8")

        # Define o codigo HTTP da resposta.
        self.send_response(status)

        # Informa que o retorno e JSON.
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # Informa o tamanho da resposta.
        self.send_header("Content-Length", str(len(resposta)))

        # Finaliza os cabecalhos.
        self.end_headers()

        # Envia os dados.
        self.wfile.write(resposta)

    def api_listar_alunos(self):
        """
        Rota GET /api/alunos

        Retorna:
        - lista de alunos
        - lista de turmas existentes
        """

        # Busca todos os alunos salvos.
        alunos = listar_alunos()

        # Usa um conjunto para pegar turmas sem repetir e depois ordena.
        turmas = sorted({aluno["turma"] for aluno in alunos})

        # Devolve tudo em JSON.
        self.enviar_json({"alunos": alunos, "turmas": turmas})

    def api_criar_aluno(self):
        """
        Rota POST /api/alunos

        Recebe nome e turma para cadastrar um aluno novo.
        """

        # Tenta ler o JSON enviado pelo navegador.
        try:
            dados = self.ler_json()
        except (ValueError, json.JSONDecodeError) as erro:
            # Se o JSON vier errado, devolve erro 400.
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        # Pega o nome e remove espacos extras.
        nome = str(dados.get("nome", "")).strip()

        # Pega a turma e remove espacos extras.
        turma = str(dados.get("turma", "")).strip()

        # Valida se os dois campos foram preenchidos.
        if not nome or not turma:
            self.enviar_json(
                {"erro": "Informe o nome do aluno e a turma."},
                status=400,
            )
            return

        # Grava o aluno no banco.
        aluno = criar_aluno(nome, turma)

        # Retorna 201, que significa recurso criado com sucesso.
        self.enviar_json({"mensagem": "Aluno cadastrado com sucesso.", "aluno": aluno}, status=201)

    def api_buscar_chamada(self, query_string):
        """
        Rota GET /api/chamada?data=AAAA-MM-DD

        Busca a chamada salva para uma data especifica.
        """

        # Converte os parametros da URL em dicionario.
        parametros = parse_qs(query_string)

        # Pega o valor da chave "data".
        data = parametros.get("data", [""])[0]

        # Se a data nao vier, devolve erro.
        if not data:
            self.enviar_json({"erro": "Informe a data da chamada."}, status=400)
            return

        # Valida o formato da data.
        try:
            data = validar_data(data)
        except ValueError:
            self.enviar_json({"erro": "Data invalida. Use o formato AAAA-MM-DD."}, status=400)
            return

        # Busca todos os alunos.
        alunos = listar_alunos()

        # Busca a chamada daquele dia.
        chamada_atual = buscar_chamada(data)

        # Gera o resumo para mostrar no painel do front-end.
        resumo = gerar_resumo(alunos, chamada_atual)

        # Converte o dicionario interno em lista para enviar por JSON.
        registros = [
            {"aluno_id": aluno_id, "status": status}
            for aluno_id, status in chamada_atual.items()
        ]

        # Devolve data, registros e resumo.
        self.enviar_json({"data": data, "registros": registros, "resumo": resumo})

    def api_salvar_chamada(self):
        """
        Rota POST /api/chamada

        Recebe a data e a lista de status dos alunos.
        """

        # Tenta ler o JSON do front-end.
        try:
            dados = self.ler_json()
        except (ValueError, json.JSONDecodeError) as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        # Pega a data enviada.
        data = str(dados.get("data", "")).strip()

        # Pega a lista de registros enviada pelo front-end.
        registros = dados.get("registros", [])

        # Valida se a data existe.
        if not data:
            self.enviar_json({"erro": "Informe a data da chamada."}, status=400)
            return

        # Valida se a data esta no formato correto.
        try:
            data = validar_data(data)
        except ValueError:
            self.enviar_json({"erro": "Data invalida. Use o formato AAAA-MM-DD."}, status=400)
            return

        # Valida se existe pelo menos um registro para salvar.
        if not isinstance(registros, list) or not registros:
            self.enviar_json({"erro": "Envie pelo menos um registro de chamada."}, status=400)
            return

        # Aqui vamos montar uma lista ja validada.
        registros_limpos = []

        # Percorre cada item recebido.
        for registro in registros:
            try:
                # Converte o id do aluno para inteiro.
                aluno_id = int(registro.get("aluno_id"))
            except (TypeError, ValueError):
                self.enviar_json({"erro": "Aluno invalido enviado para a API."}, status=400)
                return

            # Padroniza o texto do status.
            status = str(registro.get("status", "")).strip().lower()

            # Confere se o status esta entre os permitidos.
            if status not in STATUS_VALIDOS:
                self.enviar_json({"erro": "Status invalido. Use presente, faltou ou atrasado."}, status=400)
                return

            # Guarda o registro validado.
            registros_limpos.append({"aluno_id": aluno_id, "status": status})

        # Tenta salvar no banco.
        try:
            salvar_chamada(data, registros_limpos)
        except sqlite3.IntegrityError:
            # Este erro acontece se algum aluno nao existir mais no banco.
            self.enviar_json({"erro": "Um ou mais alunos enviados nao existem mais no banco."}, status=400)
            return

        # Busca os dados atualizados para devolver o resumo novo.
        alunos = listar_alunos()
        chamada_atual = buscar_chamada(data)
        resumo = gerar_resumo(alunos, chamada_atual)

        # Devolve mensagem de sucesso e resumo atualizado.
        self.enviar_json({"mensagem": "Chamada salva com sucesso.", "resumo": resumo})


def executar():
    """
    Funcao principal do sistema.

    Ela:
    1. cria as tabelas
    2. inicia o servidor
    3. mantem a aplicacao rodando
    """

    # Garante que o banco e as tabelas existam.
    iniciar_banco()

    # Cria o servidor HTTP local.
    servidor = ThreadingHTTPServer((HOST, PORT), ListaChamadaHandler)

    # Mostra no terminal onde abrir o projeto.
    print(f"Servidor rodando em http://{HOST}:{PORT}")

    # Mantem o servidor funcionando ate o usuario parar manualmente.
    servidor.serve_forever()


# Esta condicao garante que a funcao executar() so rode
# quando o arquivo for iniciado diretamente.
if __name__ == "__main__":
    executar()
