"""Rotas FastAPI — a única camada que conhece HTTP (Request, Response, status codes).

Recebe a requisição, valida com app/schemas, chama app/services, devolve a resposta.
Nunca fala com o banco nem com o storage diretamente.
"""
