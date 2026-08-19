"""Entidades SQLAlchemy — representam as tabelas do banco (User, Directory, File).

Carregam comportamento próprio quando fizer sentido (ex.: Directory.caminho_completo()),
não são só "sacos de dados". Não sabem nada sobre HTTP.
"""
