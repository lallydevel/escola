import { Router } from 'express';

import { alunoRouter } from './aluno.routes';

export const apiRouter = Router();

apiRouter.get('/', (_request, response) => {
  response.json({
    nome: 'API de chamada escolar',
    endpointsImplementados: [
      'GET /api/alunos',
      'GET /api/alunos/:id',
      'POST /api/alunos',
    ],
    endpointsPlanejados: [
      'PUT /api/alunos/:id',
      'DELETE /api/alunos/:id',
      'GET /api/chamadas',
      'POST /api/chamadas',
    ],
  });
});

// Metade pronta:
// tudo que esta em /alunos ja esta funcionando de verdade.
apiRouter.use('/alunos', alunoRouter);

// Proxima metade:
// quando o grupo for terminar a API, a ligacao das chamadas entra aqui.
//
// Exemplo do proximo passo:
// import { chamadaRouter } from './chamada.routes';
// apiRouter.use('/chamadas', chamadaRouter);
//
// A ideia e seguir a mesma estrutura usada em alunos:
// rota -> controller -> data.
