# Inventário — estado real verificado

Última verificação: **2026-08-15**
Método: comandos somente-leitura executados via SSH (`hostnamectl`, `lscpu`, `free`,
`lsblk`, `df`, `ip`, `ss`, `systemctl`).

---

## `srv-ubnt-001` — servidor

### Sistema

| Item | Valor |
|---|---|
| Hostname | `srv-ubnt-001` |
| SO | Ubuntu 26.04 LTS (Server) |
| Kernel | 7.0.0-29-generic (atualizado em 2026-08-15, reboot deliberado) |
| Arquitetura | x86-64 |
| Machine ID | `d36a813a...` (truncado) |

> Histórico: até 2026-08-15 o servidor rodava o kernel `7.0.0-14-generic`, atrás do
> notebook (`7.0.0-29`), com atualização já baixada pelo `unattended-upgrades` aguardando
> reboot. Reiniciado deliberadamente nessa data, também como teste de resiliência —
> ver [seguranca.md](seguranca.md).

### Hardware

| Item | Valor |
|---|---|
| Fabricante / Modelo | Dell Inspiron 3501 (notebook) |
| CPU | Intel Core i3-1005G1 @ 1.20 GHz — 4 vCPUs (2 núcleos + HT) |
| Memória RAM | 14 GiB (≈ 708 MiB em uso, 12 GiB livres) |
| Swap | 4 GiB (0 B em uso) |

**Implicação prática:** 4 vCPUs e 14 GiB de RAM são suficientes para Docker, uma stack
de observabilidade modesta e um cluster Kubernetes de nó único (k3s). Não é suficiente
para um cluster multi-nó pesado na mesma máquina.

### Armazenamento

```text
sda                       931.5G  disco físico
├─sda1                        1G  vfat   /boot/efi
├─sda2                        2G  ext4   /boot
└─sda3                    928.5G  LVM2   (volume group ubuntu-vg)
  └─ubuntu--vg-ubuntu--lv   100G  ext4   /
```

| Ponto de montagem | Tipo | Tamanho | Usado | Livre | Uso |
|---|---|---|---|---|---|
| `/` | ext4 | 98 G | 7.7 G | 86 G | 9 % |
| `/boot` | ext4 | 2.0 G | 184 M | 1.7 G | 11 % |

**Ponto importante — ~828 GB não alocados.** O instalador do Ubuntu criou o volume
lógico com apenas 100 GB dos 928 GB disponíveis no volume group. O restante está livre
dentro do LVM, sem uso.

Isso **não é um problema**, é uma oportunidade: quando Docker e dados persistentes
começarem a consumir espaço, expandir o volume lógico a quente (`lvextend` +
`resize2fs`, sem downtime e sem reboot) é um exercício excelente de LVM. Registrar
aqui quando for feito.

Para confirmar o espaço livre no VG (requer `sudo`):

```bash
ssh ubnt@srv-ubnt-001 'sudo vgs && sudo lvs'
```

### Serviços relevantes

| Serviço | Ativo | Habilitado no boot | Observação |
|---|---|---|---|
| `ssh.service` | sim | **não** | normal: ativação por socket |
| `ssh.socket` | sim | **sim** | é este que garante SSH após reboot |
| `ufw` | **ativo**, com regras (desde 2026-08-15) | sim | SSH liberado para LAN e Tailscale; ver [seguranca.md](seguranca.md) |
| `tailscaled` | sim | sim | versão 1.102.2 |
| `unattended-upgrades` | sim | — | atualizações automáticas ligadas; kernel novo já baixado, aguardando reboot |

`/etc/apt/apt.conf.d/20auto-upgrades`:

```text
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
```

### Software instalado

| Pacote | Versão |
|---|---|
| git | 2.53.0 |
| tailscale | 1.102.2 |
| docker | **não instalado** |

### Usuário

| Item | Valor |
|---|---|
| Usuário principal | `ubnt` (uid 1000) |
| Grupos | `ubnt, adm, cdrom, sudo, dip, plugdev, users, lxd` |
| Acesso administrativo | via `sudo` (membro do grupo `sudo`) |

---

## `NTB-UBUNTU` — estação de trabalho

| Item | Valor |
|---|---|
| Hostname | `NTB-UBUNTU` |
| SO | Ubuntu 26.04 LTS (Desktop, GNOME/Wayland) |
| Kernel | 7.0.0-29-generic |
| Hardware | Dell Inspiron 15 7000 Gaming |
| OpenSSH | 10.2p1 |
| git | 2.53.0 |
| tailscale | ativo |
| docker | não instalado |

---

## Riscos de hardware identificados

O servidor é um **notebook**. Isso traz particularidades que uma VM não tem:

| Risco | Situação atual | Impacto |
|---|---|---|
| Fechar a tampa suspende a máquina | `HandleLidSwitch=suspend` (padrão, não alterado) | **Perda total de acesso remoto** |
| Bateria | não avaliada | possível desligamento em queda de energia — ou, ao contrário, funciona como no-break natural |
| Conexão Wi-Fi | única interface ativa; `enp1s0` (cabo) está DOWN | latência e estabilidade inferiores ao cabo |
| Temperatura | não monitorada | notebook fechado em uso contínuo tende a aquecer |

Tratamento em [seguranca.md](seguranca.md).
