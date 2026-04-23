# EduChamada

Sistema web para controle de chamada escolar com:
- autenticacao por perfil (`professor` e `aluno`)
- cadastro e edicao de alunos
- registro de presenca por data
- regras de acesso por permissao
- banco SQLite local

## 1. Visao geral

O projeto foi construido em:
- Frontend: HTML + CSS + JavaScript puro
- Backend: Python (`http.server`)
- Banco: SQLite

Objetivo principal:
- permitir que professor gerencie alunos e chamada
- permitir que aluno apenas visualize chamada e edite somente seus dados permitidos

## 2. Funcionalidades implementadas

### 2.1 Login e cadastro
- Cadastro de usuario professor e aluno
- Login com sessao em cookie HTTPOnly
- Endpoint para usuario logado (`/api/auth/eu`)
- No menu, apos login:
  - remove botoes `Login` e `Cadastro`
  - mostra o nome do usuario
  - clique no nome leva para `registro.html`

### 2.2 Controle de acesso por perfil
- Professor:
  - pode cadastrar, editar e remover alunos
  - pode salvar chamada
  - pode editar todos os campos do aluno em `registro.html`
- Aluno:
  - so visualiza dados da propria turma na chamada
  - nao pode salvar chamada
  - nao pode cadastrar/editar/remover alunos pela API administrativa
  - em `registro.html`, so pode editar: `email`, `endereco`, `responsavel`

### 2.3 Cadastro e edicao de alunos
- Cadastro completo do aluno com:
  - nome, turma, nascimento, cpf, professor, endereco, email, responsavel
- Campo `responsavel` com regra de menor de idade no frontend
- Marcador `adicionado_por_admin` no retorno da API
  - indica se aquele aluno foi inserido por professor/admin ou surgiu do cadastro de login do proprio aluno

### 2.4 Chamada
- Busca chamada por data
- Status por aluno:
  - `presente`
  - `faltou`
  - `atrasado`
- Resumo automatico de totais
- Salva chamada com upsert (atualiza se ja existir no mesmo dia)

### 2.5 Turmas dinamicas
- Turmas carregadas do banco via `/api/turmas`
- Usadas em:
  - `cadastro.html`
  - `cadastro_aluno.html`
  - `registro.html`
  - filtro de `chamada.html`

### 2.6 Correcao de validacao de email
- Ajustado mapeamento dos campos de cadastro no frontend
- Validacao backend centralizada em `validar_email`
- Atualizacao de email no perfil do aluno com tratamento de erro 400 (email invalido) e duplicidade

## 3. Paginas principais

- `index.html`: pagina inicial
- `login.html`: autenticacao
- `cadastro.html`: cadastro de login (professor/aluno)
- `cadastro_aluno.html`: cadastro administrativo de aluno (somente professor)
- `chamada.html`: lista e marcacao de chamada
- `registro.html`: visualizacao/edicao conforme perfil

## 4. API (resumo)

### Auth
- `POST /api/auth/cadastro`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/eu`

### Alunos
- `GET /api/alunos`
- `GET /api/alunos/{id}`
- `POST /api/alunos` (professor)
- `PUT /api/alunos/{id}` (professor)
- `DELETE /api/alunos/{id}` (professor)

### Perfil de aluno
- `GET /api/perfil-aluno` (aluno)
- `PUT /api/perfil-aluno` (aluno)

### Chamada
- `GET /api/chamada?data=AAAA-MM-DD`
- `POST /api/chamada` (professor)

### Turmas
- `GET /api/turmas`

## 5. Estrutura do projeto

```text
escola/
  server.py
  escola.db
  static/
    app.js
    index.html
    login.html
    cadastro.html
    cadastro_aluno.html
    chamada.html
    registro.html
    style.css
    index.css
    chamada.css
    registro.css
```

## 6. Como executar

### Requisitos
- Python 3.10+ (recomendado 3.12+)

### Passos
1. Abra terminal na pasta do projeto:
   - `C:\\Users\\Basil\\Desktop\\escola-main\\escola`
2. Execute:

```bash
python server.py
```

3. Acesse no navegador:

```text
http://127.0.0.1:8000
```

Observacao importante:
- Este projeto NAO usa Django.
- Se voce rodar `python manage.py runserver`, vai dar erro de arquivo inexistente.
- Comando correto deste projeto: `python server.py`.

## 7. Banco de dados

Tabelas principais:
- `usuarios`
  - autenticacao e perfil de acesso
- `alunos`
  - dados academicos e contato
- `chamadas`
  - presenca por aluno e data
- `tarefas`
  - recurso auxiliar legado

## 8. Testes e validacao executados

Validacoes tecnicas realizadas:
- compilacao Python:
  - `python -m py_compile server.py`
- validacao sintatica do JS:
  - `node -e "new Function(require('fs').readFileSync('static/app.js','utf8'));"`
- smoke test de integracao local cobrindo:
  - rotas estaticas
  - cadastro/login/logout
  - permissoes professor x aluno
  - chamada (leitura e bloqueio de escrita para aluno)
  - perfil do aluno (leitura e atualizacao)
  - turmas dinamicas

## 9. Roteiro rapido para apresentacao (5 min)

1. **Problema**
   - controle de chamada com perfis diferentes e seguranca de acesso.
2. **Arquitetura**
   - frontend simples + backend Python + SQLite.
3. **Demo professor**
   - login professor
   - cadastro de aluno
   - chamada com salvamento
   - edicao completa em `registro.html`
4. **Demo aluno**
   - login aluno
   - visualiza chamada da propria turma
   - nao consegue salvar chamada
   - em `registro.html` so edita contato permitido
5. **Fechamento**
   - turmas dinamicas, validacoes, regras de permissao e backend consistente.

## 10. Troubleshooting rapido

- Porta ocupada:
  - altere `PORT` em `server.py` ou encerre o processo que usa `8000`.
- Sessao invalida:
  - faca logout/login novamente.
- Sem ver alunos na chamada:
  - confirme se ha alunos cadastrados na mesma turma do usuario aluno.
- Email recusado:
  - use formato valido, ex: `usuario@dominio.com`.

---

Se precisar, eu tambem posso preparar um script de demonstracao com passos exatos (clicar/tela/fala) para voce apresentar sem improviso.
