# `app/main.py` explicado — Ponto de entrada do FileHub

Código-fonte: [`projects/filehub/app/main.py`](../../../projects/filehub/app/main.py)

---

## Bloco 1 — docstring do módulo

```python
"""Ponto de entrada da aplicação FileHub.

Roda em desenvolvimento com:
    uvicorn app.main:app --reload
"""
```

Documentação do próprio arquivo — explica pra que ele serve e como executá-lo. O
comando `uvicorn app.main:app --reload` decifrado:

- `app.main` — o módulo Python `app/main.py` (o `.` navega pacotes, igual `import`).
- `:app` — o nome da **variável** dentro desse módulo que contém a aplicação FastAPI
  (definida no Bloco 2). O Uvicorn precisa saber exatamente qual objeto executar.
- `--reload` — reinicia o servidor sozinho a cada alteração salva no código. Só usar em
  desenvolvimento — nunca em produção (custa performance).

---

## Bloco 2 — criando a aplicação

```python
from fastapi import FastAPI

app = FastAPI(
    title="FileHub",
    description="Plataforma pessoal de armazenamento e gerenciamento de arquivos.",
    version="0.1.0",
)
```

`FastAPI()` cria a aplicação — um objeto que vai acumular todas as rotas que
registrarmos. `title`, `description` e `version` não afetam o funcionamento; são só
metadados usados para gerar a documentação automática em `/docs`.

---

## Bloco 3 — a rota `/health`

```python
@app.get("/health")
def health_check() -> dict[str, str]:
    """Confirma que a aplicação está no ar. Endpoint de infraestrutura — sem
    estado, sem lógica de negócio, por isso não é um método de classe."""
    return {"status": "ok"}
```

- `@app.get("/health")` — decorador que registra `health_check` como a função
  chamada quando alguém faz uma requisição `GET` para `/health`.
- `-> dict[str, str]` — type hint: retorna um dicionário com chaves e valores texto.
  O FastAPI usa isso para gerar automaticamente o schema desse endpoint no `/docs`.
- **Por que uma função solta, e não um método de classe:** este endpoint não tem
  estado nenhum (não guarda nada entre chamadas) nem lógica de negócio — só confirma
  que o processo está rodando. Criar uma classe só pra isso seria abstração sem
  propósito. POO entra quando há **estado e comportamento relacionados** para
  encapsular — o que vamos ver a partir da modelagem de `User`/`Directory`/`File`
  (Fase 4).
- O FastAPI converte automaticamente o `dict` retornado em uma resposta JSON.

---

## Testado em (2026-08-18)

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001
curl http://127.0.0.1:8001/health
→ {"status":"ok"}
```

Confirmado também: `/docs` (Swagger UI, gerado automaticamente pelo FastAPI a partir
do próprio código, sem nenhuma linha extra) respondendo `200`.

---

## Histórico

| Data | Mudança |
|---|---|
| 2026-08-18 | Versão inicial — aplicação FastAPI mínima com endpoint `/health` |
