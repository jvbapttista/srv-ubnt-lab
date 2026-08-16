# Arquitetura do laboratório

Última verificação: **2026-08-15**

## 1. Visão geral

O laboratório é composto por **duas máquinas físicas** na mesma rede doméstica
(`192.168.15.0/24`), unidas também por uma rede privada Tailscale.

```text
                        Internet
                            │
                            │
                    Roteador 192.168.15.1
                    (DHCP + DNS + NAT)
                            │
            ┌───────────────┴───────────────┐
            │                               │
     NTB-UBUNTU (Wi-Fi)             srv-ubnt-001 (Wi-Fi)
     192.168.15.94                  192.168.15.182
     Estação de trabalho            Servidor do laboratório
     Ubuntu 26.04 Desktop           Ubuntu 26.04 Server
            │                               │
            └────────── Tailscale ──────────┘
                (WireGuard, rede 100.64.0.0/10)
       100.111.99.46              100.96.168.97
```

## 2. Papéis

### `NTB-UBUNTU` — estação de trabalho

Dell Inspiron 15 7000 Gaming. É de onde eu **administro** o laboratório.

- Cliente SSH e chave privada ed25519.
- Cliente Tailscale.
- **Hospeda a raiz do laboratório**: `/home/joao/Documentos/SRV_UBNT`.
- Não roda serviços do laboratório.

### `srv-ubnt-001` — servidor

Dell Inspiron 3501 (notebook reaproveitado como servidor). É onde os **serviços rodam**.

- Ubuntu Server, sem interface gráfica.
- Acesso exclusivamente remoto, via SSH.
- Futuro host de Docker, aplicações, banco de dados e monitoramento.

## 3. Decisão de arquitetura: onde vive a raiz do laboratório

**Decisão:** a raiz `/home/joao/Documentos/SRV_UBNT` fica **no notebook**, não no servidor.

**Racional:**

- Documentação e código precisam sobreviver a uma reinstalação do servidor. Se a raiz
  estivesse no servidor, formatá-lo (algo que vai acontecer neste laboratório) levaria a
  documentação junto.
- O fluxo profissional real é esse: você versiona no seu ambiente de trabalho, o servidor
  recebe o código. O servidor é *gado*, não *bicho de estimação*.
- Permite editar com ferramentas gráficas e commitar sem depender do servidor estar de pé.

**Consequência:** arquivos que precisam **executar** no servidor (`docker-compose.yml`,
scripts, manifests) não bastam existir aqui. Precisam chegar lá. O caminho previsto é:

```text
NTB-UBUNTU (edito e commito)
      │
      ├── git push ──► GitHub
      │                   │
      └───────────────────┴──► git clone/pull no servidor  (caminho preferido)
```

Enquanto o repositório remoto não existir, o transporte pontual é `scp`/`rsync` sobre a
rede Tailscale. Isso é **provisório** e deve ser registrado quando usado.

**O que NÃO fazer:** editar arquivos direto no servidor via `nano` e deixá-los só lá.
Isso cria configuração não versionada e não reproduzível — exatamente o que este
laboratório quer aprender a evitar.

## 4. Camadas da infraestrutura

```text
Hardware físico (Dell Inspiron 3501)
        ↓
Ubuntu Server 26.04 LTS
        ↓
Rede: Wi-Fi + DHCP (LAN) · Tailscale (privada)
        ↓
Acesso: SSH por chave, via Tailscale
        ↓
Firewall: ufw (ativo — SSH liberado para LAN e Tailscale, ver docs/seguranca.md)
        ↓
[a construir] Docker → Compose → Aplicações → Observabilidade → Kubernetes
```

## 5. Estrutura de diretórios da raiz

```text
SRV_UBNT/
├── README.md          índice e estado geral
├── .gitignore         proteção contra vazamento de segredos
└── docs/              documentação técnica
```

Diretórios como `scripts/`, `configs/`, `docker/`, `projects/` e `kubernetes/` serão
criados **quando houver conteúdo real** para eles. Diretório vazio criado "por
antecipação" só polui o repositório.

## 6. Roadmap (ordem deliberada)

| # | Etapa | Situação |
|---|---|---|
| 1 | Ubuntu Server instalado | concluído |
| 2 | SSH por chave | concluído |
| 3 | Tailscale | concluído |
| 4 | Documentação do estado real | concluído |
| 5 | Estabilizar o servidor (tampa, IP fixo, hardening SSH, ufw) | **próximo** |
| 6 | Git/GitHub para este repositório | pendente |
| 7 | Docker (conceitos → instalação → primeiro container) | pendente |
| 8 | Docker Compose | pendente |
| 9 | Aplicação real hospedada | pendente |
| 10 | Reverse proxy + TLS | pendente |
| 11 | Monitoramento / Observabilidade | pendente |
| 12 | Kubernetes | pendente |
| 13 | Correlação com OCI | pendente |

A etapa 5 vem antes de Docker de propósito: não faz sentido subir serviços sobre uma base
que suspende ao fechar a tampa e cujo IP pode mudar sozinho.

## 7. Correlação com OCI

| Conceito local | Equivalente aproximado na OCI |
|---|---|
| Servidor físico `srv-ubnt-001` | Compute Instance |
| Rede `192.168.15.0/24` | VCN + Subnet |
| `ufw` | Security List / Network Security Group |
| Tailscale | Bastion / VPN / FastConnect (acesso privado) |
| SSH por chave | SSH por chave em instância OCI (idêntico) |
| LVM / partições | Block Volume |
| Docker (futuro) | OCI Container Instances / OKE |
