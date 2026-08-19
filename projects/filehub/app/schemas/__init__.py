"""Modelos Pydantic — validam o que entra e sai pela API (DTOs).

Diferente de app/models (que é persistência), aqui é o "formato de dados" que a API
aceita e devolve. Um schema pode expor só parte de um model (ex.: nunca devolver o
hash da senha).
"""
