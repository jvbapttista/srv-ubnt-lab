import time

import redis
from flask import Flask

app = Flask(__name__)

# "redis" é o nome do serviço definido no docker-compose.yml — o Compose cria uma
# rede interna onde cada serviço enxerga os outros pelo próprio nome, sem precisar
# saber IP nenhum.
cache = redis.Redis(host="redis", port=6379, decode_responses=True)


def get_hit_count():
    """Incrementa o contador no Redis, com retentativas — útil porque o container
    da aplicação pode subir um pouco antes do Redis estar pronto para aceitar
    conexões."""
    retries = 5
    while True:
        try:
            return cache.incr("hits")
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)


@app.route("/")
def hello():
    count = get_hit_count()
    return f"Olá! Esta página foi visitada {count} vezes.\n"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
