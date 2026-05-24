# CompStat Rio AI API

Backend FastAPI do MVP CompStat Rio AI. Ele fornece os dados do dashboard, o motor de risco, o resumo executivo, o plano de ação e o chat operacional.

## Rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API local:

```text
http://localhost:8000
```

Documentação automática:

```text
http://localhost:8000/docs
```

## Testes

```bash
.venv/bin/pytest
```

## Endpoints

- `GET /health`
- `GET /area`
- `GET /summary`
- `GET /action-plan`
- `POST /chat`

Exemplo de chat:

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Onde a FM deve atuar hoje à noite?"}'
```

## Claude

Se `ANTHROPIC_API_KEY` estiver configurada no ambiente, o endpoint `/chat` chama Claude. Sem essa variável, retorna resposta mockada inteligente no formato obrigatório:

- Diagnóstico
- Evidências
- Recomendação operacional
- Órgãos responsáveis
