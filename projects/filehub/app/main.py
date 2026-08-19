"""Ponto de entrada da aplicação FileHub.

Roda em desenvolvimento com:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

app = FastAPI(
    title="FileHub",
    description="Plataforma pessoal de armazenamento e gerenciamento de arquivos.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Confirma que a aplicação está no ar. Endpoint de infraestrutura — sem
    estado, sem lógica de negócio, por isso não é um método de classe."""
    return {"status": "ok"}
