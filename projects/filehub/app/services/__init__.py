"""Regras de negócio — orquestram repositories e storage.

Ex.: "salvar um arquivo" = FileService grava o conteúdo via app/storage E registra o
metadado via FileRepository, como uma operação lógica única. Não sabe nada sobre HTTP
(não conhece Request/Response do FastAPI).
"""
