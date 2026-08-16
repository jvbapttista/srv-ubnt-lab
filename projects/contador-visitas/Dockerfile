# Imagem base: Python já pronto, versão "slim" = enxuta, sem pacotes desnecessários
FROM python:3.12-slim

# Diretório de trabalho dentro do container — tudo daqui pra frente roda a partir dele
WORKDIR /app

# Copia só o requirements.txt primeiro (não o código todo) — truque de cache do Docker:
# se o código mudar mas as dependências não, essa camada é reaproveitada, e o build
# fica bem mais rápido
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Agora sim copia o código da aplicação
COPY app.py .

# Documenta (não abre de verdade) que a aplicação escuta na porta 5000 dentro do container
EXPOSE 5000

# Comando executado quando o container inicia
CMD ["python", "app.py"]
