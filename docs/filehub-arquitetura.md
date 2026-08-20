# FileHub — Arquitetura (Fase 0)

Documento vivo — evolui conforme discutirmos e revisarmos decisões.

**Status: arquitetura aprovada em 2026-08-18, implementação PAUSADA (não cancelada)**
na mesma data — o autor decidiu priorizar aprender Docker/Linux na prática, rodando
aplicações self-hosted já existentes (Nextcloud, CasaOS, etc.), antes de continuar o
desenvolvimento próprio. Este documento continua válido para quando o projeto for
retomado. Ver [docs/filehub-progresso.md](filehub-progresso.md) para detalhes.

Última atualização: 2026-08-18

---

## 1. Visão geral e problema

Plataforma pessoal de armazenamento de arquivos (conceitualmente parecida com
Nextcloud/Drive/Dropbox, mas sem tentar competir com eles), acessível via navegador,
hospedada no homelab, usável no dia a dia real do usuário e ao mesmo tempo peça de
portfólio.

## 2. Objetivo e usuários

Três objetivos simultâneos: ferramenta útil, aprendizado prático, portfólio forte.

**Usuários:** um único usuário (o próprio dono do laboratório) no MVP. Multiusuário,
grupos e permissões são explicitamente **fase futura** — modelar a tabela `users` desde
já de forma que suporte múltiplos usuários no futuro, mas **sem** construir a
complexidade de permissões/grupos agora. Isso evita dois erros opostos: construir só
para um usuário (impossível de estender depois) ou construir multiusuário completo
agora (overengineering para quem vai usar sozinho por muito tempo).

## 3. MVP — escopo travado

Login (usuário único) → dashboard → listar/navegar pastas → criar pasta → upload →
download → renomear → excluir.

Fora do MVP, propositalmente: busca, tags, lixeira, compartilhamento, permissões,
processamento assíncrono, observabilidade, Kubernetes, OCI. Todos ficam no roadmap
(seção 15), não no MVP.

---

## 4. Arquitetura geral — avaliação crítica

Sua proposta:

```text
Browser → Reverse Proxy → FileHub API → [PostgreSQL, File Storage]
```

Concordo com a espinha dorsal, mas com um ajuste importante: você descreveu "FileHub
API" — porém você também quer uma **interface web de verdade**, não só Swagger. Isso
levanta uma decisão que precisa ser resolvida antes de tudo: **o FileHub é uma API pura
consumida por um frontend separado, ou uma aplicação web única que serve HTML e lógica
juntos?** Ver seção 8.

**Reverse proxy: adiado, não removido.** Enquanto o acesso for só via Tailscale
(mesmo padrão que já usamos no projeto anterior), publicar a porta direto no
`docker-compose.yml` é suficiente — as regras `DOCKER-USER` que já configuramos no
servidor (Tailscale + LAN liberados, resto bloqueado) continuam protegendo isso. Reverse
proxy entra quando quisermos: (a) HTTPS de verdade, (b) um endereço amigável
(`files.<domínio>`), ou (c) rodar mais de um serviço atrás da mesma porta 443. Nenhum
desses três é verdade ainda no MVP.

---

## 5. Decisão: Frontend

**Proposta: templates server-side (Jinja2, renderizado pelo próprio FastAPI) + HTML
simples + JavaScript mínimo (ou `htmx`), não React/Vue.**

**Por quê, não só "porque é mais simples":**

- Seu objetivo declarado é portfólio de **Python/DevOps/Cloud**, não frontend. Um SPA
  (React/Vue) adiciona uma segunda stack inteira (Node, bundler, build step, gerência de
  estado no cliente) que não serve a esse objetivo — é complexidade que não resolve
  problema real seu, exatamente o que você pediu para eu evitar.
- Templates server-side deixam **uma aplicação, um container**, mais fácil de ensinar
  Docker/Compose sem confundir com "preciso buildar o frontend separado".
- `htmx` (biblioteca pequena, sem build step) cobre 90% do que dá "sensação de app
  moderna" (upload sem recarregar a página, confirmação de exclusão) sem precisar de
  SPA. Se um dia você precisar de algo bem mais rico (preview de arquivo, drag-and-drop
  complexo com progress bar), aí sim reavaliamos — com necessidade real na mão, não
  antecipada.

**Trade-off honesto:** essa decisão custa "menos vitrine de frontend moderno" no
portfólio. Se seu objetivo incluísse também mostrar domínio de React, eu mudaria a
recomendação. Mas você foi claro que o foco é Python/DevOps/Cloud.

## 6. Decisão: Storage de arquivos

Concordo com separar metadados (PostgreSQL) de arquivos reais (filesystem). Um ajuste
importante na sua proposta original:

**Você sugeriu um layout tipo `/storage/documentos`, `/storage/estudos`.** Isso mistura
duas coisas que devem ficar separadas: a **estrutura lógica de pastas** (o que o usuário
vê e nomeia, guardado inteiramente no banco) e o **layout físico em disco** (onde o
arquivo realmente fica salvo). Se o disco espelhar os nomes de pastas 1:1, renomear ou
mover uma pasta no app exigiria mover arquivos de verdade no disco — lento, arriscado, e
abre brecha para bugs de *path traversal* se o nome da pasta vier direto do usuário.

**Proposta:** cada arquivo físico é salvo com um caminho **opaco**, baseado no ID gerado
pelo banco (ex.: `/data/storage/<file_id>`), nunca no nome escolhido pelo usuário. Toda
a lógica de "qual pasta, qual nome, qual hierarquia" vive só no PostgreSQL (tabela
`directories` com auto-referência `parent_id`). Renomear/mover no app vira só um
`UPDATE` no banco — nunca toca o disco.

**Abstração de storage:** vale criar uma interface pequena agora (não implementar duas
vezes, só a interface + uma implementação):

```python
class FileStorage(Protocol):
    def save(self, file_id: str, content: bytes) -> None: ...
    def read(self, file_id: str) -> bytes: ...
    def delete(self, file_id: str) -> None: ...
```

Com uma única implementação, `LocalFileStorage` (escreve num diretório montado via
volume Docker). Isso custa pouco agora e paga muito depois — é exatamente o que você
pediu na seção 5 do seu documento original ("permitir trocar por S3/OCI depois, sem
implementar agora"). É um uso justificado de abstração, não POO por decoração.

---

## 7. Arquitetura de backend (camadas)

**Não vou propor a estrutura completa `domain/application/infrastructure/api` agora.**
Ela é excelente para sistemas complexos, mas para 3 entidades (`User`, `Directory`,
`File`) seria a abstração chegando antes do problema que ela resolve — o oposto do que
você pediu.

**Proposta para o MVP**, mais simples, mas já com separação de responsabilidades real:

```text
app/
├── main.py           ponto de entrada, monta a aplicação FastAPI
├── core/             configuração, segurança/hash de senha, sessão
├── models/           entidades SQLAlchemy (persistência)
├── schemas/           modelos Pydantic (validação de entrada/saída da API)
├── repositories/      acesso a dados — únicos que sabem falar SQLAlchemy
├── services/          regras de negócio — usam repositories e o FileStorage
├── storage/           interface FileStorage + LocalFileStorage
├── api/               rotas FastAPI — só HTTP, chamam services
└── templates/         HTML Jinja2
```

**Regra de dependência:** `api` depende de `services`; `services` depende de
`repositories` e `storage`; `repositories` depende de `models`. Nunca ao contrário —
uma rota não fala com o banco diretamente, e um `service` não sabe o que é uma
requisição HTTP. Isso é o que torna a lógica de negócio testável sem precisar subir um
servidor web.

**Caminho de evolução:** se/quando a complexidade justificar (ex.: regras de
permissão/compartilhamento ficarem elaboradas), migramos para o layout
`domain/application/infrastructure` completo. Registro isso como decisão adiada, não
esquecida — ver roadmap.

---

## 8. POO — o que vira classe, e por quê

| Elemento | Vira classe? | Justificativa |
|---|---|---|
| `User`, `Directory`, `File` | Sim — modelos SQLAlchemy **com comportamento próprio** (ex.: `Directory.caminho_completo()`, `User.verificar_senha()`) | Evita "modelo anêmico" (classe só com campos, sem comportamento) — dados e comportamento relacionados ficam juntos |
| `FileRepository`, `DirectoryRepository`, `UserRepository` | Sim | Centraliza acesso a dados; permite testar `services` com um repositório falso, sem precisar de Postgres de verdade |
| `FileService` (usa um `FileStorage` por **composição**, não herança) | Sim | Orquestra a regra de negócio "salvar arquivo" = grava no storage + registra metadado no banco, como uma transação lógica |
| `FileStorage` (interface/Protocol) + `LocalFileStorage` | Sim | Única abstração que temos hoje: permite trocar a implementação (S3, OCI) sem tocar o resto do código |
| Herança entre `File`/`Directory`/`User` | **Não** | Não existe relação "é um" genuína entre eles hoje — forçar herança aqui seria POO por decoração, exatamente o que você pediu para evitar |
| Value Objects (ex.: `Checksum`, `FileSize`) | **Adiado** | Só valem a pena quando a validação em torno deles crescer; por enquanto são campos simples |

**Dependency Injection:** o próprio `Depends()` do FastAPI já é DI de verdade — vamos
usá-lo para injetar sessão do banco, usuário autenticado e services nas rotas, sem
precisar de nenhuma biblioteca extra.

---

## 9. Banco de dados (MVP)

```text
users
  id, email, senha_hash, criado_em

directories
  id, nome, parent_id (auto-FK, nulo = raiz), owner_id (FK users), criado_em

files
  id, nome, directory_id (FK), owner_id (FK users), tamanho_bytes, mime_type,
  storage_path (opaco, = id físico), checksum (nulo por enquanto), criado_em, atualizado_em
```

- **Constraint:** `UNIQUE(nome, parent_id, owner_id)` em `directories` e `files` —
  evita duas pastas/arquivos com o mesmo nome no mesmo lugar, regra real de qualquer
  sistema de arquivos.
- **Índices** em `parent_id`/`directory_id` e `owner_id` — toda listagem de pasta
  filtra por eles.
- **Migrations com Alembic desde já**, não "quando chegarmos lá". Retrofitting de
  migrations num schema que já existe é bem mais doloroso que começar com elas — trago
  essa etapa pra frente no roadmap (ver seção 15).

---

## 10. Autenticação

**Proposta: sessão via cookie assinado e `httpOnly`, não JWT.**

**Por quê:** esta é uma aplicação web tradicional (frontend server-side), acessada pelo
mesmo navegador no desktop e no celular — não existe um app nativo separado nem
terceiros consumindo a API. Cookie de sessão é o padrão natural pra esse cenário: o
navegador cuida de enviar o cookie sozinho, sem JavaScript manual anexando
`Authorization` header. JWT brilha quando existem múltiplos clientes independentes
(app mobile nativo, integrações de terceiros) — nenhum existe aqui ainda.

**Se um dia** você construir um app mobile nativo separado (não só acessar pelo
navegador do celular), JWT volta à mesa — fica registrado como decisão futura, não
descartada de vez.

Hash de senha: `bcrypt` ou `argon2` (via `passlib`).

**Autorização no MVP:** só checagem de dono (`owner_id == usuário logado`) — sem
sistema de permissões/grupos, que é fase futura.

---

## 11. Segurança (nível MVP, sem overengineering)

- **Path traversal:** estruturalmente eliminado pela decisão da seção 6 (nomes de
  arquivo nunca viram caminho físico).
- **Limite de tamanho de upload:** sim, configurável.
- **Allowlist de tipo de arquivo:** não no MVP — é armazenamento pessoal, não upload de
  terceiros não confiáveis.
- **Secrets** (senha do banco, chave de sessão): variável de ambiente via `.env`
  (fora do Git, mesmo padrão já usado no laboratório).
- **HTTPS:** adiado — o transporte já é criptografado pelo WireGuard do Tailscale
  enquanto o acesso for só por lá. Se um dia for exposto além do Tailscale, HTTPS via
  reverse proxy se torna obrigatório antes disso acontecer, não depois.

---

## 12. Docker / Compose (MVP)

```yaml
services:
  filehub:    # aplicação FastAPI (API + templates)
  postgres:   # metadados
```

Reverse proxy **fora** do MVP (seção 4). Volumes: `postgres-data` (persistência do
banco) e `filehub-storage` (arquivos reais). Healthcheck: `postgres` já tem
`pg_isready` pronto; `filehub` expõe um endpoint `/health` simples, checado via `curl`
no Compose.

---

## 13. Git, testes, CI/CD, backup — sem objeção

Sua proposta de fases para essas áreas está correta e não vejo motivo para mudar a
ordem: Git desde o início, `pytest` (unitários para `services`/`repositories`,
integração para as rotas), GitHub Actions só depois que existirem testes de verdade
para rodar, backup (dump do Postgres + tar do diretório de storage) com teste de
restore real, não só teoria.

---

## 14. O que fica de fora do MVP (concordo integralmente)

Kubernetes, microsserviços, Redis, filas, múltiplos servidores, cloud, observabilidade
complexa — tudo fase futura, como você já havia definido. Sem objeção.

---

## 15. Roadmap revisado

| Fase | O que |
|---|---|
| 0 | Arquitetura (este documento) — **discussão em andamento** |
| 1 | Estrutura do projeto Python + POO (esqueleto de `app/`) |
| 2 | FastAPI básico + `/health` |
| 3 | PostgreSQL + SQLAlchemy + **Alembic desde já** |
| 4 | Modelagem: `User`, `Directory`, `File` |
| 5 | Autenticação (sessão + cookie) |
| 6 | CRUD de pastas |
| 7 | Upload/download de arquivos (`FileStorage` + `LocalFileStorage`) |
| 8 | Interface web (Jinja2 + `htmx`) |
| 9 | Docker + Dockerfile |
| 10 | Docker Compose (filehub + postgres) |
| 11 | Deploy no homelab, acesso via Tailscale |
| 12 | Testes (`pytest`) |
| 13 | GitHub Actions / CI |
| 14 | Backup e restore |
| 15+ | Busca, tags, lixeira, compartilhamento, permissões, reverse proxy/HTTPS, workers assíncronos, observabilidade, Kubernetes, OCI — nessa ordem aproximada, revista conforme necessidade real surgir |

---

## 16. Riscos e trade-offs assumidos

- **Servidor único, sem alta disponibilidade** — coerente com o estágio do laboratório;
  backup disciplinado (fase 14) é o que compensa isso, não redundância.
- **Frontend server-side troca "vitrine de SPA moderna" por simplicidade e foco em
  Python/DevOps** — decisão consciente, revisitável se o objetivo de portfólio mudar.
- **Sessão por cookie troca "escalabilidade stateless" por simplicidade** — aceitável
  na escala de um usuário único num homelab.

---

## 17. Definição final do MVP

Aplicação web única (FastAPI + Jinja2), com login por sessão (usuário único),
CRUD completo de pastas e arquivos, metadados em PostgreSQL (com Alembic desde o
início), arquivos reais em disco via uma interface `FileStorage` abstrata (implementação
local), containerizada via Docker Compose (`filehub` + `postgres`), acessível só via
Tailscale (sem reverse proxy/HTTPS ainda), sem sistema de permissões, sem
processamento assíncrono, sem Kubernetes, sem CI (chega quando houver testes).

---

## Próximo passo

Este documento é uma **proposta para discussão**, não uma decisão final. Os pontos que
mais merecem sua reação antes de qualquer código:

1. Frontend server-side (Jinja2/htmx) em vez de React/Vue — concorda?
2. Storage físico opaco por ID, não espelhando nomes de pasta — faz sentido?
3. Autenticação por sessão/cookie em vez de JWT — de acordo?
4. Estrutura de camadas simplificada agora, DDD completo só se/quando necessário —
   tudo bem começar assim?

Sem escrever nenhum código até fecharmos isso.
