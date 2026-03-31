import { app } from './app';

const PORT = 3333;

// Este arquivo so tem uma responsabilidade:
// iniciar o servidor e apontar para o app principal.
app.listen(PORT, () => {
  console.log(`API rodando em http://localhost:${PORT}`);
});
