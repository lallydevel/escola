// Esta rota tambem ficou como guia para a segunda metade.
//
// Quando voces forem ativar:
// 1. importar Router do express;
// 2. importar as funcoes do chamada.controller.ts;
// 3. criar o chamadaRouter;
// 4. ligar GET / e POST /;
// 5. registrar o router em routes/index.ts.
//
// Exemplo:
//
// import { Router } from 'express';
// import { createChamada, getChamadas } from '../controllers/chamada.controller';
//
// export const chamadaRouter = Router();
// chamadaRouter.get('/', getChamadas);
// chamadaRouter.post('/', createChamada);
//
// A ligacao final ficaria em routes/index.ts com:
// apiRouter.use('/chamadas', chamadaRouter);
export {};
