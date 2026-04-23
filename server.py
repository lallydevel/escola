import hashlib
import json
import mimetypes
import secrets
import sqlite3
import traceback
from datetime import date
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "escola.db"

HOST = "127.0.0.1"
PORT = 8000

STATUS_VALIDOS = {"presente", "faltou", "atrasado"}
TIPOS_USUARIO = {"professor", "aluno"}
SESSION_COOKIE = "educhamada_session"
SESSOES = {}

ROTAS_HTML = {
    "/": "index.html",
    "/index.html": "index.html",
    "/index": "index.html",
    "/index/": "index.html",
    "/inicio": "index.html",
    "/inicio.html": "index.html",
    "/inicio/": "index.html",
    "/login": "login.html",
    "/login.html": "login.html",
    "/login/": "login.html",
    "/cadastro": "cadastro.html",
    "/cadastro.html": "cadastro.html",
    "/cadastro/": "cadastro.html",
    "/cadastro-aluno": "cadastro_aluno.html",
    "/cadastro-aluno/": "cadastro_aluno.html",
    "/cadastro_aluno.html": "cadastro_aluno.html",
    "/cadastro_aluno/": "cadastro_aluno.html",
    "/chamada": "chamada.html",
    "/chamada.html": "chamada.html",
    "/chamada/": "chamada.html",
    "/registro": "registro.html",
    "/registro.html": "registro.html",
    "/registro/": "registro.html",
}

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("image/avif", ".avif")

APP_JS = r"""
(() => {
    const estadoChamada = {
        alunos: [],
        chamada: new Map(),
    };

    function textoSeguro(valor) {
        return String(valor ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function dataHoje() {
        const hoje = new Date();
        const ano = String(hoje.getFullYear());
        const mes = String(hoje.getMonth() + 1).padStart(2, "0");
        const dia = String(hoje.getDate()).padStart(2, "0");
        return `${ano}-${mes}-${dia}`;
    }

    function criarCaixaMensagem(referencia) {
        if (!referencia || referencia.__caixaMensagem) {
            return referencia ? referencia.__caixaMensagem : null;
        }

        const caixa = document.createElement("div");
        caixa.style.display = "none";
        caixa.style.margin = "16px 0";
        caixa.style.padding = "12px 14px";
        caixa.style.borderRadius = "10px";
        caixa.style.fontWeight = "600";
        caixa.style.lineHeight = "1.4";
        caixa.style.border = "1px solid transparent";
        referencia.parentNode.insertBefore(caixa, referencia);
        referencia.__caixaMensagem = caixa;
        return caixa;
    }

    function mostrarMensagem(caixa, texto, tipo = "sucesso") {
        if (!caixa) {
            return;
        }

        caixa.textContent = texto;
        caixa.style.display = "block";

        if (tipo === "erro") {
            caixa.style.background = "#fde8e8";
            caixa.style.color = "#8a1c1c";
            caixa.style.borderColor = "#f5b8b8";
            return;
        }

        caixa.style.background = "#e7f7eb";
        caixa.style.color = "#1f6b37";
        caixa.style.borderColor = "#b7e2c4";
    }

    function limparMensagem(caixa) {
        if (!caixa) {
            return;
        }

        caixa.textContent = "";
        caixa.style.display = "none";
    }

    async function lerJson(resposta) {
        const texto = await resposta.text();
        let dados = {};

        if (texto) {
            try {
                dados = JSON.parse(texto);
            } catch (erro) {
                dados = {};
            }
        }

        if (!resposta.ok) {
            throw new Error(dados.erro || "Nao foi possivel concluir a operacao.");
        }

        return dados;
    }

    async function getJson(url) {
        const resposta = await fetch(url, {
            credentials: "same-origin",
        });
        return lerJson(resposta);
    }

    async function postJson(url, dados) {
        const resposta = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "same-origin",
            body: JSON.stringify(dados),
        });
        return lerJson(resposta);
    }

    function bindLogin() {
        const form = document.querySelector(".login-box .formulario");
        if (!form) {
            return;
        }

        const caixa = criarCaixaMensagem(form);
        const campos = form.querySelectorAll("input");
        const email = campos[0];
        const senha = campos[1];

        form.addEventListener("submit", async (evento) => {
            evento.preventDefault();
            limparMensagem(caixa);

            try {
                const dados = await postJson("/api/auth/login", {
                    email: email.value.trim(),
                    senha: senha.value,
                });

                mostrarMensagem(caixa, dados.mensagem || "Login realizado com sucesso.");
                form.reset();
                window.setTimeout(() => {
                    window.location.href = "/chamada.html";
                }, 300);
            } catch (erro) {
                mostrarMensagem(caixa, erro.message, "erro");
            }
        });
    }

    function bindCadastro() {
        const formProfessor = document.querySelector("#cadastro-professor .form-padrao");
        const formAluno = document.querySelector("#cadastro-aluno .form-padrao");

        if (formProfessor) {
            const caixaProfessor = criarCaixaMensagem(formProfessor);
            const camposProfessor = formProfessor.querySelectorAll("input");

            formProfessor.addEventListener("submit", async (evento) => {
                evento.preventDefault();
                limparMensagem(caixaProfessor);

                try {
                    const dados = await postJson("/api/auth/cadastro", {
                        tipo: "professor",
                        nome: camposProfessor[0].value.trim(),
                        email: camposProfessor[1].value.trim(),
                        senha: camposProfessor[2].value,
                        disciplinas_turmas: camposProfessor[3].value.trim(),
                    });

                    mostrarMensagem(caixaProfessor, dados.mensagem || "Cadastro realizado com sucesso.");
                    formProfessor.reset();
                    window.setTimeout(() => {
                        window.location.href = "/login.html";
                    }, 500);
                } catch (erro) {
                    mostrarMensagem(caixaProfessor, erro.message, "erro");
                }
            });
        }

        if (formAluno) {
            const caixaAluno = criarCaixaMensagem(formAluno);
            const camposAluno = formAluno.querySelectorAll("input");

            formAluno.addEventListener("submit", async (evento) => {
                evento.preventDefault();
                limparMensagem(caixaAluno);

                try {
                    const dados = await postJson("/api/auth/cadastro", {
                        tipo: "aluno",
                        nome: camposAluno[0].value.trim(),
                        nascimento: camposAluno[1].value,
                        cpf: camposAluno[2].value.trim(),
                        turma: camposAluno[3].value.trim(),
                        email: camposAluno[4].value.trim(),
                        senha: camposAluno[5].value,
                    });

                    mostrarMensagem(caixaAluno, dados.mensagem || "Cadastro realizado com sucesso.");
                    formAluno.reset();
                    window.setTimeout(() => {
                        window.location.href = "/login.html";
                    }, 500);
                } catch (erro) {
                    mostrarMensagem(caixaAluno, erro.message, "erro");
                }
            });
        }
    }

    function calcularIdade(dataNascimento) {
        if (!dataNascimento) {
            return Number.NaN;
        }

        const hoje = new Date();
        const nascimento = new Date(`${dataNascimento}T00:00:00`);

        if (Number.isNaN(nascimento.getTime())) {
            return Number.NaN;
        }

        let idade = hoje.getFullYear() - nascimento.getFullYear();
        const aindaNaoFezAniversario =
            hoje.getMonth() < nascimento.getMonth() ||
            (hoje.getMonth() === nascimento.getMonth() && hoje.getDate() < nascimento.getDate());

        if (aindaNaoFezAniversario) {
            idade -= 1;
        }

        return idade;
    }

    function bindCadastroAluno() {
        const form = document.getElementById("formCadastro");
        if (!form) {
            return;
        }

        const caixa = criarCaixaMensagem(form);
        const nome = document.getElementById("nome");
        const nascimento = document.getElementById("nascimento");
        const cpf = document.getElementById("cpf");
        const turma = document.getElementById("turma");
        const professor = document.getElementById("professor");
        const endereco = document.getElementById("endereco");
        const email = document.getElementById("email");
        const responsavel = document.getElementById("responsavel");
        const campoResponsavel = document.getElementById("campo-responsavel");

        function atualizarCampoResponsavel() {
            if (!campoResponsavel || !responsavel) {
                return;
            }

            const idade = calcularIdade(nascimento ? nascimento.value : "");
            const menorDeIdade = Number.isFinite(idade) && idade < 18;
            campoResponsavel.classList.toggle("hidden", !menorDeIdade);
            responsavel.required = menorDeIdade;

            if (!menorDeIdade) {
                responsavel.value = "";
            }
        }

        if (nascimento) {
            nascimento.addEventListener("change", atualizarCampoResponsavel);
            atualizarCampoResponsavel();
        }

        form.addEventListener("submit", async (evento) => {
            evento.preventDefault();
            limparMensagem(caixa);

            try {
                const dados = await postJson("/api/alunos", {
                    nome: nome ? nome.value.trim() : "",
                    nascimento: nascimento ? nascimento.value : "",
                    cpf: cpf ? cpf.value.trim() : "",
                    turma: turma ? turma.value.trim() : "",
                    professor: professor ? professor.value.trim() : "",
                    endereco: endereco ? endereco.value.trim() : "",
                    email: email ? email.value.trim() : "",
                    responsavel: responsavel ? responsavel.value.trim() : "",
                });

                mostrarMensagem(caixa, dados.mensagem || "Aluno cadastrado com sucesso.");
                form.reset();
                atualizarCampoResponsavel();
                window.setTimeout(() => {
                    window.location.href = "/chamada.html";
                }, 500);
            } catch (erro) {
                mostrarMensagem(caixa, erro.message, "erro");
            }
        });
    }

    function bindChamada() {
        const dataChamada = document.getElementById("data-chamada");
        const filtroTurma = document.getElementById("filtro-turma");
        const tabela = document.querySelector(".tabela-area tbody");
        const botaoAtualizar = document.querySelector(".botao-secundario");
        const botaoSalvar = document.querySelector(".botao-principal");
        const resumoPresente = document.getElementById("presente");
        const resumoFalta = document.getElementById("falta");
        const resumoAtraso = document.getElementById("atraso");
        const cartaoTabela = document.querySelector(".cartao-tabela");

        if (!dataChamada || !filtroTurma || !tabela || !botaoAtualizar || !botaoSalvar) {
            return;
        }

        const caixa = criarCaixaMensagem(cartaoTabela || tabela);

        function statusAtual(alunoId) {
            return estadoChamada.chamada.get(alunoId) || "presente";
        }

        function alunosFiltrados() {
            const turmaSelecionada = filtroTurma.value;

            if (!turmaSelecionada) {
                return estadoChamada.alunos;
            }

            return estadoChamada.alunos.filter((aluno) => aluno.turma === turmaSelecionada);
        }

        function preencherTurmas(turmas) {
            const turmaAtual = filtroTurma.value && filtroTurma.value !== "Todas" ? filtroTurma.value : "";
            filtroTurma.innerHTML = "";

            const opcaoPadrao = document.createElement("option");
            opcaoPadrao.value = "";
            opcaoPadrao.textContent = "Todas as turmas";
            filtroTurma.appendChild(opcaoPadrao);

            turmas.forEach((turma) => {
                const option = document.createElement("option");
                option.value = turma;
                option.textContent = turma;
                filtroTurma.appendChild(option);
            });

            filtroTurma.value = turmas.includes(turmaAtual) ? turmaAtual : "";
        }

        function renderizarResumo() {
            const resumo = { presente: 0, faltou: 0, atrasado: 0 };

            alunosFiltrados().forEach((aluno) => {
                resumo[statusAtual(aluno.id)] += 1;
            });

            if (resumoPresente) {
                resumoPresente.textContent = String(resumo.presente);
            }

            if (resumoFalta) {
                resumoFalta.textContent = String(resumo.faltou);
            }

            if (resumoAtraso) {
                resumoAtraso.textContent = String(resumo.atrasado);
            }
        }

        function opcaoStatus(alunoId, valor, rotulo, classe) {
            const checked = statusAtual(alunoId) === valor ? "checked" : "";
            return `
                <label class="radio-status ${classe}">
                    <input type="radio" name="aluno-${alunoId}" data-aluno-id="${alunoId}" value="${valor}" ${checked}>
                    <span>${rotulo}</span>
                </label>
            `;
        }

        function renderizarTabela() {
            const alunos = alunosFiltrados();

            if (alunos.length === 0) {
                tabela.innerHTML = `
                    <tr>
                        <td colspan="3"><strong>Nenhum aluno cadastrado para esta visualizacao.</strong></td>
                    </tr>
                `;
                renderizarResumo();
                return;
            }

            tabela.innerHTML = alunos
                .map((aluno) => `
                    <tr>
                        <td><strong>${textoSeguro(aluno.nome)}</strong></td>
                        <td><span class="tag-turma">${textoSeguro(aluno.turma)}</span></td>
                        <td>
                            <div class="opcoes-presenca">
                                ${opcaoStatus(aluno.id, "presente", "P", "presente")}
                                ${opcaoStatus(aluno.id, "faltou", "F", "falta")}
                                ${opcaoStatus(aluno.id, "atrasado", "A", "atraso")}
                            </div>
                        </td>
                    </tr>
                `)
                .join("");

            renderizarResumo();
        }

        async function carregarAlunos() {
            const dados = await getJson("/api/alunos");
            estadoChamada.alunos = Array.isArray(dados.alunos) ? dados.alunos : [];
            preencherTurmas(Array.isArray(dados.turmas) ? dados.turmas : []);
        }

        async function carregarChamada() {
            const dados = await getJson(`/api/chamada?data=${encodeURIComponent(dataChamada.value)}`);
            estadoChamada.chamada = new Map(
                (dados.registros || []).map((registro) => [Number(registro.aluno_id), registro.status]),
            );
        }

        async function atualizarTela() {
            limparMensagem(caixa);
            await carregarAlunos();
            await carregarChamada();
            renderizarTabela();
        }

        tabela.addEventListener("change", (evento) => {
            const campo = evento.target.closest("input[data-aluno-id]");
            if (!campo) {
                return;
            }

            estadoChamada.chamada.set(Number(campo.dataset.alunoId), campo.value);
            renderizarResumo();
        });

        botaoAtualizar.addEventListener("click", async (evento) => {
            evento.preventDefault();

            try {
                await atualizarTela();
            } catch (erro) {
                mostrarMensagem(caixa, erro.message, "erro");
            }
        });

        botaoSalvar.addEventListener("click", async (evento) => {
            evento.preventDefault();
            limparMensagem(caixa);

            try {
                const registros = estadoChamada.alunos.map((aluno) => ({
                    aluno_id: aluno.id,
                    status: statusAtual(aluno.id),
                }));

                if (registros.length === 0) {
                    throw new Error("Cadastre pelo menos um aluno antes de salvar a chamada.");
                }

                const dados = await postJson("/api/chamada", {
                    data: dataChamada.value,
                    registros,
                });

                mostrarMensagem(caixa, dados.mensagem || "Chamada salva com sucesso.");
                await carregarChamada();
                renderizarTabela();
            } catch (erro) {
                mostrarMensagem(caixa, erro.message, "erro");
            }
        });

        filtroTurma.addEventListener("change", renderizarTabela);
        dataChamada.addEventListener("change", async () => {
            try {
                await atualizarTela();
            } catch (erro) {
                mostrarMensagem(caixa, erro.message, "erro");
            }
        });

        dataChamada.value = dataChamada.value || dataHoje();

        atualizarTela().catch((erro) => {
            mostrarMensagem(caixa, erro.message || "Nao foi possivel carregar a chamada.", "erro");
        });
    }

    function iniciar() {
        bindLogin();
        bindCadastro();
        bindCadastroAluno();
        bindChamada();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }
})();
"""


def conectar_banco():
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def colunas_tabela(conexao, tabela):
    return {
        linha["name"]
        for linha in conexao.execute(f"PRAGMA table_info({tabela})").fetchall()
    }


def adicionar_coluna_se_ausente(conexao, tabela, coluna, definicao):
    if coluna not in colunas_tabela(conexao, tabela):
        conexao.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")


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

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('professor', 'aluno')),
                turma TEXT DEFAULT '',
                disciplinas_turmas TEXT DEFAULT '',
                cpf TEXT DEFAULT '',
                nascimento TEXT DEFAULT '',
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        for coluna, definicao in {
            "nascimento": "TEXT DEFAULT ''",
            "cpf": "TEXT DEFAULT ''",
            "professor": "TEXT DEFAULT ''",
            "endereco": "TEXT DEFAULT ''",
            "email": "TEXT DEFAULT ''",
            "responsavel": "TEXT DEFAULT ''",
        }.items():
            adicionar_coluna_se_ausente(conexao, "alunos", coluna, definicao)


def texto_limpo(valor):
    return str(valor or "").strip()


def validar_texto_obrigatorio(valor, campo):
    texto = texto_limpo(valor)
    if not texto:
        raise ValueError(f"Informe {campo}.")
    return texto


def validar_data(data_texto):
    return date.fromisoformat(texto_limpo(data_texto)).isoformat()


def validar_id(texto_id):
    try:
        valor = int(texto_id)
        if valor <= 0:
            raise ValueError
        return valor
    except (TypeError, ValueError) as erro:
        raise ValueError("ID invalido.") from erro


def validar_email(email):
    email_limpo = texto_limpo(email).lower()
    if not email_limpo or email_limpo.count("@") != 1:
        raise ValueError("Informe um e-mail valido.")

    usuario, dominio = email_limpo.split("@", 1)
    if not usuario or not dominio or "." not in dominio:
        raise ValueError("Informe um e-mail valido.")

    return email_limpo


def validar_senha(senha):
    senha_texto = str(senha or "")
    if len(senha_texto.strip()) < 6:
        raise ValueError("A senha deve ter pelo menos 6 caracteres.")
    return senha_texto


def validar_tipo_usuario(tipo):
    tipo_limpo = texto_limpo(tipo).lower()
    if tipo_limpo not in TIPOS_USUARIO:
        raise ValueError("Tipo de usuario invalido.")
    return tipo_limpo


def normalizar_cpf(cpf):
    digitos = "".join(caractere for caractere in str(cpf or "") if caractere.isdigit())
    if not digitos:
        return ""
    if len(digitos) != 11:
        raise ValueError("Informe um CPF valido.")
    return digitos


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


def validar_dados_aluno(dados):
    nome = validar_texto_obrigatorio(dados.get("nome"), "o nome do aluno")
    turma = validar_texto_obrigatorio(dados.get("turma"), "a turma")

    nascimento = texto_limpo(dados.get("nascimento"))
    if nascimento:
        nascimento = validar_data(nascimento)

    email = texto_limpo(dados.get("email"))
    if email:
        email = validar_email(email)

    return {
        "nome": nome,
        "turma": turma,
        "nascimento": nascimento,
        "cpf": normalizar_cpf(dados.get("cpf")),
        "professor": texto_limpo(dados.get("professor")),
        "endereco": texto_limpo(dados.get("endereco")),
        "email": email,
        "responsavel": texto_limpo(dados.get("responsavel")),
    }


def linha_tarefa(linha):
    if not linha:
        return None

    tarefa = dict(linha)
    tarefa["concluida"] = bool(tarefa["concluida"])
    return tarefa


def linha_aluno(linha):
    if not linha:
        return None

    aluno = dict(linha)
    for campo in ("nascimento", "cpf", "professor", "endereco", "email", "responsavel"):
        aluno[campo] = aluno.get(campo) or ""
    aluno["adicionado_por_admin"] = bool(aluno.get("adicionado_por_admin", False))
    return aluno


def linha_usuario_publica(linha):
    if not linha:
        return None

    usuario = dict(linha)
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
        "turma": usuario.get("turma") or "",
        "disciplinas_turmas": usuario.get("disciplinas_turmas") or "",
        "cpf": usuario.get("cpf") or "",
        "nascimento": usuario.get("nascimento") or "",
        "criado_em": usuario.get("criado_em"),
    }


def identidades_usuarios_aluno(conexao):
    linhas = conexao.execute(
        """
        SELECT LOWER(email) AS email, cpf
        FROM usuarios
        WHERE tipo = 'aluno'
        """
    ).fetchall()

    emails = {texto_limpo(linha["email"]).lower() for linha in linhas if texto_limpo(linha["email"])}
    cpfs = {texto_limpo(linha["cpf"]) for linha in linhas if texto_limpo(linha["cpf"])}
    return emails, cpfs


def marcar_aluno_adicionado_por_admin(aluno, emails_usuarios, cpfs_usuarios):
    email = texto_limpo(aluno.get("email")).lower()
    cpf = texto_limpo(aluno.get("cpf"))
    tem_vinculo_usuario = (email and email in emails_usuarios) or (cpf and cpf in cpfs_usuarios)
    aluno["adicionado_por_admin"] = not tem_vinculo_usuario
    return aluno


def listar_turmas():
    with conectar_banco() as conexao:
        turmas = {
            texto_limpo(linha["turma"])
            for linha in conexao.execute(
                """
                SELECT turma
                FROM alunos
                WHERE TRIM(COALESCE(turma, '')) <> ''
                """
            ).fetchall()
        }
        turmas.update(
            {
                texto_limpo(linha["turma"])
                for linha in conexao.execute(
                    """
                    SELECT turma
                    FROM usuarios
                    WHERE tipo = 'aluno'
                      AND TRIM(COALESCE(turma, '')) <> ''
                    """
                ).fetchall()
            }
        )

    turmas = [turma for turma in turmas if turma]
    return sorted(turmas)


def listar_alunos():
    with conectar_banco() as conexao:
        alunos = conexao.execute(
            """
            SELECT
                id,
                nome,
                turma,
                nascimento,
                cpf,
                professor,
                endereco,
                email,
                responsavel
            FROM alunos
            ORDER BY turma, nome
            """
        ).fetchall()

        emails_usuarios, cpfs_usuarios = identidades_usuarios_aluno(conexao)

    resultado = []
    for aluno in alunos:
        dado = linha_aluno(aluno)
        resultado.append(marcar_aluno_adicionado_por_admin(dado, emails_usuarios, cpfs_usuarios))
    return resultado


def buscar_aluno(aluno_id):
    with conectar_banco() as conexao:
        aluno = conexao.execute(
            """
            SELECT
                id,
                nome,
                turma,
                nascimento,
                cpf,
                professor,
                endereco,
                email,
                responsavel
            FROM alunos
            WHERE id = ?
            """,
            (aluno_id,),
        ).fetchone()
        emails_usuarios, cpfs_usuarios = identidades_usuarios_aluno(conexao)

    dado = linha_aluno(aluno)
    if not dado:
        return None
    return marcar_aluno_adicionado_por_admin(dado, emails_usuarios, cpfs_usuarios)


def buscar_aluno_por_email_ou_cpf(email, cpf):
    filtros = []
    valores = []

    if email:
        filtros.append("LOWER(email) = ?")
        valores.append(email.lower())

    if cpf:
        filtros.append("cpf = ?")
        valores.append(cpf)

    if not filtros:
        return None

    consulta = f"""
        SELECT
            id,
            nome,
            turma,
            nascimento,
            cpf,
            professor,
            endereco,
            email,
            responsavel
        FROM alunos
        WHERE {' OR '.join(filtros)}
        ORDER BY id
        LIMIT 1
    """

    with conectar_banco() as conexao:
        aluno = conexao.execute(consulta, valores).fetchone()
        emails_usuarios, cpfs_usuarios = identidades_usuarios_aluno(conexao)

    dado = linha_aluno(aluno)
    if not dado:
        return None
    return marcar_aluno_adicionado_por_admin(dado, emails_usuarios, cpfs_usuarios)


def criar_aluno(dados):
    with conectar_banco() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO alunos (
                nome,
                turma,
                nascimento,
                cpf,
                professor,
                endereco,
                email,
                responsavel
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dados["nome"],
                dados["turma"],
                dados["nascimento"],
                dados["cpf"],
                dados["professor"],
                dados["endereco"],
                dados["email"],
                dados["responsavel"],
            ),
        )
    return buscar_aluno(cursor.lastrowid)


def atualizar_aluno(aluno_id, dados):
    existente = buscar_aluno(aluno_id)
    if not existente:
        return None

    dados_atualizados = {
        "nome": dados.get("nome", existente["nome"]),
        "turma": dados.get("turma", existente["turma"]),
        "nascimento": dados.get("nascimento", existente["nascimento"]),
        "cpf": dados.get("cpf", existente["cpf"]),
        "professor": dados.get("professor", existente["professor"]),
        "endereco": dados.get("endereco", existente["endereco"]),
        "email": dados.get("email", existente["email"]),
        "responsavel": dados.get("responsavel", existente["responsavel"]),
    }

    with conectar_banco() as conexao:
        cursor = conexao.execute(
            """
            UPDATE alunos
            SET
                nome = ?,
                turma = ?,
                nascimento = ?,
                cpf = ?,
                professor = ?,
                endereco = ?,
                email = ?,
                responsavel = ?
            WHERE id = ?
            """,
            (
                dados_atualizados["nome"],
                dados_atualizados["turma"],
                dados_atualizados["nascimento"],
                dados_atualizados["cpf"],
                dados_atualizados["professor"],
                dados_atualizados["endereco"],
                dados_atualizados["email"],
                dados_atualizados["responsavel"],
                aluno_id,
            ),
        )

        if cursor.rowcount == 0:
            return None
    return buscar_aluno(aluno_id)


def criar_ou_atualizar_aluno_de_cadastro(dados):
    existente = buscar_aluno_por_email_ou_cpf(dados["email"], dados["cpf"])

    if not existente:
        return criar_aluno(dados)

    dados_atualizados = {
        "nome": dados["nome"] or existente["nome"],
        "turma": dados["turma"] or existente["turma"],
        "nascimento": dados["nascimento"] or existente["nascimento"],
        "cpf": dados["cpf"] or existente["cpf"],
        "professor": dados["professor"] or existente["professor"],
        "endereco": dados["endereco"] or existente["endereco"],
        "email": dados["email"] or existente["email"],
        "responsavel": dados["responsavel"] or existente["responsavel"],
    }
    return atualizar_aluno(existente["id"], dados_atualizados)


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


def buscar_chamada(data_chamada):
    with conectar_banco() as conexao:
        registros = conexao.execute(
            """
            SELECT aluno_id, status
            FROM chamadas
            WHERE data = ?
            """,
            (data_chamada,),
        ).fetchall()
    return {registro["aluno_id"]: registro["status"] for registro in registros}


def salvar_chamada(data_chamada, registros):
    with conectar_banco() as conexao:
        conexao.executemany(
            """
            INSERT INTO chamadas (aluno_id, data, status)
            VALUES (?, ?, ?)
            ON CONFLICT(aluno_id, data) DO UPDATE SET
                status = excluded.status,
                atualizado_em = CURRENT_TIMESTAMP
            """,
            [(registro["aluno_id"], data_chamada, registro["status"]) for registro in registros],
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
            SET
                titulo = ?,
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


def gerar_hash_senha(senha, salt_hex=None):
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    senha_hash = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, 120_000).hex()
    return salt.hex(), senha_hash


def buscar_usuario_por_email(email):
    with conectar_banco() as conexao:
        usuario = conexao.execute(
            """
            SELECT
                id,
                nome,
                email,
                senha_hash,
                salt,
                tipo,
                turma,
                disciplinas_turmas,
                cpf,
                nascimento,
                criado_em
            FROM usuarios
            WHERE LOWER(email) = ?
            """,
            (email.lower(),),
        ).fetchone()
    return usuario


def buscar_usuario_por_id(usuario_id):
    with conectar_banco() as conexao:
        usuario = conexao.execute(
            """
            SELECT
                id,
                nome,
                email,
                tipo,
                turma,
                disciplinas_turmas,
                cpf,
                nascimento,
                criado_em
            FROM usuarios
            WHERE id = ?
            """,
            (usuario_id,),
        ).fetchone()
    return linha_usuario_publica(usuario)


def criar_usuario(dados):
    salt_hex, senha_hash = gerar_hash_senha(dados["senha"])

    with conectar_banco() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO usuarios (
                nome,
                email,
                senha_hash,
                salt,
                tipo,
                turma,
                disciplinas_turmas,
                cpf,
                nascimento
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dados["nome"],
                dados["email"],
                senha_hash,
                salt_hex,
                dados["tipo"],
                dados["turma"],
                dados["disciplinas_turmas"],
                dados["cpf"],
                dados["nascimento"],
            ),
        )
        usuario = conexao.execute(
            """
            SELECT
                id,
                nome,
                email,
                tipo,
                turma,
                disciplinas_turmas,
                cpf,
                nascimento,
                criado_em
            FROM usuarios
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return linha_usuario_publica(usuario)


def autenticar_usuario(email, senha):
    usuario = buscar_usuario_por_email(email)
    if not usuario:
        return None

    _, senha_hash = gerar_hash_senha(senha, usuario["salt"])
    if senha_hash != usuario["senha_hash"]:
        return None

    return buscar_usuario_por_id(usuario["id"])


def criar_sessao(usuario_id):
    token = secrets.token_urlsafe(32)
    SESSOES[token] = usuario_id
    return token


def remover_sessao(token):
    if token:
        SESSOES.pop(token, None)


def atualizar_usuario_por_id(usuario_id, campos):
    if not campos:
        return buscar_usuario_por_id(usuario_id)

    permitidos = {
        "nome",
        "email",
        "turma",
        "disciplinas_turmas",
        "cpf",
        "nascimento",
    }
    campos_validos = {chave: valor for chave, valor in campos.items() if chave in permitidos}
    if not campos_validos:
        return buscar_usuario_por_id(usuario_id)

    colunas = ", ".join(f"{chave} = ?" for chave in campos_validos.keys())
    valores = list(campos_validos.values()) + [usuario_id]

    with conectar_banco() as conexao:
        cursor = conexao.execute(
            f"""
            UPDATE usuarios
            SET {colunas}
            WHERE id = ?
            """,
            valores,
        )
        if cursor.rowcount == 0:
            return None

    return buscar_usuario_por_id(usuario_id)


class ListaChamadaHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.enviar_cabecalhos_cors()
        self.end_headers()

    def do_GET(self):
        try:
            rota = urlparse(self.path)

            if rota.path == "/app.js":
                return self.servir_app_js()

            if rota.path == "/api/alunos":
                return self.api_listar_alunos()

            if rota.path.startswith("/api/alunos/"):
                return self.api_buscar_aluno_por_id(rota.path)

            if rota.path == "/api/chamada":
                return self.api_buscar_chamada(rota.query)

            if rota.path == "/api/auth/eu":
                return self.api_auth_eu()

            if rota.path == "/api/turmas":
                return self.api_listar_turmas()

            if rota.path == "/api/perfil-aluno":
                return self.api_perfil_aluno()

            if rota.path == "/api/tarefas" or rota.path == "/tarefas":
                return self.api_listar_tarefas()

            if rota.path.startswith("/api/tarefas/"):
                return self.api_buscar_tarefa_por_id(rota.path.replace("/api", "", 1))

            if rota.path.startswith("/tarefas/"):
                return self.api_buscar_tarefa_por_id(rota.path)

            if rota.path == "/favicon.ico":
                self.send_response(204)
                self.enviar_cabecalhos_cors()
                self.end_headers()
                return

            if self.servir_recurso_estatico(rota.path):
                return

            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
        except Exception:
            traceback.print_exc()
            self.enviar_json({"erro": "Erro interno do servidor."}, status=500)

    def do_POST(self):
        try:
            rota = urlparse(self.path)

            if rota.path == "/api/alunos":
                return self.api_criar_aluno()

            if rota.path == "/api/chamada":
                return self.api_salvar_chamada()

            if rota.path == "/api/auth/cadastro":
                return self.api_auth_cadastro()

            if rota.path == "/api/auth/login":
                return self.api_auth_login()

            if rota.path == "/api/auth/logout":
                return self.api_auth_logout()

            if rota.path == "/api/tarefas" or rota.path == "/tarefas":
                return self.api_criar_tarefa()

            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
        except Exception:
            traceback.print_exc()
            self.enviar_json({"erro": "Erro interno do servidor."}, status=500)

    def do_PUT(self):
        try:
            rota = urlparse(self.path)

            if rota.path == "/api/perfil-aluno":
                return self.api_atualizar_perfil_aluno()

            if rota.path.startswith("/tarefas/"):
                return self.api_atualizar_tarefa(rota.path)

            if rota.path.startswith("/api/tarefas/"):
                return self.api_atualizar_tarefa(rota.path.replace("/api", "", 1))

            if rota.path.startswith("/api/alunos/"):
                return self.api_atualizar_aluno(rota.path)

            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
        except Exception:
            traceback.print_exc()
            self.enviar_json({"erro": "Erro interno do servidor."}, status=500)

    def do_DELETE(self):
        try:
            rota = urlparse(self.path)

            if rota.path.startswith("/tarefas/"):
                return self.api_remover_tarefa(rota.path)

            if rota.path.startswith("/api/tarefas/"):
                return self.api_remover_tarefa(rota.path.replace("/api", "", 1))

            if rota.path.startswith("/api/alunos/"):
                return self.api_remover_aluno(rota.path)

            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
        except Exception:
            traceback.print_exc()
            self.enviar_json({"erro": "Erro interno do servidor."}, status=500)

    def log_message(self, format, *args):
        return

    def enviar_cabecalhos_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def enviar_bytes(self, conteudo, content_type, status=200, cabecalhos_extras=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(conteudo)))
        self.enviar_cabecalhos_cors()

        if cabecalhos_extras:
            for nome, valor in cabecalhos_extras.items():
                self.send_header(nome, valor)

        self.end_headers()
        self.wfile.write(conteudo)

    def enviar_json(self, dados, status=200, cabecalhos_extras=None):
        resposta = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.enviar_bytes(
            resposta,
            "application/json; charset=utf-8",
            status=status,
            cabecalhos_extras=cabecalhos_extras,
        )

    def servir_app_js(self):
        caminho = STATIC_DIR / "app.js"
        if not caminho.exists() or caminho.is_dir():
            self.enviar_json({"erro": "Arquivo app.js nao encontrado."}, status=404)
            return

        self.enviar_bytes(
            caminho.read_bytes(),
            "application/javascript; charset=utf-8",
            cabecalhos_extras={"Cache-Control": "no-store"},
        )

    def caminho_estatico(self, path):
        arquivo = ROTAS_HTML.get(path, path.lstrip("/"))
        if not arquivo:
            arquivo = "index.html"

        caminho = (STATIC_DIR / arquivo).resolve()

        try:
            caminho.relative_to(STATIC_DIR.resolve())
        except ValueError:
            return None

        if not caminho.exists() or caminho.is_dir():
            return None

        return caminho

    def servir_recurso_estatico(self, path):
        caminho = self.caminho_estatico(path)
        if not caminho:
            return False

        content_type, _ = mimetypes.guess_type(caminho.name)
        if caminho.suffix in {".html", ".css", ".js"}:
            content_type = f"{content_type or 'text/plain'}; charset=utf-8"
        else:
            content_type = content_type or "application/octet-stream"

        self.enviar_bytes(caminho.read_bytes(), content_type)
        return True

    def ler_json(self):
        tamanho = int(self.headers.get("Content-Length", 0))
        if tamanho == 0:
            raise ValueError("O corpo da requisicao esta vazio.")

        corpo = self.rfile.read(tamanho).decode("utf-8")

        try:
            return json.loads(corpo)
        except json.JSONDecodeError as erro:
            raise ValueError("JSON invalido.") from erro

    def id_da_rota(self, path, prefixo):
        base = prefixo.rstrip("/")
        inicio = f"{base}/"

        if not path.startswith(inicio):
            return None

        trecho_id = path[len(inicio):]
        if not trecho_id or "/" in trecho_id:
            return None

        return trecho_id

    def cookies_recebidos(self):
        cabecalho = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie()
        if cabecalho:
            jar.load(cabecalho)
        return jar

    def token_sessao(self):
        cookie = self.cookies_recebidos().get(SESSION_COOKIE)
        return cookie.value if cookie else None

    def usuario_logado(self):
        token = self.token_sessao()
        usuario_id = SESSOES.get(token)
        if not usuario_id:
            return None
        return buscar_usuario_por_id(usuario_id)

    def exigir_usuario_logado(self):
        usuario = self.usuario_logado()
        if not usuario:
            self.enviar_json({"erro": "Sessao nao encontrada. Faça login novamente."}, status=401)
            return None
        return usuario

    def exigir_professor(self):
        usuario = self.exigir_usuario_logado()
        if not usuario:
            return None
        if usuario.get("tipo") != "professor":
            self.enviar_json({"erro": "Acesso permitido somente para professor."}, status=403)
            return None
        return usuario

    def turma_usuario_aluno(self, usuario):
        if not usuario or usuario.get("tipo") != "aluno":
            return ""
        return texto_limpo(usuario.get("turma"))

    # ----- API ALUNOS -----

    def api_listar_alunos(self):
        usuario = self.exigir_usuario_logado()
        if not usuario:
            return

        alunos = listar_alunos()
        turmas = listar_turmas()

        # Aluno so pode visualizar (somente leitura) e apenas a propria turma.
        if usuario.get("tipo") == "aluno":
            turma_aluno = self.turma_usuario_aluno(usuario)
            if turma_aluno:
                alunos = [aluno for aluno in alunos if aluno["turma"] == turma_aluno]
                turmas = [turma_aluno]
            else:
                alunos = []
                turmas = []

        # Para aluno, escondemos campos sensiveis.
        if usuario.get("tipo") == "aluno":
            alunos = [
                {
                    "id": aluno["id"],
                    "nome": aluno["nome"],
                    "turma": aluno["turma"],
                }
                for aluno in alunos
            ]

        turma_filtro = parse_qs(urlparse(self.path).query).get("turma", [""])[0].strip()
        if turma_filtro:
            alunos_filtrados = [aluno for aluno in alunos if aluno["turma"] == turma_filtro]
            self.enviar_json(alunos_filtrados)
            return

        self.enviar_json({"alunos": alunos, "turmas": turmas})

    def api_buscar_aluno_por_id(self, path):
        usuario = self.exigir_usuario_logado()
        if not usuario:
            return

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

        if usuario.get("tipo") == "aluno":
            turma_aluno = self.turma_usuario_aluno(usuario)
            if not turma_aluno or aluno.get("turma") != turma_aluno:
                self.enviar_json({"erro": "Acesso negado para visualizar este aluno."}, status=403)
                return
            aluno = {"id": aluno["id"], "nome": aluno["nome"], "turma": aluno["turma"]}

        self.enviar_json({"aluno": aluno})

    def api_criar_aluno(self):
        usuario = self.exigir_professor()
        if not usuario:
            return

        try:
            dados = validar_dados_aluno(self.ler_json())
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        aluno = criar_ou_atualizar_aluno_de_cadastro(dados)
        self.enviar_json({"mensagem": "Aluno cadastrado com sucesso.", "aluno": aluno}, status=201)

    def api_atualizar_aluno(self, path):
        usuario = self.exigir_professor()
        if not usuario:
            return

        aluno_id_texto = self.id_da_rota(path, "/api/alunos")
        if not aluno_id_texto:
            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
            return

        try:
            aluno_id = validar_id(aluno_id_texto)
            dados = validar_dados_aluno(self.ler_json())
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        aluno = atualizar_aluno(aluno_id, dados)
        if not aluno:
            self.enviar_json({"erro": "Aluno nao encontrado."}, status=404)
            return

        self.enviar_json({"mensagem": "Aluno atualizado com sucesso.", "aluno": aluno})

    def api_remover_aluno(self, path):
        usuario = self.exigir_professor()
        if not usuario:
            return

        aluno_id_texto = self.id_da_rota(path, "/api/alunos")
        if not aluno_id_texto:
            self.enviar_json({"erro": "Rota nao encontrada."}, status=404)
            return

        try:
            aluno_id = validar_id(aluno_id_texto)
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        if not remover_aluno(aluno_id):
            self.enviar_json({"erro": "Aluno nao encontrado."}, status=404)
            return

        self.enviar_json({"mensagem": "Aluno removido com sucesso."})

    # ----- API CHAMADA -----

    def api_buscar_chamada(self, query_string):
        usuario = self.exigir_usuario_logado()
        if not usuario:
            return

        parametros = parse_qs(query_string)
        data_chamada = parametros.get("data", [""])[0]

        if not data_chamada:
            self.enviar_json({"erro": "Informe a data da chamada."}, status=400)
            return

        try:
            data_chamada = validar_data(data_chamada)
        except ValueError:
            self.enviar_json({"erro": "Data invalida. Use o formato AAAA-MM-DD."}, status=400)
            return

        alunos = listar_alunos()
        if usuario.get("tipo") == "aluno":
            turma_aluno = self.turma_usuario_aluno(usuario)
            if turma_aluno:
                alunos = [aluno for aluno in alunos if aluno["turma"] == turma_aluno]
            else:
                alunos = []

        chamada_atual = buscar_chamada(data_chamada)
        resumo = gerar_resumo(alunos, chamada_atual)
        registros = [
            {"aluno_id": aluno_id, "status": status}
            for aluno_id, status in chamada_atual.items()
        ]

        if usuario.get("tipo") == "aluno":
            ids_permitidos = {aluno["id"] for aluno in alunos}
            registros = [registro for registro in registros if registro["aluno_id"] in ids_permitidos]

        self.enviar_json({"data": data_chamada, "registros": registros, "resumo": resumo})

    def api_salvar_chamada(self):
        usuario = self.exigir_professor()
        if not usuario:
            return

        try:
            dados = self.ler_json()
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        data_chamada = texto_limpo(dados.get("data"))
        registros = dados.get("registros", [])

        if not data_chamada:
            self.enviar_json({"erro": "Informe a data da chamada."}, status=400)
            return

        try:
            data_chamada = validar_data(data_chamada)
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

            status = texto_limpo(registro.get("status")).lower()
            if status not in STATUS_VALIDOS:
                self.enviar_json({"erro": "Status invalido. Use presente, faltou ou atrasado."}, status=400)
                return

            registros_limpos.append({"aluno_id": aluno_id, "status": status})

        try:
            salvar_chamada(data_chamada, registros_limpos)
        except sqlite3.IntegrityError:
            self.enviar_json({"erro": "Um ou mais alunos enviados nao existem mais no banco."}, status=400)
            return

        resumo = gerar_resumo(listar_alunos(), buscar_chamada(data_chamada))
        self.enviar_json({"mensagem": "Chamada salva com sucesso.", "resumo": resumo})

    # ----- API AUTH -----

    def api_listar_turmas(self):
        self.enviar_json({"turmas": listar_turmas()})

    def api_auth_cadastro(self):
        try:
            dados = self.ler_json()
            tipo = validar_tipo_usuario(dados.get("tipo"))
            nome = validar_texto_obrigatorio(dados.get("nome"), "o nome")
            email = validar_email(dados.get("email"))
            senha = validar_senha(dados.get("senha"))
            turma = texto_limpo(dados.get("turma"))
            disciplinas_turmas = texto_limpo(dados.get("disciplinas_turmas"))
            cpf = normalizar_cpf(dados.get("cpf"))
            nascimento = texto_limpo(dados.get("nascimento"))
            if nascimento:
                nascimento = validar_data(nascimento)
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        if tipo == "professor" and not disciplinas_turmas:
            self.enviar_json({"erro": "Informe as disciplinas ou turmas do professor."}, status=400)
            return

        if tipo == "aluno" and not turma:
            self.enviar_json({"erro": "Informe a turma do aluno."}, status=400)
            return

        try:
            usuario = criar_usuario(
                {
                    "nome": nome,
                    "email": email,
                    "senha": senha,
                    "tipo": tipo,
                    "turma": turma,
                    "disciplinas_turmas": disciplinas_turmas,
                    "cpf": cpf,
                    "nascimento": nascimento,
                }
            )
        except sqlite3.IntegrityError:
            self.enviar_json({"erro": "Ja existe um usuario cadastrado com este e-mail."}, status=400)
            return

        resposta = {"mensagem": "Cadastro realizado com sucesso.", "usuario": usuario}

        if tipo == "aluno":
            aluno = criar_ou_atualizar_aluno_de_cadastro(
                {
                    "nome": nome,
                    "turma": turma,
                    "nascimento": nascimento,
                    "cpf": cpf,
                    "professor": "",
                    "endereco": "",
                    "email": email,
                    "responsavel": "",
                }
            )
            resposta["aluno"] = aluno

        self.enviar_json(resposta, status=201)

    def api_auth_login(self):
        try:
            dados = self.ler_json()
            email = validar_email(dados.get("email"))
            senha = validar_senha(dados.get("senha"))
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        usuario = autenticar_usuario(email, senha)
        if not usuario:
            self.enviar_json({"erro": "E-mail ou senha invalidos."}, status=401)
            return

        token = criar_sessao(usuario["id"])
        self.enviar_json(
            {"mensagem": "Login realizado com sucesso.", "usuario": usuario},
            cabecalhos_extras={
                "Set-Cookie": f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400"
            },
        )

    def api_auth_logout(self):
        remover_sessao(self.token_sessao())
        self.enviar_json(
            {"mensagem": "Logout realizado com sucesso."},
            cabecalhos_extras={
                "Set-Cookie": f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
            },
        )

    def api_auth_eu(self):
        usuario = self.usuario_logado()
        if not usuario:
            self.enviar_json({"erro": "Sessao nao encontrada."}, status=401)
            return

        self.enviar_json({"usuario": usuario})

    def api_perfil_aluno(self):
        usuario = self.exigir_usuario_logado()
        if not usuario:
            return

        if usuario.get("tipo") != "aluno":
            self.enviar_json({"erro": "Endpoint disponivel apenas para aluno."}, status=403)
            return

        aluno = buscar_aluno_por_email_ou_cpf(usuario.get("email"), usuario.get("cpf"))
        if not aluno:
            self.enviar_json({"erro": "Aluno vinculado nao encontrado."}, status=404)
            return

        self.enviar_json({"aluno": aluno})

    def api_atualizar_perfil_aluno(self):
        usuario = self.exigir_usuario_logado()
        if not usuario:
            return

        if usuario.get("tipo") != "aluno":
            self.enviar_json({"erro": "Endpoint disponivel apenas para aluno."}, status=403)
            return

        aluno = buscar_aluno_por_email_ou_cpf(usuario.get("email"), usuario.get("cpf"))
        if not aluno:
            self.enviar_json({"erro": "Aluno vinculado nao encontrado."}, status=404)
            return

        try:
            dados = self.ler_json()
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        # Aluno altera somente seus dados de contato.
        try:
            atualizacao = {
                "email": validar_email(dados.get("email")) if texto_limpo(dados.get("email")) else aluno["email"],
                "endereco": texto_limpo(dados.get("endereco")) or aluno["endereco"],
                "responsavel": texto_limpo(dados.get("responsavel")) or aluno["responsavel"],
            }
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        try:
            aluno_atualizado = atualizar_aluno(aluno["id"], atualizacao)
        except ValueError as erro:
            self.enviar_json({"erro": str(erro)}, status=400)
            return

        if not aluno_atualizado:
            self.enviar_json({"erro": "Nao foi possivel atualizar o perfil do aluno."}, status=400)
            return

        # Mantem tabela de usuarios sincronizada para login por e-mail.
        try:
            atualizar_usuario_por_id(usuario["id"], {"email": aluno_atualizado["email"]})
        except sqlite3.IntegrityError:
            self.enviar_json({"erro": "Ja existe outro usuario com este e-mail."}, status=400)
            return

        self.enviar_json({"mensagem": "Perfil atualizado com sucesso.", "aluno": aluno_atualizado})

    # ----- API TAREFAS -----

    def api_listar_tarefas(self):
        self.enviar_json({"tarefas": listar_tarefas()})

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

        titulo = texto_limpo(dados.get("titulo"))
        descricao = texto_limpo(dados.get("descricao"))
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

        titulo = texto_limpo(dados.get("titulo"))
        descricao = texto_limpo(dados.get("descricao"))
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

        if not remover_tarefa(tarefa_id):
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

