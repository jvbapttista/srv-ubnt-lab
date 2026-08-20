# `docker-compose.yml` explicado — Nextcloud

Código-fonte: [`projects/nextcloud/docker-compose.yml`](../../projects/nextcloud/docker-compose.yml)

---

## Serviço `db`

```yaml
db:
  image: mariadb:11
  restart: unless-stopped
  command: --transaction-isolation=READ-COMMITTED --binlog-format=ROW
  volumes:
    - db-data:/var/lib/mysql
  environment:
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    MYSQL_DATABASE: nextcloud
    MYSQL_USER: nextcloud
    MYSQL_PASSWORD: ${MYSQL_PASSWORD}
```

- `image: mariadb:11` — usa a imagem oficial do MariaDB pronta, não construímos nada
  aqui (diferente de projetos anteriores onde tínhamos um `Dockerfile` próprio).
- `restart: unless-stopped` — se o container cair (ou o servidor reiniciar), o Docker
  sobe ele de novo sozinho, a menos que alguém tenha parado manualmente.
- `command: ...` — sobrescreve o comando padrão de inicialização do MariaDB, passando
  flags recomendadas oficialmente pela documentação do Nextcloud (melhoram
  compatibilidade e integridade transacional).
- `volumes: - db-data:/var/lib/mysql` — `/var/lib/mysql` é onde o MariaDB guarda os
  dados de verdade *dentro* do container. Sem um volume, esses dados sumiriam toda vez
  que o container fosse recriado. `db-data` é um **volume nomeado** (declarado no fim
  do arquivo), gerenciado pelo próprio Docker — fica em disco, fora do container.
- `environment: ...` — variáveis de ambiente lidas pela imagem oficial do MariaDB na
  primeira inicialização, para criar o banco e o usuário automaticamente.
- `${MYSQL_ROOT_PASSWORD}` — sintaxe de **substituição de variável**: o Compose lê esse
  valor de um arquivo `.env` na mesma pasta (nunca commitado — ver `.env.example`).

## Serviço `app`

```yaml
app:
  image: nextcloud:apache
  restart: unless-stopped
  depends_on:
    - db
  ports:
    - "8080:80"
  volumes:
    - nc-data:/var/www/html
  environment:
    MYSQL_HOST: db
    ...
    NEXTCLOUD_ADMIN_USER: ${NEXTCLOUD_ADMIN_USER}
    NEXTCLOUD_ADMIN_PASSWORD: ${NEXTCLOUD_ADMIN_PASSWORD}
    NEXTCLOUD_TRUSTED_DOMAINS: srv-ubnt-001 100.96.168.97 192.168.15.182
```

- `image: nextcloud:apache` — variante da imagem oficial que já inclui o Apache como
  servidor web embutido (não precisamos de um serviço separado pra isso).
- `depends_on: - db` — o Compose sobe o `db` antes do `app`. Garante só a **ordem de
  início**, não que o MariaDB já esteja pronto pra aceitar conexão — a própria imagem
  do Nextcloud já lida com isso internamente, tentando reconectar.
- `ports: "8080:80"` — mapeia a porta 8080 do servidor para a porta 80 *dentro* do
  container (onde o Apache do Nextcloud escuta). Acessamos via `:8080` de fora.
- `MYSQL_HOST: db` — aqui está a rede interna do Compose em ação: `db` é o **nome do
  serviço** definido acima, não um IP. O Compose resolve isso sozinho.
- `NEXTCLOUD_ADMIN_USER`/`_PASSWORD` — provisiona o usuário administrador
  automaticamente na primeira subida, evitando o assistente de instalação manual pelo
  navegador — o deploy fica inteiramente descrito neste arquivo, repetível.
- `NEXTCLOUD_TRUSTED_DOMAINS` — o Nextcloud recusa por padrão requisições que chegam
  com um cabeçalho `Host` diferente do que ele espera (proteção contra ataques de
  *Host header injection*). Como acessamos por hostname Tailscale e por IP de LAN, não
  por um domínio público, precisamos listar essas origens explicitamente.

## Volumes nomeados

```yaml
volumes:
  db-data:
  nc-data:
```

Declaração dos dois volumes usados acima. Sem conteúdo/configuração extra — deixamos o
Docker gerenciar onde eles ficam fisicamente em disco (dentro de `/var/lib/docker/volumes/`).

---

## Histórico

| Data | Mudança |
|---|---|
| 2026-08-19 | Versão inicial — `db` (MariaDB) + `app` (Nextcloud) |
