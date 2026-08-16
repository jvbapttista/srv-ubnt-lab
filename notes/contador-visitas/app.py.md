# `app.py` explicado — Contador de Visitas

Código-fonte: [`projects/contador-visitas/app.py`](../../projects/contador-visitas/app.py)

Aplicação Flask que conta visitas, guardando o número num banco Redis separado.
Escrita em **POO** (Programação Orientada a Objetos) — a pedido explícito do autor,
como prática para uso no trabalho.

---

## Bloco 1 — imports

```python
import time
import redis
from flask import Flask
```

Trazendo as bibliotecas que o arquivo usa:

- `time` — biblioteca padrão do Python, usada aqui só para pausar a execução (`sleep`).
- `redis` — cliente Python para conversar com o banco Redis.
- `Flask` — o framework web.

---

## Bloco 2 — definição da classe

```python
class ContadorVisitas:
    """Encapsula a conexão com o Redis e a lógica de incrementar o contador de
    visitas, incluindo retentativa caso o Redis ainda não esteja pronto para
    aceitar conexões quando a aplicação subir."""
```

`class NomeDaClasse:` define uma classe — uma "planta baixa" para criar objetos. A
string entre `"""` logo abaixo é a **docstring**: documentação da classe, acessível em
tempo de execução (`ContadorVisitas.__doc__`) e lida por IDEs/ferramentas de doc. Boa
prática documentar toda classe e método público.

---

## Bloco 3 — o construtor `__init__`

```python
def __init__(self, host="redis", port=6379, chave="hits", max_tentativas=5):
    self._cache = redis.Redis(host=host, port=port, decode_responses=True)
    self._chave = chave
    self._max_tentativas = max_tentativas
```

- `__init__` é um **método especial** ("dunder", de *double underscore*) — o Python
  chama ele automaticamente sempre que um objeto dessa classe é criado
  (`ContadorVisitas()`). É o "construtor".
- `self` é **sempre o primeiro parâmetro** de um método de instância — representa "o
  próprio objeto". O Python injeta ele sozinho quando você chama `objeto.metodo()`; em
  outras linguagens, equivale ao `this`.
- `host="redis", port=6379, chave="hits", max_tentativas=5` são **parâmetros com valor
  padrão** — `ContadorVisitas()` sem argumentos usa esses valores, mas
  `ContadorVisitas(host="outro-servidor")` sobrescreveria só o `host`.
- `self._cache = redis.Redis(...)` cria um **atributo de instância**: cada objeto
  `ContadorVisitas` guarda seu próprio `_cache`. É assim que POO guarda **estado** —
  diferente de uma função solta, que esquece tudo assim que termina, o objeto carrega
  dados consigo enquanto existir.
- O `_` no início de `_cache`, `_chave`, `_max_tentativas` é **convenção** Python para
  "isso é interno da classe, não mexa direto de fora" — não é uma trava real (Python
  não tem `private` de verdade), é um sinal para quem lê o código.

**Nota — nome do host `"redis"`:** não é um IP, é o **nome do serviço** definido em
`docker-compose.yml`. A rede interna criada pelo Compose resolve esse nome
automaticamente para o container certo.

---

## Bloco 4 — o método `incrementar`

```python
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
```

- Método de instância (de novo, `self` como primeiro parâmetro) — usa
  `self._cache` e `self._chave`, guardados no `__init__`.
- `-> int` é uma **type hint**: documenta que o método retorna um inteiro. O Python não
  obriga isso em tempo de execução (diferente de Java/C#), mas ajuda quem lê o código
  e ferramentas como `mypy` a detectar erros.
- `tentativas_restantes = self._max_tentativas` — variável **local** ao método (sem
  `self.`, não sobrevive depois que o método termina).
- `while True:` — loop infinito, só sai por `return` ou `raise`.
- `try / except redis.exceptions.ConnectionError:` — tenta incrementar o contador no
  Redis; se ele ainda não estiver pronto pra aceitar conexão (comum logo que os
  containers sobem juntos), cai no `except`.
- Dentro do `except`: se já esgotou as tentativas (`tentativas_restantes == 0`),
  `raise` propaga o erro (desiste de vez). Senão, decrementa o contador de tentativas
  e espera meio segundo antes do `while` tentar de novo.

---

## Bloco 5 — instanciando a aplicação e a classe

```python
app = Flask(__name__)
contador = ContadorVisitas()
```

Aqui a classe vira **objeto de verdade**: `ContadorVisitas()` chama o `__init__` do
Bloco 3, criando um objeto guardado em `contador`. Criado **uma vez só**, quando o
processo Python sobe — reaproveitado em toda requisição seguinte (por isso "lembra" a
conexão com o Redis, sem precisar reconectar a cada acesso).

---

## Bloco 6 — a rota do Flask

```python
@app.route("/")
def hello():
    total = contador.incrementar()
    return f"Olá! Esta página foi visitada {total} vezes.\n"
```

- `@app.route("/")` é um **decorador** — "envolve" a função abaixo com comportamento
  extra. Aqui, registra `hello()` como a função que responde a acessos na rota raiz
  (`/`).
- **As rotas continuam sendo funções decoradas** — é a convenção do próprio Flask, não
  muda com POO. O que encapsulamos em classe foi a **lógica de negócio** (conexão e
  incremento no Redis), não o roteamento HTTP em si.
- `contador.incrementar()` — chamada de método no objeto criado no Bloco 5. A rota não
  sabe nada sobre Redis, retentativa, etc. — só pede "incrementa e devolve o total".
  Essa é a vantagem prática de POO aqui: a complexidade fica escondida dentro do objeto.
- `f"...{total}..."` é uma **f-string**, forma moderna de interpolar variáveis dentro
  de uma string.

---

## Bloco 7 — ponto de entrada

```python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
```

Padrão comum em Python: esse bloco só roda se o arquivo for executado **diretamente**
(`python app.py`), não se for importado por outro arquivo.

`host="0.0.0.0"` significa "escute em todas as interfaces de rede **dentro do
container**" — importante porque `127.0.0.1` só aceitaria conexão de dentro do próprio
container, e o Compose precisa alcançar essa porta de fora (via o mapeamento
`8000:5000` do `docker-compose.yml`).

---

## Histórico

| Data | Mudança |
|---|---|
| 2026-08-16 | Versão inicial, estilo funcional (funções soltas, sem classe) |
| 2026-08-16 | Reescrito em POO (`ContadorVisitas`), a pedido do autor — este documento passou a refletir a versão em POO |
