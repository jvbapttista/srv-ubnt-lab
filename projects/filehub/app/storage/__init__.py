"""Interface FileStorage (Protocol) + implementações concretas.

Hoje só existe LocalFileStorage (disco local). A interface existe para permitir trocar
por S3/OCI Object Storage no futuro, sem tocar em app/services.
"""
