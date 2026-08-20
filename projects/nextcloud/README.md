# Nextcloud

Suíte self-hosted de armazenamento e colaboração — instalada para uso real e como
prática de Docker/Linux, enquanto o desenvolvimento do [FileHub](../filehub/) está
pausado.

## Arquitetura

```text
Browser (Tailscale)
      │ :8080
      ▼
┌───────────────┐   rede interna do Compose   ┌──────────────┐
│ app (Nextcloud) │ ────────── "db:3306" ─────► │ db (MariaDB)  │
│ volume: nc-data │                             │ volume: db-data│
└───────────────┘                             └──────────────┘
```

## Decisões

- **Docker Compose "clássico"** (não Nextcloud AIO) — propositalmente, para aprender
  Docker de verdade em vez de usar uma caixa preta que gerencia tudo sozinha.
- **MariaDB**, banco oficialmente recomendado pelo Nextcloud (mais testado que
  alternativas).
- **Admin provisionado via variável de ambiente** (`NEXTCLOUD_ADMIN_USER`/`_PASSWORD`)
  — evita o assistente manual de instalação, mantendo o deploy repetível.
- **Sem reverse proxy/HTTPS ainda** — acesso só via Tailscale/LAN, protegido pelas
  regras `DOCKER-USER` já configuradas no servidor (ver `docs/docker.md`).

## Como subir

No servidor (`~/srv-ubnt-lab/projects/nextcloud/`):

```bash
cp .env.example .env
# editar .env com senhas reais, salvar as mesmas no Bitwarden
sudo docker compose up -d
```

## Como acessar

`http://srv-ubnt-001:8080` (via Tailscale) ou `http://192.168.15.182:8080` (via LAN)

## Comandos úteis

```bash
sudo docker compose ps
sudo docker compose logs -f app
sudo docker compose down          # para os containers (dados persistem nos volumes)
sudo docker compose down -v       # também apaga os volumes — CUIDADO, apaga os dados
```

## Segurança

- `.env` nunca é commitado — senhas ficam só no servidor e no Bitwarden.
- Acesso restrito a Tailscale + LAN pelas regras `DOCKER-USER` (ver
  [docs/docker.md](../../docs/docker.md), seção 7).
- `NEXTCLOUD_TRUSTED_DOMAINS` precisa ser atualizado se o IP de LAN mudar (ele é
  dinâmico, via DHCP — ver [docs/rede.md](../../docs/rede.md)).
