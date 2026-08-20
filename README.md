# Laboratório DevOps — SRV_UBNT

Raiz oficial do laboratório. **Todo** material criado para o laboratório (documentação,
scripts, compose, manifests, projetos, notas) vive aqui dentro.

**Repositório:** [github.com/jvbapttista/srv-ubnt-lab](https://github.com/jvbapttista/srv-ubnt-lab)
(público, versionado desde 2026-08-15)

> Este diretório fica no **notebook de trabalho** (`NTB-UBUNTU`), não no servidor.
> Ver [docs/arquitetura.md](docs/arquitetura.md) para entender por quê e como os
> arquivos chegam ao servidor.

## Máquinas do laboratório

| Papel | Nome | SO | IP LAN | IP Tailscale |
|---|---|---|---|---|
| Estação de trabalho / cliente | `NTB-UBUNTU` | Ubuntu 26.04 LTS (Desktop) | 192.168.15.94 | 100.111.99.46 |
| Servidor do laboratório | `srv-ubnt-001` | Ubuntu 26.04 LTS (Server) | 192.168.15.182 (Wi-Fi, DHCP) | 100.96.168.97 |

## Acesso rápido

```bash
ssh ubnt@srv-ubnt-001
```

Funciona por chave SSH (ed25519) através da rede Tailscale, sem senha e sem expor a
porta 22 na internet. Detalhes em [docs/ssh.md](docs/ssh.md) e
[docs/tailscale.md](docs/tailscale.md).

## Índice da documentação

| Documento | Conteúdo |
|---|---|
| [docs/servidor.md](docs/servidor.md) | **Ficha técnica do servidor** — hostname, propósito, como logar, o que roda, onde tudo fica, aplicações hospedadas. Comece por aqui. |
| [docs/arquitetura.md](docs/arquitetura.md) | Visão geral, papéis das máquinas, onde ficam os arquivos, roadmap |
| [docs/inventario.md](docs/inventario.md) | Hardware, SO, disco, memória — estado real verificado |
| [docs/rede.md](docs/rede.md) | Interfaces, IPs, DNS, rotas, portas em escuta |
| [docs/ssh.md](docs/ssh.md) | Servidor e cliente SSH, chaves, configuração atual, hardening pendente |
| [docs/tailscale.md](docs/tailscale.md) | Rede privada, dispositivos, comandos, troubleshooting |
| [docs/seguranca.md](docs/seguranca.md) | Postura atual, riscos abertos, pendências priorizadas |
| [docs/docker.md](docs/docker.md) | Instalação, conceitos, decisão sobre o grupo `docker`, Docker vs `ufw`, comandos do dia a dia |
| [docs/filehub-arquitetura.md](docs/filehub-arquitetura.md) | Arquitetura completa do projeto FileHub — aprovada |
| [docs/filehub-progresso.md](docs/filehub-progresso.md) | Progresso do FileHub, fase por fase |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Problemas reais encontrados, causa e solução |
| [notes/](notes/) | Código explicado bloco por bloco — material de estudo, separado da documentação de infraestrutura |

## Estado do laboratório

Etapas concluídas:

- [x] Instalação do Ubuntu Server no hardware físico
- [x] Acesso SSH por chave pública
- [x] Tailscale instalado e autenticado nas duas máquinas
- [x] Documentação inicial do estado real
- [x] Estabilizar o servidor: tampa não suspende mais, firewall ativo, senha SSH
      desativada, reboot validado, `ListenAddress` avaliado, chave de recuperação criada
      (todos os P0/P1/P2 de [docs/seguranca.md](docs/seguranca.md) resolvidos)
- [x] Git/GitHub para este repositório — [github.com/jvbapttista/srv-ubnt-lab](https://github.com/jvbapttista/srv-ubnt-lab)
- [x] Docker instalado (v29.7.2 + Compose v5.4.0) — ver [docs/docker.md](docs/docker.md)
- [x] ~~Contador de Visitas~~ (Flask + Redis) — cancelado em 2026-08-16, sem valor de
      portfólio; serviu de aprendizado de Compose e revelou o achado real de segurança
      documentado abaixo
- [ ] Instalar `iptables-persistent` e validar regras `DOCKER-USER` após reboot
- [ ] ⏸️ **FileHub** — pausado (não cancelado) em 2026-08-18, Fases 1-2 concluídas
      (esqueleto + FastAPI/`health`). Retomar quando fizer sentido. Ver
      [docs/filehub-arquitetura.md](docs/filehub-arquitetura.md) e
      [docs/filehub-progresso.md](docs/filehub-progresso.md)
- [ ] **Direção atual: aplicações self-hosted prontas** (Nextcloud, CasaOS, etc.) para
      organizar e evoluir o homelab na prática, combinado com estudo estruturado
      (cursos, Udemy, YouTube)
- [ ] Monitoramento / Observabilidade
- [ ] Kubernetes
- [ ] Integração com OCI

Pendências menores (P3, sem urgência) em [docs/seguranca.md](docs/seguranca.md):
`~/.ssh/config`, IP de LAN fixo, cabo de rede, passphrase na chave principal.

## Convenções

- Documentação em Markdown, dentro de `docs/`.
- Nada de credenciais, tokens, chaves privadas ou senhas em nenhum arquivo versionado.
- Segredos (chaves, tokens, senhas) ficam no **Bitwarden**, pasta `Laboratório DevOps`,
  como Nota Segura — nunca em arquivo local nem no repositório. Formato de referência em
  [docs/servidor.md](docs/servidor.md), seção "Chave de recuperação".
- Cada projeto hospedado no laboratório ganha um `README.md` pensado também como
  material de portfólio (contexto, problema resolvido, decisões técnicas, não só "como
  rodar") — os projetos serão documentados para publicação no LinkedIn.
- Todo código (`.py`, `Dockerfile`, `docker-compose.yml`, etc.) ganha uma explicação
  bloco por bloco em [notes/](notes/), mantida atualizada conforme o código evolui.
- Arquivos que o sistema exige em caminhos próprios (`/etc`, `/var`, `/opt`) permanecem lá;
  quando relevante, mantemos aqui uma **cópia de referência** em `configs/`, claramente
  marcada como cópia — nunca como fonte de verdade.
- Toda alteração relevante no servidor atualiza o `.md` correspondente **no mesmo momento**.

---
Última verificação do estado real: **2026-08-15**
