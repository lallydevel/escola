import { Router } from 'express';

import {
  createAluno,
  getAlunoById,
  getAlunos,
} from '../controllers/aluno.controller';

export const alunoRouter = Router();

// A rota recebe a URL e encaminha para o controller certo.
// Quem decide a regra de negocio nao e a rota, e sim o controller.
alunoRouter.get('/', getAlunos);
alunoRouter.get('/:id', getAlunoById);
alunoRouter.post('/', createAluno);

// Proximos endpoints desta mesma entidade.
// Deixei comentado porque o pedido foi entregar metade pronta
// e a outra metade apenas orientada no codigo.
//
// alunoRouter.put('/:id', updateAluno);
// alunoRouter.delete('/:id', deleteAluno);
//
// Para isso funcionar depois, voces vao precisar:
// 1. criar as funcoes updateAluno e deleteAluno no controller;
// 2. criar as funcoes updateAlunoData e deleteAlunoData na camada data;
// 3. validar se o aluno existe antes de alterar ou remover.
