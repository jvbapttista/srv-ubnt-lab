import time

import redis
from flask import Flask


class ContadorVisitas:
    """Encapsula a conexão com o Redis e a lógica de incrementar o contador de
    visitas, incluindo retentativa caso o Redis ainda não esteja pronto para
    aceitar conexões quando a aplicação subir."""

    def __init__(self, host="redis", port=6379, chave="hits", max_tentativas=5):
        # "redis" é o nome do serviço definido no docker-compose.yml — a rede
        # interna do Compose resolve isso pelo nome, sem precisar de IP.
        self._cache = redis.Redis(host=host, port=port, decode_responses=True)
        self._chave = chave
        self._max_tentativas = max_tentativas

    def incrementar(self) -> int:
        """Incrementa e retorna o valor atual do contador."""
        tentativas_restantes = self._max_tentativas
        while True:
            try:
                return self._cache.incr(self._chave)
            except redis.exceptions.ConnectionError:
                if tentativas_restantes == 0:
                    raise
                tentativas_restantes -= 1
                time.sleep(0.5)


app = Flask(__name__)
# Uma instância única, criada quando a aplicação sobe — guarda o estado da
# conexão com o Redis, reaproveitada em toda requisição.
contador = ContadorVisitas()


@app.route("/")
def hello():
    # As rotas continuam sendo funções decoradas — isso é a convenção do
    # próprio Flask, não muda com POO. O que encapsulamos em classe foi a
    # lógica de negócio (a conexão e o incremento no Redis), não o roteamento.
    total = contador.incrementar()
    return f"Olá! Esta página foi visitada {total} vezes.\n"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
