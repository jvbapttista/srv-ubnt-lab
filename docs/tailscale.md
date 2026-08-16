# Tailscale

Última verificação: **2026-08-15**

## 1. Finalidade no laboratório

O Tailscale é a **camada de acesso remoto** do laboratório. Ele cria uma rede privada
(baseada em WireGuard) entre dispositivos autorizados, permitindo alcançar
`srv-ubnt-001` de fora de casa **sem abrir a porta 22 no roteador**.

```text
Dispositivo remoto
      ↓
   Tailscale (WireGuard)
      ↓
Rede privada 100.64.0.0/10
      ↓
srv-ubnt-001
      ↓
   SSH → shell
```

O Tailscale **não substitui** o SSH nem o hardening do servidor. Ele resolve
conectividade, não autenticação do sistema operacional.

### Por que isso é melhor que port forwarding

| | Port forwarding (22 aberta na internet) | Tailscale |
|---|---|---|
| Quem alcança a porta | qualquer máquina da internet | só dispositivos autenticados no tailnet |
| Tentativas de força bruta | constantes, minutos após abrir | não existem — a porta não está pública |
| Requer IP fixo / DDNS | sim | não |
| Requer mexer no roteador | sim | não |
| Criptografia | do SSH apenas | WireGuard + SSH |

## 2. Estado atual

### Dispositivos no tailnet

| Nome | IP Tailscale | SO | Papel |
|---|---|---|---|
| `ntb-ubuntu` | 100.111.99.46 | Linux | estação de trabalho |
| `srv-ubnt-001` | 100.96.168.97 | Linux | servidor do laboratório |

Ambos autenticados sob a mesma conta. Nenhum outro dispositivo autorizado no momento.

### Serviço no servidor

| Item | Valor |
|---|---|
| Versão | 1.102.2 |
| `tailscaled` ativo | sim |
| `tailscaled` habilitado no boot | sim |
| IPv4 | 100.96.168.97 |
| IPv6 | `fd7a:115c:a1e0::e501:a8c1` |
| Interface | `tailscale0` |
| Porta WireGuard | UDP 41641 |

### Conectividade verificada

```text
tailscale ping srv-ubnt-001
  pong via DERP(sao)                    381 ms   ← relay em São Paulo
  pong via 192.168.15.182:41641         123 ms   ← conexão direta
```

Interpretação: a primeira resposta passou por um servidor de relay (DERP) enquanto o
túnel direto era negociado; a segunda já foi **direta**, ponto a ponto. Isso é o
comportamento ideal — como as duas máquinas estão na mesma LAN, o tráfego não sai da
rede local depois de estabelecido.

Do lado do servidor, o status confirma: `active; direct 192.168.15.94:41641`.

## 3. MagicDNS

É o que permite `ssh ubnt@srv-ubnt-001` em vez de decorar `100.96.168.97`.

Funciona porque o `tailscaled` registra `100.100.100.100` como servidor DNS para a
interface `tailscale0`, e o `systemd-resolved` roteia as consultas do domínio do tailnet
para lá. Confirmado em ambas as máquinas.

Se o nome parar de resolver, verificar nesta ordem:

```bash
resolvectl status tailscale0
```

```bash
tailscale status
```

```bash
resolvectl query srv-ubnt-001
```

## 4. Comandos relevantes

```bash
tailscale status
```
Lista dispositivos do tailnet e o tipo de conexão (direta ou via relay).

```bash
tailscale ip -4
```
Mostra o IP Tailscale da máquina local.

```bash
tailscale ping srv-ubnt-001
```
Testa a conectividade **do túnel** — diferente do `ping` do ICMP comum, mostra se a
conexão é direta ou por relay.

```bash
tailscale netcheck
```
Diagnóstico de rede: tipo de NAT, latência até os relays, se UDP está disponível.

```bash
systemctl status tailscaled
```

```bash
sudo journalctl -u tailscaled -n 50 --no-pager
```

## 5. Cuidados

- **Nunca** registrar auth keys, tokens ou chaves em arquivos versionados. O `.gitignore`
  da raiz já bloqueia padrões comuns, mas a responsabilidade é do operador.
- O estado do Tailscale no servidor fica em `/var/lib/tailscale/` — não copiar para o
  repositório.
- Autorizar um dispositivo no tailnet dá a ele acesso de rede ao servidor. Revisar
  periodicamente a lista de dispositivos no painel do Tailscale e remover o que não for
  mais usado.
- Chaves de dispositivo expiram por padrão. Se o servidor sair do tailnet sozinho após
  meses, a causa provável é expiração — considerar desativar a expiração de chave **para
  o servidor** no painel, já que ele não tem quem o reautentique presencialmente.

## 6. Recursos ainda não usados

Documentados aqui como opções futuras, **não configurados**:

| Recurso | Para quê | Quando avaliar |
|---|---|---|
| ACLs do tailnet | restringir quem alcança o quê dentro da rede privada | quando houver mais dispositivos |
| Tailscale SSH | o Tailscale intermedia a autenticação SSH | opcional; hoje a chave própria é suficiente e ensina mais |
| Subnet router | expor a LAN 192.168.15.0/24 inteira via Tailscale | se precisar alcançar outros equipamentos de casa |
| Tailscale Serve / Funnel | publicar um serviço HTTPS interno (ou público) | quando houver aplicações web no servidor |
| Exit node | rotear todo o tráfego pelo servidor | não é objetivo do laboratório agora |

## 7. Troubleshooting

| Sintoma | Verificação |
|---|---|
| `srv-ubnt-001` não resolve | `resolvectl status tailscale0`; `tailscale status` |
| Dispositivo aparece offline | a máquina pode ter suspendido — ver [seguranca.md](seguranca.md) |
| Conexão só via DERP (lenta) | `tailscale netcheck`; NAT restritivo ou UDP 41641 bloqueado |
| `tailscaled` não sobe | `journalctl -u tailscaled` |
| Servidor sumiu do tailnet | expiração de chave — reautenticar com `sudo tailscale up` |

## 8. Registro de alterações

| Data | Alteração |
|---|---|
| 2026-08-15 | Documentação inicial criada a partir do estado real verificado. Nenhuma alteração feita na configuração do Tailscale. |
