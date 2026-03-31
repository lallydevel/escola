import { Aluno } from '../types/aluno';

// Esta camada simula um banco de dados em memoria.
// Para trabalho escolar funciona bem, porque deixa a API rodando
// sem precisar configurar banco agora.
const alunos: Aluno[] = [
  {
    id: 'a1',
    nome: 'Ana Souza',
    matricula: '2026001',
  },
  {
    id: 'a2',
    nome: 'Bruno Lima',
    matricula: '2026002',
  },
  {
    id: 'a3',
    nome: 'Carla Mendes',
    matricula: '2026003',
  },
];

export function listAlunos() {
  return alunos;
}

export function findAlunoById(id: string) {
  return alunos.find((aluno) => aluno.id === id);
}

export function createAlunoData(aluno: Aluno) {
  alunos.push(aluno);
  return aluno;
}

// Continuacao planejada desta camada:
//
// export function updateAlunoData(id: string, dadosAtualizados: Partial<Aluno>) {
//   localizar o indice do aluno;
//   atualizar nome e/ou matricula;
//   devolver o aluno atualizado;
// }
//
// export function deleteAlunoData(id: string) {
//   remover o aluno pelo indice;
//   devolver true ou false para o controller saber se encontrou ou nao.
// }
