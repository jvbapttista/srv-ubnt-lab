# FileHub

Plataforma pessoal de armazenamento e gerenciamento de arquivos, hospedada no
laboratório DevOps.

**Status: em desenvolvimento — Fases 1–2 do roadmap concluídas.**

- Arquitetura completa (decisões técnicas, trade-offs, roadmap):
  [`docs/filehub-arquitetura.md`](../../docs/filehub-arquitetura.md)
- Progresso fase a fase: [`docs/filehub-progresso.md`](../../docs/filehub-progresso.md)
- Código explicado bloco a bloco: [`notes/filehub/`](../../notes/filehub/)

## Rodando localmente

```bash
cd projects/filehub
source .venv/bin/activate
uvicorn app.main:app --reload
```

Depois acesse `http://127.0.0.1:8000/health` ou `http://127.0.0.1:8000/docs`.
