// Este controller ficou como mapa da implementacao futura.
// A ideia e repetir o mesmo fluxo dos alunos:
// rota chama controller, controller valida, depois chama data.
//
// Exemplo de funcoes para a proxima etapa:
//
// export function getChamadas(_request: Request, response: Response) {
//   const chamadas = listChamadasPlanejado();
//   response.status(200).json(chamadas);
// }
//
// export function createChamada(request: Request, response: Response) {
//   const { alunoId, data, presente } = request.body;
//
//   1. validar se os campos vieram;
//   2. validar se o alunoId existe em aluno.data.ts;
//   3. montar o novo registro;
//   4. salvar na camada data;
//   5. responder com 201.
// }
//
// Esse arquivo ficou sem implementacao ativa para manter o combinado:
// metade pronta e metade comentada.
export {};
