import { Chamada } from '../types/chamada';

// Este arquivo representa a segunda metade da API.
// Ainda nao foi ligado nas rotas de proposito, porque o pedido
// foi deixar so metade pronta e a outra metade explicada.
//
// Quando forem continuar, este arquivo pode guardar os registros
// de chamada do mesmo jeito que aluno.data.ts guarda os alunos.
const chamadas: Chamada[] = [];

export function listChamadasPlanejado() {
  return chamadas;
}

// Proximos passos aqui:
//
// export function createChamadaData(chamada: Chamada) {
//   chamadas.push(chamada);
//   return chamada;
// }
//
// export function listChamadasByData(data: string) {
//   return chamadas.filter((chamada) => chamada.data === data);
// }
//
// Observacao importante:
// alunoId precisa bater com um id existente em aluno.data.ts,
// senao a chamada pode ficar apontando para um aluno que nao existe.
