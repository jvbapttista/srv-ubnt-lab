# Notes — código explicado, bloco por bloco

Esta pasta é diferente de `docs/` (que documenta a **infraestrutura**: servidor, rede,
SSH, Docker) e de `projects/` (que tem o **código em si**, funcional).

Aqui fica a explicação **didática** de cada código que escrevemos no laboratório —
bloco por bloco, o que cada parte faz e por quê. É material de estudo, pensado para eu
mesmo consultar quando tiver dúvida sobre um trecho específico, sem precisar reler o
código todo ou lembrar da explicação original.

## Convenção

Uma subpasta por projeto, espelhando o nome em `projects/`:

```text
notes/
└── <nome-do-projeto>/
    ├── app.py.md              explicação do app.py, bloco por bloco
    ├── docker-compose.yml.md  explicação do compose, se relevante
    └── Dockerfile.md          explicação do Dockerfile, se relevante
```

Cada arquivo de explicação carrega o nome do arquivo de código original + `.md`.

## Regra de manutenção

**Sempre que o código evoluir, a explicação correspondente é atualizada junto** — não é
um retrato de um momento único, é para refletir o estado atual do código. Se um bloco
for removido ou mudar de comportamento, a nota é ajustada na mesma hora, não depois.

## Índice

| Projeto | Arquivos explicados |
|---|---|
| [filehub](filehub/) | [app/main.py.md](filehub/app/main.py.md) |
| [nextcloud](nextcloud/) | [docker-compose.yml.md](nextcloud/docker-compose.yml.md) |
