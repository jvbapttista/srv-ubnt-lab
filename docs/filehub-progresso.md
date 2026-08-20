# FileHub — Progresso

Acompanhamento das fases definidas em [filehub-arquitetura.md](filehub-arquitetura.md),
seção 15. Este documento muda a cada sessão de trabalho; a arquitetura em si (as
decisões e seus porquês) fica estável em `filehub-arquitetura.md`.

## ⏸️ PAUSADO em 2026-08-18 — não cancelado

Decisão do autor: priorizar, por ora, rodar e aprender com aplicações self-hosted já
existentes (Nextcloud, CasaOS, etc.) para organizar e evoluir o homelab na prática,
combinado com estudo estruturado (cursos, Udemy, YouTube). O FileHub volta a ser
desenvolvido quando fizer sentido, com mais bagagem prática acumulada.

**Nada foi removido** — código, arquitetura e explicações permanecem no repositório
exatamente como estão, prontos para retomar de onde paramos (Fase 3 seria o próximo
passo: PostgreSQL + SQLAlchemy + Alembic, com a decisão síncrono-vs-assíncrono ainda
em aberto).

Última atualização: 2026-08-18

## Ambiente de desenvolvimento

Desenvolvimento local no notebook, com ambiente virtual Python — **não** em container
ainda (Docker entra na Fase 9). Postgres, quando chegarmos na Fase 3, também deve rodar
localmente (via `docker run`, só o banco) enquanto a aplicação roda nativa.

```bash
cd projects/filehub
source .venv/bin/activate      # ativa o ambiente virtual
uvicorn app.main:app --reload  # roda a aplicação em desenvolvimento
```

## Fases

- [x] **Fase 0 — Arquitetura.** Proposta completa discutida e aprovada em 2026-08-18
      (ver [filehub-arquitetura.md](filehub-arquitetura.md)).
- [x] **Fase 1 — Esqueleto do projeto.** Ambiente virtual criado, `requirements.txt`
      inicial (`fastapi`, `uvicorn[standard]`), estrutura de pacotes
      (`core/models/schemas/repositories/services/storage/api/templates`) com
      docstring explicando a responsabilidade de cada um.
- [x] **Fase 2 — FastAPI básico + `/health`.** Aplicação mínima criada em
      `app/main.py`, testada localmente: `GET /health` → `{"status": "ok"}`,
      `/docs` (Swagger, automático) respondendo. Explicado bloco a bloco em
      [`notes/filehub/app/main.py.md`](../notes/filehub/app/main.py.md).
- [ ] **Fase 3 — PostgreSQL + SQLAlchemy + Alembic** — próximo passo
- [ ] Fase 4 — Modelagem: `User`, `Directory`, `File`
- [ ] Fase 5 — Autenticação (sessão + cookie)
- [ ] Fase 6 — CRUD de pastas
- [ ] Fase 7 — Upload/download de arquivos
- [ ] Fase 8 — Interface web (Jinja2 + htmx)
- [ ] Fase 9 — Docker (Dockerfile)
- [ ] Fase 10 — Docker Compose
- [ ] Fase 11 — Deploy no homelab
- [ ] Fase 12 — Testes (pytest)
- [ ] Fase 13 — CI (GitHub Actions)
- [ ] Fase 14 — Backup e restore
- [ ] Fase 15+ — busca, tags, lixeira, compartilhamento, permissões, reverse
      proxy/HTTPS, workers assíncronos, observabilidade, Kubernetes, OCI
