import cors from 'cors';
import express from 'express';

import { apiRouter } from './routes';

export const app = express();

// Middleware global:
// 1. cors libera o acesso do frontend quando ele for conectar na API.
// 2. express.json permite receber JSON no body das requisicoes.
app.use(cors());
app.use(express.json());

app.get('/', (_request, response) => {
  response.json({
    projeto: 'Sistema de chamada escolar',
    status: 'API online',
    observacao:
      'Metade da API foi implementada e a outra metade esta guiada por comentarios no codigo.',
  });
});

// Aqui o app principal conecta todas as rotas da API.
// Fluxo da ligacao:
// server.ts -> app.ts -> routes -> controllers -> data
app.use('/api', apiRouter);
