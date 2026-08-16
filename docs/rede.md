# Rede

Última verificação: **2026-08-15**

## 1. Topologia

```text
Internet
   │
Roteador 192.168.15.1  ── DHCP · DNS · NAT
   │
   ├── NTB-UBUNTU     192.168.15.94   (Wi-Fi)
   └── srv-ubnt-001   192.168.15.182  (Wi-Fi)

Sobreposta a isso, a rede Tailscale (100.64.0.0/10):
   ├── ntb-ubuntu     100.111.99.46
   └── srv-ubnt-001   100.96.168.97
```

## 2. Interfaces do servidor

```text
lo           UNKNOWN   127.0.0.1/8
enp1s0       DOWN      (somente link-local IPv6) ← porta Ethernet, sem cabo
wlp0s20f3    UP        192.168.15.182/24  metric 600  ← Wi-Fi, interface ativa
tailscale0   UNKNOWN   100.96.168.97/32              ← túnel WireGuard
```

`tailscale0` aparece como `UNKNOWN` — isso é normal para interfaces TUN, não indica falha.

### Rotas

```text
default via 192.168.15.1 dev wlp0s20f3 proto dhcp src 192.168.15.182 metric 600
192.168.15.0/24 dev wlp0s20f3 proto kernel scope link src 192.168.15.182 metric 600
```

O `proto dhcp` confirma: o endereço **não é estático**, foi concedido pelo roteador.

### DNS

| Interface | Servidor DNS |
|---|---|
| `wlp0s20f3` | 192.168.15.1 (o próprio roteador) |
| `tailscale0` | 100.100.100.100 (MagicDNS do Tailscale) |

O MagicDNS é o que faz `ssh ubnt@srv-ubnt-001` funcionar sem `/etc/hosts` e sem digitar
o IP. É resolvido pelo `systemd-resolved` com roteamento por domínio.

## 3. Portas em escuta no servidor

Coletado com `ss -tulnp` (sem `sudo`, portanto sem nomes de processo).

| Proto | Endereço:Porta | Alcance | O que é |
|---|---|---|---|
| tcp | `0.0.0.0:22` | **toda a LAN + Tailscale** | SSH |
| tcp | `127.0.0.53:53`, `127.0.0.54:53` | só local | `systemd-resolved` |
| tcp | `100.96.168.97:62749` | só Tailscale | Tailscale (porta dinâmica) |
| udp | `0.0.0.0:41641` | toda a LAN + internet | Tailscale (WireGuard) |
| udp | `127.0.0.1:323` | só local | `chrony` (NTP) |
| udp | `192.168.15.182:68` | LAN | cliente DHCP |

### Ponto de atenção

O SSH escuta em `0.0.0.0:22`, ou seja, **em todas as interfaces**, não apenas na
Tailscale. Consequência: qualquer dispositivo na rede Wi-Fi de casa — incluindo um
aparelho de visita ou uma TV comprometida — consegue alcançar a porta 22 do servidor.

Isso **não** significa exposição à internet: para isso seria necessário port forwarding
no roteador, que não existe. Mas é uma superfície de ataque maior que o necessário.
Tratamento em [seguranca.md](seguranca.md).

## 4. "Está funcionando" ≠ "está acessível pela rede"

Distinção central deste laboratório. Um serviço pode estar perfeitamente no ar e ainda
assim inacessível. As três camadas para verificar, em ordem:

```text
1. O processo está rodando?      systemctl status <serviço>
2. Está escutando em qual IP?    ss -tulnp | grep <porta>
3. O firewall permite?           sudo ufw status verbose
4. A rota/DNS chegam até ele?    ping / tailscale ping / nc -zv
```

O erro clássico é um serviço escutando em `127.0.0.1:8080` — funcionando, mas
inalcançável de fora da máquina. Vai acontecer com Docker.

### Comandos de diagnóstico

```bash
tailscale ping srv-ubnt-001
```

```bash
nc -zv 100.96.168.97 22
```

```bash
ssh ubnt@srv-ubnt-001 'ss -tulnp'
```

## 5. Problema conhecido: IP por DHCP

O servidor recebe `192.168.15.182` do roteador por DHCP. Esse endereço **pode mudar**
após reboot do roteador, expiração da concessão ou troca de rede.

Impacto real hoje é baixo, porque o acesso principal é pelo nome Tailscale
(`srv-ubnt-001`), cujo IP `100.96.168.97` é estável. Mas o IP de LAN vai importar quando
publicarmos serviços acessíveis pela rede local.

Duas abordagens, quando chegarmos nesta etapa:

| Abordagem | Onde se configura | Prós | Contras |
|---|---|---|---|
| **Reserva DHCP** (recomendada) | no roteador, por MAC | sem risco de derrubar a rede do servidor; centralizado | depende de acesso ao roteador |
| **IP estático via Netplan** | `/etc/netplan/*.yaml` no servidor | independe do roteador; é o que se vê em ambiente profissional | erro de digitação derruba a rede **e o SSH junto** |

Se optarmos por Netplan, usar obrigatoriamente `sudo netplan try`, que reverte
automaticamente em 120 s se a configuração não for confirmada. Nunca `netplan apply`
direto em uma máquina acessada remotamente.

Arquivos Netplan atuais no servidor (permissão `600`, root):

```text
/etc/netplan/00-installer-config.yaml   185 bytes
/etc/netplan/50-cloud-init.yaml         159 bytes
```

## 6. Próximos passos de rede

- [ ] Migrar o servidor de Wi-Fi para cabo (`enp1s0`), se houver ponto disponível
- [ ] Fixar o IP de LAN (reserva DHCP preferencialmente)
- [ ] Restringir o SSH para escutar apenas na interface Tailscale
- [x] Ativar o `ufw` com regras corretas — feito em 2026-08-15, ver [seguranca.md](seguranca.md)
- [ ] Documentar rede de containers quando o Docker entrar
