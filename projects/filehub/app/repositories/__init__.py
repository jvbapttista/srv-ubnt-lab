"""Únicos módulos que sabem "falar SQLAlchemy" diretamente com o banco.

Centralizam consultas (ex.: FileRepository.buscar_por_pasta(...)). Permitem testar
app/services com um repositório falso, sem precisar de PostgreSQL de verdade.
"""
