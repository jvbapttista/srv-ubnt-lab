# SSH

Última verificação: **2026-08-15**

## 1. Papel do SSH no laboratório

SSH é o **único** meio de administrar `srv-ubnt-001`. O servidor não tem interface
gráfica e fica normalmente sem teclado/monitor. Se o SSH cair, resta ir fisicamente até
a máquina. Por isso toda alteração em SSH, rede ou firewall é tratada como operação de
risco.

Relação com o Tailscale:

```text
Tailscale = o caminho (rede privada até o servidor)
SSH       = o protocolo (administração do servidor)
```

## 2. Como acessar

```bash
ssh ubnt@srv-ubnt-001
```

- Usuário: `ubnt`
- Autenticação: chave pública ed25519, sem senha
- Nome resolvido pelo MagicDNS do Tailscale
- Alternativa por IP Tailscale: `ssh ubnt@100.96.168.97`
- Alternativa pela LAN: `ssh ubnt@192.168.15.182` (IP pode mudar — ver [rede.md](rede.md))

## 3. Chaves

### No cliente (`NTB-UBUNTU`)

```text
~/.ssh/id_ed25519       chave privada   permissão 600   NUNCA sai desta máquina
~/.ssh/id_ed25519.pub   chave pública   permissão 644   pode ser distribuída
~/.ssh/known_hosts      fingerprints dos servidores já aceitos
```

Gerada com `ssh-keygen -t ed25519`.

**ed25519 e não RSA:** chaves menores, verificação mais rápida e segurança equivalente a
RSA de 3072+ bits. É o padrão atual recomendado.

### No servidor (`srv-ubnt-001`)

```text
/home/ubnt/.ssh/authorized_keys   permissão 600   contém 1 chave: ssh-ed25519 joao@NTB-UBUNTU
```

Instalada com `ssh-copy-id ubnt@srv-ubnt-001`.

**Como funciona a autenticação por chave**, resumidamente: o servidor consulta
`authorized_keys`, envia um desafio cifrado com a chave pública, e só a chave privada
correspondente consegue respondê-lo. A chave privada nunca trafega pela rede.

**Permissões importam.** O `sshd` recusa a autenticação — silenciosamente, do ponto de
vista do cliente — se `~/.ssh` não for `700` ou `authorized_keys` não for `600`. É a
causa nº 1 de "minha chave não funciona".

## 4. Configuração atual do servidor (atualizado em 2026-08-15)

`/etc/ssh/sshd_config` (linhas efetivas, sem comentários) continua o mesmo arquivo
base; toda a customização vive em drop-ins:

```text
Include /etc/ssh/sshd_config.d/*.conf
KbdInteractiveAuthentication no
UsePAM yes
X11Forwarding yes
PrintMotd no
AcceptEnv LANG LC_* COLORTERM NO_COLOR
Subsystem sftp /usr/lib/openssh/sftp-server
```

Drop-ins em `/etc/ssh/sshd_config.d/`, lidos em ordem alfabética:

```text
50-cloud-init.conf   → PasswordAuthentication no   (editado nesta data, era yes)
90-hardening.conf    → PasswordAuthentication no
                        PermitRootLogin no
                        X11Forwarding no
```

### Valor efetivo (via `sudo sshd -T`)

| Diretiva | Valor efetivo | Avaliação |
|---|---|---|
| `PasswordAuthentication` | **no** | resolvido — só chave autentica |
| `PermitRootLogin` | **no** | resolvido — nem por chave |
| `Port` | 22 | ok |
| `ListenAddress` | todas as interfaces (LAN + Tailscale), mas filtradas pelo `ufw` | ver [seguranca.md](seguranca.md) |
| `X11Forwarding` | **no** | resolvido |
| `MaxAuthTries` | 6 | aceitável, ainda mais com senha desativada |

### Pegadinha encontrada: ordem de leitura dos drop-ins

Diferente de quase todo outro arquivo de configuração Linux, no `sshd_config` **a
primeira ocorrência de uma diretiva vence; ocorrências posteriores são ignoradas em
silêncio**, sem erro. Isso mordeu na prática: criamos `90-hardening.conf` com
`PasswordAuthentication no`, mas `50-cloud-init.conf` (lido antes, por ordem alfabética)
já tinha `PasswordAuthentication yes` — e continuou valendo, apesar do `sshd -t` validar
a sintaxe sem reclamar.

**Lição para qualquer mudança futura em `sshd_config.d/`:** antes de criar um novo
drop-in, conferir se a diretiva já existe em outro arquivo com nome alfabeticamente
anterior:

```bash
sudo grep -rn "NomeDaDiretiva" /etc/ssh/sshd_config.d/
```

E sempre confirmar com `sudo sshd -T`, nunca só validar a sintaxe (`sshd -t`) — sintaxe
válida não significa que a diretiva está em vigor.

## 5. Serviço: `ssh.service` vs `ssh.socket`

Verificação feita:

```text
ssh.service   active=active   enabled=disabled
ssh.socket    active=active   enabled=enabled
```

À primeira vista `ssh.service disabled` parece indicar que o SSH não sobe no boot. **Não
é o caso.** Desde o Ubuntu 22.10 o OpenSSH usa *socket activation*: o `systemd` (via
`ssh.socket`) é quem abre a porta 22 e só inicia o `sshd` quando chega uma conexão.

Portanto, o que garante o acesso após reboot é `ssh.socket`, que está **enabled**.
Situação correta.

Consequência prática: para alterar a porta do SSH não basta editar `Port` no
`sshd_config` — é preciso mexer no `ssh.socket`. Anotar isso se algum dia mudarmos a porta.

### Comandos úteis

```bash
systemctl status ssh.socket ssh.service
```

```bash
sudo sshd -T | grep -Ei 'passwordauth|permitroot|port|listenaddress|pubkey'
```

`sshd -T` mostra a configuração **efetiva**, já resolvendo includes e padrões implícitos.
É a forma correta de auditar — muito melhor que ler o arquivo.

## 6. Procedimento seguro para alterar o SSH

Qualquer erro no `sshd_config` pode derrubar o acesso remoto permanentemente. O
procedimento obrigatório:

1. **Manter a sessão SSH atual aberta.** Ela não cai quando o serviço reinicia.
2. Fazer backup: `sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak-AAAA-MM-DD`
3. Editar (preferencialmente um drop-in em `/etc/ssh/sshd_config.d/`, não o arquivo principal).
4. **Validar a sintaxe antes de aplicar:** `sudo sshd -t` — não retorna nada se estiver ok.
5. Recarregar: `sudo systemctl reload ssh`
6. **Abrir um segundo terminal** e testar uma nova conexão.
7. Só fechar a sessão original depois que a nova funcionar.
8. Atualizar este documento.

Se o passo 6 falhar, a sessão do passo 1 ainda permite reverter o backup.

## 7. Melhorias pendentes

Priorizadas em [seguranca.md](seguranca.md):

- [x] Desabilitar autenticação por senha (`PasswordAuthentication no`) — 2026-08-15
- [x] Explicitar `PermitRootLogin no` — 2026-08-15
- [x] Desligar `X11Forwarding` — 2026-08-15
- [x] `ListenAddress` avaliado e mantido no padrão por decisão consciente — restringir
      o bind a um IP fixo arriscaria o `sshd` falhar ao iniciar se o IP mudasse (DHCP) ou
      a interface Tailscale subisse atrasada no boot. Mitigado via `ufw`. Ver [seguranca.md](seguranca.md).
- [ ] Criar `~/.ssh/config` no notebook com um alias e configuração explícita
- [ ] Avaliar passphrase na chave privada + `ssh-agent`
- [ ] Avaliar `fail2ban` (menos relevante agora, com senha desativada)

## 8. Troubleshooting

| Sintoma | Causa provável | Verificação |
|---|---|---|
| `Permission denied (publickey)` | chave ausente ou permissões erradas no servidor | `ls -la ~/.ssh` no servidor; `ssh -v` no cliente |
| `Connection refused` | `sshd`/socket parado | `systemctl status ssh.socket` |
| `Connection timed out` | firewall, rota ou máquina suspensa | `tailscale ping srv-ubnt-001` |
| `Host key verification failed` | host key mudou (reinstalação) | conferir a mudança e então `ssh-keygen -R <host>` |
| Conexão cai sozinha | servidor suspendeu (tampa) | ver [seguranca.md](seguranca.md) |

Diagnóstico detalhado do lado do cliente:

```bash
ssh -vvv ubnt@srv-ubnt-001
```

Log do lado do servidor:

```bash
sudo journalctl -u ssh -n 50 --no-pager
```

## 9. Registro de alterações

| Data | Alteração |
|---|---|
| 2026-08-15 | Chave `ed25519` do notebook adicionada ao `known_hosts` para o IP `100.96.168.97` (aceite do host key durante a auditoria) |
| 2026-08-15 | Documentação inicial criada a partir do estado real verificado |
