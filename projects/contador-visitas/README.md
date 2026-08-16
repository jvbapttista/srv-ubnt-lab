# Contador de Visitas — Flask + Redis + Docker Compose

Primeiro projeto multi-container do laboratório. Uma aplicação web mínima que conta
quantas vezes foi acessada, com o contador persistido num banco Redis separado.

## Contexto

Este projeto foi criado como prática inicial de **Docker Compose**, no laboratório
DevOps documentado em [`/docs`](../../docs). O objetivo não é a aplicação em si (é
propositalmente simples), mas demonstrar, de forma real e executável, os conceitos
fundamentais de orquestração de múltiplos containers:

- Construção de imagem própria via `Dockerfile`
- Comunicação entre serviços pela rede interna do Compose (por nome, não por IP)
- Persistência de dados com volume nomeado
- Ordem de inicialização entre serviços (`depends_on`)

## Arquitetura

```text
Cliente (navegador)
      │
      │ :8000
      ▼
┌─────────────┐        rede interna do Compose        ┌─────────────┐
│  web (Flask) │ ──────────── "redis:6379" ──────────► │ redis:7-alpine│
│  porta 5000  │ ◄───────────────────────────────────  │  volume: data │
└─────────────┘                                        └─────────────┘
```

## Estrutura

```text
contador-visitas/
├── app.py               aplicação Flask
├── requirements.txt     dependências Python
├── Dockerfile            receita de build da imagem "web"
├── docker-compose.yml    orquestração dos dois serviços
└── README.md             este arquivo
```

## Como rodar

```bash
docker compose up -d --build
```

Acesse: `http://<IP-do-servidor>:8000`

A cada acesso, o contador incrementa:

```text
Olá! Esta página foi visitada 1 vezes.
Olá! Esta página foi visitada 2 vezes.
```

## Comandos úteis

```bash
docker compose ps          # ver os dois serviços rodando
docker compose logs -f web  # acompanhar logs da aplicação
docker compose down        # parar e remover os containers (o volume do Redis persiste)
docker compose down -v     # parar tudo E apagar o volume (reseta o contador)
```

## Decisões técnicas

- **Lógica de negócio em POO** (`ContadorVisitas`, em `app.py`) — a conexão com o Redis
  e o incremento do contador ficam encapsulados numa classe, separados da camada de
  rotas do Flask (que continua sendo funções decoradas, convenção do próprio framework).
  Facilita testar a lógica isolada e reaproveitar a classe em outro contexto.
- **Redis com volume nomeado**, não bind mount — deixa o Docker gerenciar onde os
  dados ficam fisicamente, mais simples para este caso de uso.
- **`depends_on` sem healthcheck** — o Compose só garante que o Redis foi *iniciado*,
  não que já está pronto para aceitar conexões. Por isso a aplicação implementa
  retentativa (`get_hit_count()` em `app.py`), um padrão comum em sistemas distribuídos.
- **Porta 8000 no host, 5000 no container** — evita conflito com outras aplicações
  que porventura usem a 5000 diretamente no host.

## Dependências

- Docker Engine + Compose plugin instalados no host (ver [docs/docker.md](../../docs/docker.md))

---
Documentado em: 2026-08-16
