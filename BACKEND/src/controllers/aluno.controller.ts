import { Request, Response } from 'express';
import { randomUUID } from 'node:crypto';

import { createAlunoData, findAlunoById, listAlunos } from '../data/aluno.data';

export function getAlunos(_request: Request, response: Response) {
  const alunos = listAlunos();

  response.status(200).json(alunos);
}

export function getAlunoById(request: Request, response: Response) {
  const rawId = request.params.id;
  const id = Array.isArray(rawId) ? rawId[0] : rawId;

  if (!id) {
    return response.status(400).json({
      mensagem: 'O id do aluno precisa ser informado.',
    });
  }

  const aluno = findAlunoById(id);

  if (!aluno) {
    return response.status(404).json({
      mensagem: 'Aluno nao encontrado.',
    });
  }

  return response.status(200).json(aluno);
}

export function createAluno(request: Request, response: Response) {
  const { nome, matricula } = request.body;

  // O controller faz a validacao basica antes de falar com a camada de dados.
  if (!nome || !matricula) {
    return response.status(400).json({
      mensagem: 'Os campos nome e matricula sao obrigatorios.',
    });
  }

  const alunoExistente = listAlunos().find(
    (aluno) => aluno.matricula === matricula,
  );

  if (alunoExistente) {
    return response.status(409).json({
      mensagem: 'Ja existe um aluno com essa matricula.',
    });
  }

  const novoAluno = createAlunoData({
    id: randomUUID(),
    nome,
    matricula,
  });

  return response.status(201).json(novoAluno);
}

// Proxima etapa do controller:
//
// export function updateAluno(request: Request, response: Response) {
//   1. pegar o id pela URL;
//   2. validar os dados novos no body;
//   3. chamar a camada data para atualizar;
//   4. retornar 404 se nao existir;
//   5. retornar o aluno atualizado.
// }
//
// export function deleteAluno(request: Request, response: Response) {
//   1. pegar o id pela URL;
//   2. verificar se o aluno existe;
//   3. chamar a camada data para remover;
//   4. retornar 204 em caso de sucesso.
// }
//
// Seguindo essa ideia, toda regra de requisicao HTTP continua centralizada aqui.
