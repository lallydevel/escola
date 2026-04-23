(() => {
    const estado = {
        usuario: null,
        alunos: [],
        chamada: new Map(),
        turmas: [],
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

    async function requestJson(url, options = {}) {
        const resposta = await fetch(url, {
            credentials: "same-origin",
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
        });

        const texto = await resposta.text();
        let dados = {};
        if (texto) {
            try {
                dados = JSON.parse(texto);
            } catch {
                dados = {};
            }
        }

        if (!resposta.ok) {
            const erro = new Error(dados.erro || "Nao foi possivel concluir a operacao.");
            erro.status = resposta.status;
            erro.payload = dados;
            throw erro;
        }

        return dados;
    }

    function getJson(url) {
        return requestJson(url, { method: "GET" });
    }

    function postJson(url, dados) {
        return requestJson(url, {
            method: "POST",
            body: JSON.stringify(dados),
        });
    }

    function putJson(url, dados) {
        return requestJson(url, {
            method: "PUT",
            body: JSON.stringify(dados),
        });
    }

    function deleteJson(url) {
        return requestJson(url, { method: "DELETE" });
    }

    function caminhoNormalizado(href) {
        try {
            return new URL(href, window.location.origin).pathname;
        } catch {
            return href;
        }
    }

    async function carregarUsuarioLogado() {
        try {
            const dados = await getJson("/api/auth/eu");
            estado.usuario = dados.usuario || null;
        } catch (erro) {
            if (erro.status === 401) {
                estado.usuario = null;
                return null;
            }
            throw erro;
        }
        return estado.usuario;
    }

    function atualizarMenuUsuario() {
        document.querySelectorAll("nav ul").forEach((lista) => {
            const itens = Array.from(lista.querySelectorAll("li"));
            const itemLogin = itens.find((item) => {
                const link = item.querySelector("a");
                return link && caminhoNormalizado(link.getAttribute("href") || "") === "/login.html";
            });
            const itemCadastro = itens.find((item) => {
                const link = item.querySelector("a");
                return link && caminhoNormalizado(link.getAttribute("href") || "") === "/cadastro.html";
            });

            if (!estado.usuario) {
                return;
            }

            if (itemCadastro) {
                itemCadastro.remove();
            }

            if (itemLogin) {
                const link = itemLogin.querySelector("a");
                link.textContent = estado.usuario.nome;
                link.href = "/registro.html";
            } else {
                const novoItem = document.createElement("li");
                const novoLink = document.createElement("a");
                novoLink.href = "/registro.html";
                novoLink.textContent = estado.usuario.nome;
                novoItem.appendChild(novoLink);
                lista.appendChild(novoItem);
            }
        });
    }

    async function carregarTurmas() {
        try {
            const dados = await getJson("/api/turmas");
            estado.turmas = Array.isArray(dados.turmas) ? dados.turmas : [];
        } catch {
            estado.turmas = [];
        }
        return estado.turmas;
    }

    function preencherSelectTurma(select, turmas, placeholder = "Selecione...") {
        if (!select) {
            return;
        }

        const valorAtual = select.value;
        select.innerHTML = "";

        const optionPadrao = document.createElement("option");
        optionPadrao.value = "";
        optionPadrao.textContent = placeholder;
        select.appendChild(optionPadrao);

        turmas.forEach((turma) => {
            const option = document.createElement("option");
            option.value = turma;
            option.textContent = turma;
            select.appendChild(option);
        });

        if (turmas.includes(valorAtual)) {
            select.value = valorAtual;
        }
    }

    function aplicarDatalistTurma(input, turmas) {
        if (!input || input.tagName !== "INPUT") {
            return;
        }

        const idLista = `${input.id || input.name || "turma"}-opcoes`;
        let datalist = document.getElementById(idLista);
        if (!datalist) {
            datalist = document.createElement("datalist");
            datalist.id = idLista;
            input.parentNode.appendChild(datalist);
        }

        datalist.innerHTML = turmas
            .map((turma) => `<option value="${textoSeguro(turma)}"></option>`)
            .join("");

        input.setAttribute("list", idLista);
    }

    function isProfessor() {
        return Boolean(estado.usuario && estado.usuario.tipo === "professor");
    }

    function isAluno() {
        return Boolean(estado.usuario && estado.usuario.tipo === "aluno");
    }

    function bloquearPorFaltaDeLogin(caixa) {
        if (estado.usuario) {
            return false;
        }

        mostrarMensagem(caixa, "Faca login para acessar esta funcionalidade.", "erro");
        window.setTimeout(() => {
            window.location.href = "/login.html";
        }, 900);
        return true;
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

    function bindLogin() {
        const form = document.querySelector(".login-box .formulario");
        if (!form) {
            return;
        }

        const caixa = criarCaixaMensagem(form);
        const email = form.querySelector('input[name="email"]');
        const senha = form.querySelector('input[name="senha"]');

        form.addEventListener("submit", async (evento) => {
            evento.preventDefault();
            limparMensagem(caixa);

            try {
                const dados = await postJson("/api/auth/login", {
                    email: email ? email.value.trim() : "",
                    senha: senha ? senha.value : "",
                });

                estado.usuario = dados.usuario || null;
                atualizarMenuUsuario();
                mostrarMensagem(caixa, dados.mensagem || "Login realizado com sucesso.");
                form.reset();
                window.setTimeout(() => {
                    window.location.href = "/chamada.html";
                }, 250);
            } catch (erro) {
                mostrarMensagem(caixa, erro.message, "erro");
            }
        });
    }

    async function bindCadastro() {
        const formProfessor = document.querySelector("#cadastro-professor .form-padrao");
        const formAluno = document.querySelector("#cadastro-aluno .form-padrao");

        const turmas = await carregarTurmas();

        if (formProfessor) {
            const caixaProfessor = criarCaixaMensagem(formProfessor);
            const nome = formProfessor.querySelector('input[name="nome"]');
            const email = formProfessor.querySelector('input[name="email"]');
            const senha = formProfessor.querySelector('input[name="senha"]');
            const disciplinas = formProfessor.querySelector('input[name="disciplinas"]');

            formProfessor.addEventListener("submit", async (evento) => {
                evento.preventDefault();
                limparMensagem(caixaProfessor);

                try {
                    const dados = await postJson("/api/auth/cadastro", {
                        tipo: "professor",
                        nome: nome ? nome.value.trim() : "",
                        email: email ? email.value.trim() : "",
                        senha: senha ? senha.value : "",
                        disciplinas_turmas: disciplinas ? disciplinas.value.trim() : "",
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
            const nome = formAluno.querySelector('input[name="nome"]');
            const nascimento = formAluno.querySelector('input[name="nascimento"]');
            const cpf = formAluno.querySelector('input[name="cpf"]');
            const turma = formAluno.querySelector('input[name="turma"], select[name="turma"]');
            const email = formAluno.querySelector('input[name="email"]');
            const senha = formAluno.querySelector('input[name="senha"]');

            if (turma && turma.tagName === "SELECT") {
                preencherSelectTurma(turma, turmas, "Selecione a turma");
            } else {
                aplicarDatalistTurma(turma, turmas);
            }

            formAluno.addEventListener("submit", async (evento) => {
                evento.preventDefault();
                limparMensagem(caixaAluno);

                try {
                    const dados = await postJson("/api/auth/cadastro", {
                        tipo: "aluno",
                        nome: nome ? nome.value.trim() : "",
                        nascimento: nascimento ? nascimento.value : "",
                        cpf: cpf ? cpf.value.trim() : "",
                        turma: turma ? turma.value.trim() : "",
                        email: email ? email.value.trim() : "",
                        senha: senha ? senha.value : "",
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

    async function bindCadastroAluno() {
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

        const turmas = await carregarTurmas();
        preencherSelectTurma(turma, turmas, "Selecione a turma");

        if (bloquearPorFaltaDeLogin(caixa)) {
            form.querySelectorAll("input, select, button").forEach((el) => {
                el.disabled = true;
            });
            return;
        }

        if (!isProfessor()) {
            mostrarMensagem(caixa, "Apenas professor pode cadastrar aluno.", "erro");
            form.querySelectorAll("input, select, button").forEach((el) => {
                el.disabled = true;
            });
            return;
        }

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

                const foiAdmin = dados.aluno && dados.aluno.adicionado_por_admin;
                const sufixo = foiAdmin ? " (adicionado por administrador)." : ".";
                mostrarMensagem(caixa, `${dados.mensagem || "Aluno cadastrado com sucesso"}${sufixo}`);
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

    async function bindChamada() {
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

        if (bloquearPorFaltaDeLogin(caixa)) {
            return;
        }

        const somenteVisualizacao = isAluno();
        if (somenteVisualizacao) {
            mostrarMensagem(caixa, "Acesso do aluno: visualizacao liberada, edicao bloqueada.");
            botaoSalvar.style.display = "none";
        }

        function statusAtual(alunoId) {
            return estado.chamada.get(alunoId) || "presente";
        }

        function alunosFiltrados() {
            const turmaSelecionada = filtroTurma.value;

            if (!turmaSelecionada) {
                return estado.alunos;
            }

            return estado.alunos.filter((aluno) => aluno.turma === turmaSelecionada);
        }

        function preencherTurmas(turmas) {
            const turmaAtual = filtroTurma.value;
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
            const disabled = somenteVisualizacao ? "disabled" : "";
            return `
                <label class="radio-status ${classe}">
                    <input type="radio" name="aluno-${alunoId}" data-aluno-id="${alunoId}" value="${valor}" ${checked} ${disabled}>
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
            estado.alunos = Array.isArray(dados.alunos)
                ? dados.alunos
                : (Array.isArray(dados) ? dados : []);

            const turmas = Array.isArray(dados.turmas)
                ? dados.turmas
                : [...new Set(estado.alunos.map((aluno) => aluno.turma).filter(Boolean))];
            preencherTurmas(turmas);
        }

        async function carregarChamada() {
            const dados = await getJson(`/api/chamada?data=${encodeURIComponent(dataChamada.value)}`);
            estado.chamada = new Map(
                (dados.registros || []).map((registro) => [Number(registro.aluno_id), registro.status]),
            );
        }

        async function atualizarTela() {
            await carregarAlunos();
            await carregarChamada();
            renderizarTabela();
        }

        tabela.addEventListener("change", (evento) => {
            if (somenteVisualizacao) {
                return;
            }

            const campo = evento.target.closest("input[data-aluno-id]");
            if (!campo) {
                return;
            }

            estado.chamada.set(Number(campo.dataset.alunoId), campo.value);
            renderizarResumo();
        });

        botaoAtualizar.addEventListener("click", async (evento) => {
            evento.preventDefault();
            limparMensagem(caixa);
            try {
                await atualizarTela();
            } catch (erro) {
                mostrarMensagem(caixa, erro.message, "erro");
            }
        });

        botaoSalvar.addEventListener("click", async (evento) => {
            evento.preventDefault();
            limparMensagem(caixa);

            if (somenteVisualizacao) {
                mostrarMensagem(caixa, "Aluno nao pode salvar chamada.", "erro");
                return;
            }

            try {
                const registros = estado.alunos.map((aluno) => ({
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
            limparMensagem(caixa);
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

    async function bindRegistro() {
        const form = document.getElementById("form-registro");
        if (!form) {
            return;
        }

        const caixa = criarCaixaMensagem(form);
        const painelProfessor = document.getElementById("registro-painel-professor");
        const selectAluno = document.getElementById("registro-aluno-select");
        const botaoExcluir = document.getElementById("registro-btn-excluir");

        const campos = {
            alunoId: document.getElementById("registro-aluno-id"),
            nome: document.getElementById("registro-nome"),
            turma: document.getElementById("registro-turma"),
            nascimento: document.getElementById("registro-nascimento"),
            cpf: document.getElementById("registro-cpf"),
            professor: document.getElementById("registro-professor"),
            endereco: document.getElementById("registro-endereco"),
            email: document.getElementById("registro-email"),
            responsavel: document.getElementById("registro-responsavel"),
            admin: document.getElementById("registro-admin-flag"),
        };

        const infoUsuario = {
            nome: document.getElementById("info-usuario-nome"),
            tipo: document.getElementById("info-usuario-tipo"),
            email: document.getElementById("info-usuario-email"),
            turma: document.getElementById("info-usuario-turma"),
            cpf: document.getElementById("info-usuario-cpf"),
            nascimento: document.getElementById("info-usuario-nascimento"),
        };

        if (bloquearPorFaltaDeLogin(caixa)) {
            form.querySelectorAll("input, select, button").forEach((el) => {
                el.disabled = true;
            });
            return;
        }

        if (infoUsuario.nome) infoUsuario.nome.textContent = estado.usuario.nome || "-";
        if (infoUsuario.tipo) infoUsuario.tipo.textContent = estado.usuario.tipo || "-";
        if (infoUsuario.email) infoUsuario.email.textContent = estado.usuario.email || "-";
        if (infoUsuario.turma) infoUsuario.turma.textContent = estado.usuario.turma || "-";
        if (infoUsuario.cpf) infoUsuario.cpf.textContent = estado.usuario.cpf || "-";
        if (infoUsuario.nascimento) infoUsuario.nascimento.textContent = estado.usuario.nascimento || "-";

        const turmas = await carregarTurmas();
        preencherSelectTurma(campos.turma, turmas, "Selecione a turma");

        let alunosProfessor = [];

        function atualizarListaProfessor(alunos, selecionadoId = "") {
            if (!selectAluno) {
                return;
            }

            selectAluno.innerHTML = alunos
                .map((aluno) => `<option value="${aluno.id}">${textoSeguro(aluno.nome)} (${textoSeguro(aluno.turma)})</option>`)
                .join("");

            if (!alunos.length) {
                return;
            }

            const alvo = String(selecionadoId || alunos[0].id);
            const existe = alunos.some((aluno) => String(aluno.id) === alvo);
            selectAluno.value = existe ? alvo : String(alunos[0].id);
        }

        function preencherFormularioAluno(aluno) {
            if (!aluno) {
                return;
            }

            campos.alunoId.value = String(aluno.id || "");
            campos.nome.value = aluno.nome || "";
            if (campos.turma && aluno.turma) {
                const possuiTurma = Array.from(campos.turma.options).some((option) => option.value === aluno.turma);
                if (!possuiTurma) {
                    const option = document.createElement("option");
                    option.value = aluno.turma;
                    option.textContent = aluno.turma;
                    campos.turma.appendChild(option);
                }
            }
            campos.turma.value = aluno.turma || "";
            campos.nascimento.value = aluno.nascimento || "";
            campos.cpf.value = aluno.cpf || "";
            campos.professor.value = aluno.professor || "";
            campos.endereco.value = aluno.endereco || "";
            campos.email.value = aluno.email || "";
            campos.responsavel.value = aluno.responsavel || "";
            campos.admin.value = aluno.adicionado_por_admin ? "Sim" : "Nao";

            if (isProfessor()) {
                form.querySelectorAll("input, select").forEach((el) => {
                    if (el.id === "registro-admin-flag") {
                        el.readOnly = true;
                        return;
                    }
                    el.disabled = false;
                    el.readOnly = false;
                });
                if (botaoExcluir) {
                    botaoExcluir.style.display = "inline-block";
                    botaoExcluir.disabled = false;
                }
                return;
            }

            const editaveisAluno = new Set(["registro-email", "registro-endereco", "registro-responsavel"]);
            form.querySelectorAll("input, select").forEach((el) => {
                if (editaveisAluno.has(el.id)) {
                    el.disabled = false;
                    el.readOnly = false;
                } else {
                    el.disabled = true;
                    el.readOnly = true;
                }
            });

            if (botaoExcluir) {
                botaoExcluir.style.display = "none";
            }
        }

        if (isProfessor()) {
            if (painelProfessor) {
                painelProfessor.style.display = "block";
            }

            try {
                const dados = await getJson("/api/alunos");
                alunosProfessor = Array.isArray(dados.alunos) ? dados.alunos : [];

                if (!alunosProfessor.length) {
                    mostrarMensagem(caixa, "Nenhum aluno cadastrado para edicao.", "erro");
                    if (botaoExcluir) {
                        botaoExcluir.disabled = true;
                    }
                    form.querySelectorAll("input, select, button").forEach((el) => {
                        el.disabled = true;
                    });
                    return;
                }

                atualizarListaProfessor(alunosProfessor);
                const primeiro = alunosProfessor[0];
                preencherFormularioAluno(primeiro);

                if (selectAluno) {
                    selectAluno.addEventListener("change", () => {
                        const selecionado = alunosProfessor.find((a) => String(a.id) === selectAluno.value);
                        preencherFormularioAluno(selecionado);
                    });
                }
            } catch (erro) {
                mostrarMensagem(caixa, erro.message, "erro");
                return;
            }
        } else {
            if (painelProfessor) {
                painelProfessor.style.display = "none";
            }

            try {
                const dados = await getJson("/api/perfil-aluno");
                preencherFormularioAluno(dados.aluno || null);
            } catch (erro) {
                mostrarMensagem(caixa, erro.message, "erro");
                return;
            }
        }

        form.addEventListener("submit", async (evento) => {
            evento.preventDefault();
            limparMensagem(caixa);

            try {
                if (isProfessor()) {
                    const alunoId = campos.alunoId.value;
                    if (!alunoId) {
                        throw new Error("Selecione um aluno para editar.");
                    }

                    const payload = {
                        nome: campos.nome.value.trim(),
                        turma: campos.turma.value.trim(),
                        nascimento: campos.nascimento.value,
                        cpf: campos.cpf.value.trim(),
                        professor: campos.professor.value.trim(),
                        endereco: campos.endereco.value.trim(),
                        email: campos.email.value.trim(),
                        responsavel: campos.responsavel.value.trim(),
                    };

                    const dados = await putJson(`/api/alunos/${encodeURIComponent(alunoId)}`, payload);
                    mostrarMensagem(caixa, dados.mensagem || "Aluno atualizado com sucesso.");

                    const recarga = await getJson("/api/alunos");
                    alunosProfessor = Array.isArray(recarga.alunos) ? recarga.alunos : [];
                    atualizarListaProfessor(alunosProfessor, alunoId);
                    const selecionado = alunosProfessor.find((a) => String(a.id) === String(alunoId));
                    preencherFormularioAluno(selecionado || alunosProfessor[0]);
                    return;
                }

                const dados = await putJson("/api/perfil-aluno", {
                    email: campos.email.value.trim(),
                    endereco: campos.endereco.value.trim(),
                    responsavel: campos.responsavel.value.trim(),
                });
                mostrarMensagem(caixa, dados.mensagem || "Perfil atualizado com sucesso.");
                preencherFormularioAluno(dados.aluno || null);
            } catch (erro) {
                mostrarMensagem(caixa, erro.message, "erro");
            }
        });

        if (botaoExcluir) {
            botaoExcluir.addEventListener("click", async () => {
                limparMensagem(caixa);

                if (!isProfessor()) {
                    mostrarMensagem(caixa, "Somente professor pode excluir aluno.", "erro");
                    return;
                }

                const alunoId = campos.alunoId.value;
                if (!alunoId) {
                    mostrarMensagem(caixa, "Selecione um aluno para excluir.", "erro");
                    return;
                }

                if (!window.confirm("Tem certeza que deseja excluir este aluno?")) {
                    return;
                }

                try {
                    const dados = await deleteJson(`/api/alunos/${encodeURIComponent(alunoId)}`);
                    mostrarMensagem(caixa, dados.mensagem || "Aluno removido com sucesso.");

                    const recarga = await getJson("/api/alunos");
                    alunosProfessor = Array.isArray(recarga.alunos) ? recarga.alunos : [];
                    if (!alunosProfessor.length) {
                        form.reset();
                        if (selectAluno) {
                            selectAluno.innerHTML = "";
                        }
                        return;
                    }

                    atualizarListaProfessor(alunosProfessor);
                    preencherFormularioAluno(alunosProfessor[0]);
                } catch (erro) {
                    mostrarMensagem(caixa, erro.message, "erro");
                }
            });
        }
    }

    async function iniciar() {
        try {
            await carregarUsuarioLogado();
        } catch {
            estado.usuario = null;
        }

        atualizarMenuUsuario();

        bindLogin();
        await bindCadastro();
        await bindCadastroAluno();
        await bindChamada();
        await bindRegistro();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            iniciar().catch(() => {
                // Evita quebra visual na inicializacao.
            });
        });
    } else {
        iniciar().catch(() => {
            // Evita quebra visual na inicializacao.
        });
    }
})();
