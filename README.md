# Lista de Chamada

Projeto simples feito para trabalho escolar.

O sistema usa:

- HTML
- CSS
- JavaScript
- API em Python
- banco SQLite

O objetivo e mostrar uma lista de chamada funcionando de forma facil de entender.

## O que o sistema faz

- cadastra alunos
- separa alunos por turma
- permite escolher a data da chamada
- marca `presente`, `faltou` ou `atrasado`
- salva tudo em um banco SQLite
- mostra um resumo com totais

## Como iniciar o projeto

1. Abra o terminal na pasta do projeto.
2. Execute o comando abaixo:

```bash
python server.py
```

3. Depois abra o navegador neste endereco:

```text
http://127.0.0.1:8000
```

4. Na primeira execucao, o arquivo `db.sqlite3` sera criado automaticamente.

## Como usar o sistema

1. Digite o nome do aluno.
2. Digite a turma.
3. Clique em `Adicionar aluno`.
4. Escolha a data da chamada.
5. Se quiser, filtre por turma.
6. Marque cada aluno como `Presente`, `Faltou` ou `Atrasado`.
7. Clique em `Salvar chamada`.

## Estrutura do projeto

- `server.py`: servidor principal, API e acesso ao banco SQLite
- `static/index.html`: estrutura da pagina
- `static/style.css`: estilo visual da pagina
- `static/app.js`: logica do front-end e comunicacao com a API

## Rotas da API

### `GET /api/alunos`

Retorna todos os alunos cadastrados e a lista de turmas.

### `POST /api/alunos`

Cadastra um novo aluno.

Exemplo de envio:

```json
{
  "nome": "Maria Silva",
  "turma": "3A"
}
```

### `GET /api/chamada?data=AAAA-MM-DD`

Busca a chamada de uma data especifica.

Exemplo:

```text
/api/chamada?data=2026-04-10
```

### `POST /api/chamada`

Salva ou atualiza a chamada do dia.

Exemplo de envio:

```json
{
  "data": "2026-04-10",
  "registros": [
    { "aluno_id": 1, "status": "presente" },
    { "aluno_id": 2, "status": "faltou" }
  ]
}
```

## Como explicar o projeto na apresentacao

Voce pode falar algo assim:

"Nosso projeto e uma lista de chamada simples. A parte visual foi feita com HTML, CSS e JavaScript. O JavaScript conversa com uma API feita em Python. Essa API recebe os dados, salva no banco SQLite e depois devolve as informacoes para a tela."

## Resumo tecnico bem simples

- o HTML monta a estrutura da pagina
- o CSS deixa a tela organizada e bonita
- o JavaScript controla os botoes, formularios e atualizacao da tabela
- o Python cria a API e salva os dados
- o SQLite guarda os alunos e as chamadas

## Observacao

Este projeto foi feito para ser simples, funcional e facil de explicar em sala.
