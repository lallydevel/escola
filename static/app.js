/*
    Este arquivo controla o comportamento da tela.

    Ele faz 4 coisas principais:
    1. busca dados na API
    2. atualiza a tabela de alunos
    3. permite trocar o status da chamada
    4. envia os dados para salvar no banco
*/

// Estado central da pagina.
// Aqui guardamos os alunos carregados e a chamada atual.
const estado = {
    alunos: [],
    chamada: new Map(),
};

// Referencias para elementos do HTML.
// Guardar tudo aqui evita repetir document.getElementById varias vezes.
const elementos = {
    formAluno: document.getElementById("form-aluno"),
    nome: document.getElementById("nome"),
    turma: document.getElementById("turma"),
    dataChamada: document.getElementById("data-chamada"),
    filtroTurma: document.getElementById("filtro-turma"),
    atualizarLista: document.getElementById("atualizar-lista"),
    salvarChamada: document.getElementById("salvar-chamada"),
    listaAlunos: document.getElementById("lista-alunos"),
    contadorAlunos: document.getElementById("contador-alunos"),
    mensagem: document.getElementById("mensagem"),
    resumoPresente: document.getElementById("resumo-presente"),
    resumoFalta: document.getElementById("resumo-falta"),
    resumoAtraso: document.getElementById("resumo-atraso"),
};


// Retorna a data de hoje no formato esperado pelo campo <input type="date">.
function dataHoje() {
    return new Date().toISOString().split("T")[0];
}


// Protege o HTML da tabela contra caracteres especiais digitados pelo usuario.
// Isso evita que texto do usuario seja interpretado como tag HTML.
function escapeHtml(texto) {
    return texto
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}


// Mostra uma mensagem visual na tela.
// O tipo pode ser "sucesso" ou "erro".
function mostrarMensagem(texto, tipo = "sucesso") {
    elementos.mensagem.textContent = texto;
    elementos.mensagem.className = `mensagem mensagem-${tipo}`;
}


// Esconde a caixa de mensagem quando nao houver nada para mostrar.
function limparMensagem() {
    elementos.mensagem.textContent = "";
    elementos.mensagem.className = "mensagem mensagem-escondida";
}


// Busca todos os alunos na API e atualiza o estado da aplicacao.
async function carregarAlunos() {
    const resposta = await fetch("/api/alunos");
    const dados = await resposta.json();

    // Guarda a lista de alunos em memoria.
    estado.alunos = dados.alunos;

    // Atualiza o select de turmas.
    preencherTurmas(dados.turmas);
}


// Busca na API os registros de chamada da data escolhida.
async function carregarChamada() {
    const data = elementos.dataChamada.value;
    const resposta = await fetch(`/api/chamada?data=${encodeURIComponent(data)}`);
    const dados = await resposta.json();

    // Converte a lista de registros em Map para consultar rapido por aluno_id.
    estado.chamada = new Map(
        dados.registros.map((registro) => [registro.aluno_id, registro.status]),
    );
}


// Preenche o filtro de turmas com os dados vindos da API.
function preencherTurmas(turmas) {
    // Guarda a turma atualmente selecionada para tentar manter a selecao.
    const turmaSelecionada = elementos.filtroTurma.value;

    // Recria o select do zero com a opcao padrao.
    elementos.filtroTurma.innerHTML = '<option value="">Todas as turmas</option>';

    // Cria uma opcao para cada turma encontrada.
    turmas.forEach((turma) => {
        const option = document.createElement("option");
        option.value = turma;
        option.textContent = turma;
        elementos.filtroTurma.appendChild(option);
    });

    // Se a turma antiga ainda existir, ela continua selecionada.
    elementos.filtroTurma.value = turmas.includes(turmaSelecionada) ? turmaSelecionada : "";
}


// Retorna apenas os alunos que devem aparecer na tela.
// Se nao houver filtro, retorna todos.
function alunosFiltrados() {
    const turmaSelecionada = elementos.filtroTurma.value;

    if (!turmaSelecionada) {
        return estado.alunos;
    }

    return estado.alunos.filter((aluno) => aluno.turma === turmaSelecionada);
}


// Descobre qual o status atual de um aluno.
function statusAtual(alunoId) {
    // Quando ainda nao existe chamada salva no banco, o aluno comeca como presente.
    return estado.chamada.get(alunoId) || "presente";
}


// Atualiza os numeros dos tres cards de resumo.
function renderizarResumo() {
    const resumo = { presente: 0, faltou: 0, atrasado: 0 };

    // Percorre apenas os alunos visiveis no filtro atual.
    alunosFiltrados().forEach((aluno) => {
        resumo[statusAtual(aluno.id)] += 1;
    });

    // Atualiza os valores mostrados no HTML.
    elementos.resumoPresente.textContent = resumo.presente;
    elementos.resumoFalta.textContent = resumo.faltou;
    elementos.resumoAtraso.textContent = resumo.atrasado;
}


// Monta novamente a tabela inteira com base nos dados atuais.
function renderizarTabela() {
    const alunos = alunosFiltrados();

    // Atualiza o contador acima da tabela.
    elementos.contadorAlunos.textContent = `${alunos.length} alunos carregados`;

    // Se nao houver alunos, mostramos uma linha vazia explicativa.
    if (alunos.length === 0) {
        elementos.listaAlunos.innerHTML = `
            <tr>
                <td colspan="3" class="vazio">Nenhum aluno encontrado para este filtro.</td>
            </tr>
        `;
        renderizarResumo();
        return;
    }

    // Construi as linhas da tabela com template string.
    elementos.listaAlunos.innerHTML = alunos
        .map((aluno) => {
            const status = statusAtual(aluno.id);

            return `
                <tr>
                    <td>${escapeHtml(aluno.nome)}</td>
                    <td>${escapeHtml(aluno.turma)}</td>
                    <td>
                        <div class="status-grupo">
                            ${criarBotaoStatus(aluno.id, "presente", "Presente", status)}
                            ${criarBotaoStatus(aluno.id, "faltou", "Faltou", status)}
                            ${criarBotaoStatus(aluno.id, "atrasado", "Atrasado", status)}
                        </div>
                    </td>
                </tr>
            `;
        })
        .join("");

    // Depois da tabela, atualiza o resumo.
    renderizarResumo();
}


// Gera o HTML de um dos botoes de status.
function criarBotaoStatus(alunoId, valor, label, statusAtualAluno) {
    // Se o status atual for igual ao valor do botao, ele recebe classe ativa.
    const ativo = statusAtualAluno === valor ? `ativo-${valor}` : "";

    return `
        <button
            type="button"
            class="status-botao ${ativo}"
            data-aluno-id="${alunoId}"
            data-status="${valor}"
        >
            ${label}
        </button>
    `;
}


// Faz a atualizacao completa da pagina:
// limpa mensagem, carrega alunos, carrega chamada e redesenha a tabela.
async function atualizarTela() {
    limparMensagem();
    await carregarAlunos();
    await carregarChamada();
    renderizarTabela();
}


// Envia o formulario de cadastro de aluno para a API.
async function cadastrarAluno(evento) {
    // Evita que o formulario recarregue a pagina.
    evento.preventDefault();
    limparMensagem();

    const resposta = await fetch("/api/alunos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            nome: elementos.nome.value.trim(),
            turma: elementos.turma.value.trim(),
        }),
    });

    // Converte a resposta para objeto JavaScript.
    const dados = await resposta.json();

    // Se a API retornar erro, mostramos a mensagem e paramos.
    if (!resposta.ok) {
        mostrarMensagem(dados.erro || "Nao foi possivel cadastrar o aluno.", "erro");
        return;
    }

    // Limpa o formulario.
    elementos.formAluno.reset();

    // Mostra mensagem de sucesso.
    mostrarMensagem(dados.mensagem);

    // Recarrega a tela para incluir o novo aluno.
    await atualizarTela();

    // Coloca o cursor de volta no campo nome.
    elementos.nome.focus();
}


// Captura cliques nos botoes de status dentro da tabela.
function trocarStatus(evento) {
    // closest procura o botao mais proximo do clique.
    const botao = evento.target.closest(".status-botao");

    // Se o clique nao foi em um botao de status, nao fazemos nada.
    if (!botao) {
        return;
    }

    // Le o aluno e o status a partir dos atributos data-*.
    const alunoId = Number(botao.dataset.alunoId);
    const status = botao.dataset.status;

    // Atualiza o estado em memoria.
    estado.chamada.set(alunoId, status);

    // Redesenha a tabela para destacar o botao ativo.
    renderizarTabela();
}


// Envia toda a chamada do dia para ser salva no banco.
async function salvarChamada() {
    limparMensagem();

    // Salva todos os alunos da pagina, mesmo quando um filtro de turma estiver ativo.
    const registros = estado.alunos.map((aluno) => ({
        aluno_id: aluno.id,
        status: statusAtual(aluno.id),
    }));

    // Se nao existir nenhum aluno, mostramos erro.
    if (registros.length === 0) {
        mostrarMensagem("Cadastre pelo menos um aluno antes de salvar a chamada.", "erro");
        return;
    }

    const resposta = await fetch("/api/chamada", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            data: elementos.dataChamada.value,
            registros,
        }),
    });

    // Converte a resposta da API.
    const dados = await resposta.json();

    // Se houver erro, mostra a mensagem.
    if (!resposta.ok) {
        mostrarMensagem(dados.erro || "Nao foi possivel salvar a chamada.", "erro");
        return;
    }

    // Mostra mensagem de sucesso.
    mostrarMensagem(dados.mensagem);

    // Recarrega a chamada salva no banco.
    await carregarChamada();

    // Redesenha a tabela e o resumo.
    renderizarTabela();
}


// Eventos principais da pagina.
// Cada linha liga uma acao do usuario a uma funcao JavaScript.
elementos.formAluno.addEventListener("submit", cadastrarAluno);
elementos.listaAlunos.addEventListener("click", trocarStatus);
elementos.salvarChamada.addEventListener("click", salvarChamada);
elementos.atualizarLista.addEventListener("click", atualizarTela);
elementos.filtroTurma.addEventListener("change", renderizarTabela);
elementos.dataChamada.addEventListener("change", atualizarTela);

// Ao abrir a pagina, colocamos a data de hoje automaticamente.
elementos.dataChamada.value = dataHoje();

// Tambem carregamos os dados iniciais.
atualizarTela().catch(() => {
    mostrarMensagem("Nao foi possivel carregar a lista de chamada.", "erro");
});








// NÃO SEI SE JÁ TEM Função para carregar alunos do banco de dados
async function carregarAlunos() {
    const listaAlunosCorpo = document.getElementById('lista-alunos');
    const filtroTurma = document.getElementById('filtro-turma').value;

    try {
        // Substitua pela URL da sua API
        const response = await fetch(`/api/alunos?turma=${filtroTurma}`);
        const alunos = await response.json();

        listaAlunosCorpo.innerHTML = ''; // Limpa a tabela

        if (alunos.length === 0) {
            listaAlunosCorpo.innerHTML = '<tr><td colspan="3" class="vazio">Nenhum aluno encontrado.</td></tr>';
            return;
        }

        alunos.forEach(aluno => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${aluno.nome}</td>
                <td>${aluno.turma}</td>
                <td>
                    <div class="actions">
                        <label class="btn-check">
                            <input type="radio" name="chamada-${aluno.id}" value="presente" checked> Presença
                        </label>
                        <label class="btn-check">
                            <input type="radio" name="chamada-${aluno.id}" value="falta"> Falta
                        </label>
                        <label class="btn-check">
                            <input type="radio" name="chamada-${aluno.id}" value="atraso"> Atraso
                        </label>
                    </div>
                </td>
            `;
            listaAlunosCorpo.appendChild(tr);
        });

        document.getElementById('contador-alunos').innerText = `${alunos.length} alunos carregados`;

    } catch (erro) {
        console.error("Erro ao buscar alunos:", erro);
    }
}

// Evento para o botão atualizar
document.getElementById('atualizar-lista').addEventListener('click', carregarAlunos);




// FUNÇÃO PARA SCROLL DAS PAGINAS
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();

        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);

        if (targetElement) {
            // Pegamos a posição do elemento menos 80px (altura do seu header)
            const offsetPosition = targetElement.offsetTop - 80;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    });
})

const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            entry.target.classList.add('active');
        }
    });
}, { threshold: 0.3 }); // Ativa quando 30% da seção estiver visível

document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            entry.target.classList.add('active');
        }
    });
}, { 
    threshold: 0.2 // Ativa quando 20% da seção aparecer na tela
});

// Seleciona todos os elementos que têm a classe 'reveal' e começa a observar
document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));

// FUNÇÃO PAG CADASTRO DE ALUNO - RESPONSÁVEL
document.getElementById('nascimento').addEventListener('change', function() {
    const dataNascimento = new Date(this.value);
    const hoje = new Date();
    
    let idade = hoje.getFullYear() - dataNascimento.getFullYear();
    const m = hoje.getMonth() - dataNascimento.getMonth();
    
    // Ajuste caso o aniversário ainda não tenha ocorrido este ano
    if (m < 0 || (m === 0 && hoje.getDate() < dataNascimento.getDate())) {
        idade--;
    }

    const campoResp = document.getElementById('campo-responsavel');
    const inputResp = document.getElementById('responsavel');

    if (idade < 18) {
        campoResp.classList.remove('hidden');
        inputResp.setAttribute('required', 'true');
    } else {
        campoResp.classList.add('hidden');
        inputResp.removeAttribute('required');
    }
});