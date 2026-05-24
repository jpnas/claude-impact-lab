# CompStat Rio AI

MVP funcional em Next.js para hackathon. O código principal está em [`compstat-rio-ai`](./compstat-rio-ai).

## Rodar

```bash
cd compstat-rio-ai-api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Em outro terminal:

```bash
cd compstat-rio-ai
pnpm install
pnpm dev
```

Acesse `http://localhost:3000` ou a porta informada pelo Next. Se a porta 3000 estiver ocupada, ele costuma subir em `http://localhost:3001`.

## Testar

```bash
cd compstat-rio-ai-api
.venv/bin/pytest
```

```bash
cd compstat-rio-ai
pnpm test
```

## Documentação

Veja a documentação completa do sistema, endpoints, variáveis de ambiente, testes para banca e pitch em [`compstat-rio-ai/README.md`](./compstat-rio-ai/README.md).
