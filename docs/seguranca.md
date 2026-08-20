# Segurança — postura atual e pendências

Última verificação: **2026-08-15**

Este documento registra o que já está correto, o que está em aberto e em que ordem
tratar. Itens marcados RESOLVIDO já foram executados e validados; os demais ainda não.

## 1. O que já está correto

| Item | Estado |
|---|---|
| Acesso remoto sem expor porta na internet | Tailscale, sem port forwarding |
| Autenticação SSH por chave ed25519 | funcionando |
| Firewall (`ufw`) | **ativo**, SSH liberado só para LAN e Tailscale (2026-08-15) |
| Autenticação por senha no SSH | **desativada** (2026-08-15) |
| Login como root pela rede | bloqueado por completo (`PermitRootLogin no`, 2026-08-15) |
| `X11Forwarding` | desligado (2026-08-15) |
| Suspensão ao fechar a tampa | desativada (2026-08-15) |
| Atualizações automáticas de segurança | `unattended-upgrades` ativo |
| Usuário administrativo separado do root | `ubnt` via `sudo` |
| `KbdInteractiveAuthentication` | desabilitado |
| Permissões de `~/.ssh` e `authorized_keys` | corretas (600) |
| Persistência do SSH no boot | garantida por `ssh.socket` (enabled) |

Base sólida, e as duas pendências P0 e a P1 mais urgente já resolvidas.

---

## 2. Pendências, por prioridade

### ~~P0 — Sem firewall + SSH escutando em IPv6 global~~ — RESOLVIDO em 2026-08-15

**Descoberto em 2026-08-15, corrigindo registro anterior errado.**

```text
sudo ufw status verbose  →  Status: inactive
```

O servidor **não tem firewall ativo**. Todas as portas em escuta estão acessíveis por
qualquer origem que consiga rotear até elas.

#### Erro de diagnóstico que levou ao registro incorreto

A primeira auditoria concluiu "ufw ativo" a partir de:

```text
systemctl is-active ufw   → active
systemctl is-enabled ufw  → enabled
```

Isso está **errado**. `ufw.service` é uma unit `oneshot` que executa
`/lib/ufw/ufw-init start` e termina. Se o ufw estiver desabilitado em `/etc/ufw/ufw.conf`,
o script não carrega regra alguma — mas a unit reporta `active (exited)` porque *ela*
executou com sucesso. Sucesso da unit ≠ firewall aplicando regras.

**Verificação correta e única confiável:**

```bash
sudo ufw status verbose
```

#### Por que a ausência de firewall é mais grave do que parece

Três fatos que se combinam:

1. `sshd -T` confirma `listenaddress [::]:22` — o SSH escuta também em **IPv6**.
2. A interface `wlp0s20f3` tem endereço `2804:1b3:a680:bda8:.../64`. O bloco `2804::/12`
   é IPv6 **global** (LACNIC/Brasil), não privado — é roteável pela internet.
3. Não há firewall no servidor.

IPv6 **não usa NAT**. No IPv4, o roteador é obrigado a traduzir endereços e por isso
protege por efeito colateral. No IPv6 cada dispositivo tem endereço público próprio e a
única barreira é o firewall — do roteador ou do host. Se o roteador da operadora não
filtrar tráfego de entrada IPv6, a porta 22 do servidor está acessível pela internet
inteira, **com autenticação por senha habilitada**.

#### Como confirmar se há exposição real

Um host com SSH exposto na internet recebe tentativas de força bruta em minutos. O log de
autenticação é a evidência direta:

```bash
sudo journalctl -u ssh --since "7 days ago" --no-pager | grep -ciE "failed|invalid user"
```

| Resultado | Interpretação | Ação |
|---|---|---|
| 0 ou poucas, todas de IPs da LAN | roteador filtra IPv6 de entrada | tratar como P1 planejado |
| dezenas/centenas de IPs desconhecidos | **servidor exposto à internet** | emergência: agir no mesmo dia |

**Resultado (2026-08-15):** 4 ocorrências em 7 dias, **todas de `100.111.99.46`** — o IP
Tailscale do próprio notebook `NTB-UBUNTU` (tentativas de senha errada e usuário `joao`
inexistente, geradas durante os próprios testes desta auditoria). Nenhum IP externo,
nenhum padrão de força bruta automatizada (que viria de múltiplos IPs testando usuários
genéricos como `admin`/`root`/`test`).

**Conclusão: sem evidência de exposição real à internet no momento.** O risco teórico
(porta 22 escutando em IPv6 global, sem firewall) permanece e continua sendo P0, mas a
urgência passa de "agir hoje" para "resolver com atenção, sem pânico".

Confirmado também em `/etc/ufw/ufw.conf`: `ENABLED=no` — o ufw está explicitamente
desligado, não é falha de inicialização.

#### RESOLVIDO em 2026-08-15

Firewall ativado com as seguintes regras (verificadas em `sudo ufw status verbose`):

```text
Status: active
Default: deny (incoming), allow (outgoing), disabled (routed)

22/tcp                     ALLOW IN    192.168.15.0/24     # SSH via LAN
22/tcp on tailscale0       ALLOW IN    Anywhere            # SSH via Tailscale
41641/udp                  ALLOW IN    Anywhere            # Tailscale WireGuard
22/tcp (v6) on tailscale0  ALLOW IN    Anywhere (v6)       # SSH via Tailscale
41641/udp (v6)             ALLOW IN    Anywhere (v6)       # Tailscale WireGuard
```

**Decisão tomada:** SSH liberado tanto pela LAN (`192.168.15.0/24`) quanto pela interface
Tailscale — mantém a LAN como acesso de emergência caso o Tailscale falhe, sem abrir
para qualquer origem.

**Efeito prático:** o risco de exposição via IPv6 global (endereço `2804:.../64` da
interface Wi-Fi) está eliminado — qualquer tentativa de acesso à porta 22 por esse
endereço agora cai na política padrão `deny`, pois a regra do IPv6 só existe para a
interface `tailscale0`.

**Procedimento seguido (sem incidentes):**

1. Políticas padrão definidas primeiro (`deny incoming` / `allow outgoing`) —
   sem efeito enquanto o ufw estava desligado.
2. As três regras de liberação adicionadas em seguida, também sem efeito ainda
   (conferidas com `sudo ufw show added` antes de ativar).
3. `sudo ufw enable`, com a sessão SSH original mantida aberta.
4. Validação com uma **segunda** sessão SSH nova, em paralelo — bem-sucedida,
   e passou justamente pela regra `tailscale0` (MagicDNS resolve para o IP Tailscale).

Nenhuma queda de conexão durante o processo.

**Atenção para o futuro:** o Docker manipula `iptables` diretamente e **ignora as regras
do ufw**. Um container publicado com `-p 8080:80` fica acessível mesmo com o ufw bloqueando
a porta 8080. Isso precisa ser tratado explicitamente quando o Docker entrar no
laboratório — é uma das causas mais comuns de exposição acidental de serviço.

---

### ~~P0 — Servidor suspende ao fechar a tampa~~ — RESOLVIDO em 2026-08-15

**Risco original:** o servidor é um notebook Dell Inspiron 3501 e vinha no padrão de
fábrica do `systemd-logind`: `HandleLidSwitch=suspend`. Fechar a tampa suspenderia a
máquina, derrubando Tailscale, SSH e todos os serviços, exigindo presença física para
recuperar.

**Correção aplicada:**

Arquivo criado: `/etc/systemd/logind.conf.d/90-servidor-sem-suspensao.conf`

```ini
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
```

Aplicado com `sudo systemctl restart systemd-logind` (derruba a sessão SSH atual como
efeito colateral esperado — o `logind` gerencia sessões — mas não afeta rede nem `sshd`).

**Validação:**

```bash
busctl get-property org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.login1.Manager HandleLidSwitch
→ s "ignore"   (antes: s "suspend")
```

**Validação física (2026-08-15):** tampa fechada de fato. `tailscale ping srv-ubnt-001`
de outra máquina respondeu normalmente, com conexão **direta** (não via relay):

```text
pong from srv-ubnt-001 (100.96.168.97) via 192.168.15.182:41641 in 120ms
```

Confirmado: o servidor permanece totalmente operacional com a tampa fechada.

**Efeito colateral a monitorar:** com a tampa fechada, a dissipação térmica piora
(a tela apaga mas o hardware continua ativo).

**Monitoramento térmico (2026-08-15), com a tampa fechada:**

Instalado `lm-sensors` (detecção via `sudo sensors-detect --auto`; chip `coretemp`
detectado, confiança 9/10 — módulo carregado na sessão atual, **não** persistido em
`/etc/modules` porque a última pergunta interativa não foi respondida, assumindo o
padrão `NO`. Ver pendência abaixo).

```text
coretemp-isa-0000
Package id 0:  +67.0°C  (crit = 100.0°C)
Core 0:        +67.0°C
Core 1:        +52.0°C

dell_smm-isa-00de
fan1:            0 RPM  (min = 0, max = 4900 RPM)
temp1:         +47.0°C
temp2:         +36.0°C
temp3:         +37.0°C
pwm1:              0%   MANUAL CONTROL

iwlwifi_1-virtual-0
temp1:         +44.0°C
```

**Ponto de atenção — leitura do cooler suspeita.** `fan1: 0 RPM` com controle
`MANUAL` a 0%, mesmo com o package a 67°C, é incomum. Duas hipóteses, ainda não
resolvidas:

1. Bug conhecido do driver `dell_smm-hwmon` em vários modelos Dell: não lê a rotação
   real quando o BIOS/EC controla a ventoinha de forma independente — reporta `0 RPM`
   mesmo com o cooler girando de fato. Inofensivo.
2. O cooler realmente não gira. Seria um problema real numa máquina que ficará ligada
   continuamente com a tampa fechada.

**Verificação física feita (2026-08-15):** confirmado tátil — ar saindo perceptível na
parte inferior da máquina. Somado a: (a) 3 dias ligada continuamente sem aquecimento
anormal, (b) histórico de uso anterior por outro colaborador sem qualquer relato de
problema de refrigeração. **Conclusão: `fan1: 0 RPM` é leitura incorreta do driver
`dell_smm`, não falha real do cooler.** Item considerado resolvido — sem ação de
hardware necessária.

**Persistência do módulo resolvida (2026-08-15):** `/etc/modules` está **obsoleto**
(o próprio arquivo avisa, substituído por `/etc/modules-load.d/`). Criado, em vez disso:

```text
/etc/modules-load.d/coretemp.conf
    coretemp
```

O `systemd-modules-load.service` carrega esse módulo automaticamente a cada boot.
Ainda não testado num reboot real — será validado quando o reboot do P2 (kernel
pendente) acontecer: rodar `sensors` depois e confirmar que `coretemp-isa-0000` aparece
sem precisar rodar `sensors-detect` de novo.

**Pendências deste item:**

- [ ] Reavaliar a temperatura ocasionalmente (`sensors`), sem urgência

**Reversão:** apagar `/etc/systemd/logind.conf.d/90-servidor-sem-suspensao.conf` e rodar
`sudo systemctl restart systemd-logind`.

---

### ~~P1 — Autenticação por senha habilitada no SSH~~ — RESOLVIDO em 2026-08-15

**Risco:** força bruta contra a senha do usuário `ubnt`. Sem firewall (P0 acima), a
origem do ataque pode ser a LAN **ou a internet**, dependendo do resultado da checagem de
exposição.

Confirmado via configuração efetiva (`sudo sshd -T`), não apenas pela mensagem de erro do
cliente:

```text
passwordauthentication yes
permitrootlogin       prohibit-password   ← root por chave ainda é permitido
x11forwarding         yes                 ← desnecessário, servidor headless
maxauthtries          6
```

**Correção prevista:** drop-in em `/etc/ssh/sshd_config.d/` com:

```text
PasswordAuthentication no
PermitRootLogin no
X11Forwarding no
```

**Pré-requisito obrigatório:** confirmar que a autenticação por chave funciona **antes**
de desativar a senha. Já está confirmada nesta data. Ainda assim, seguir o procedimento
de alteração segura descrito em [ssh.md](ssh.md) seção 6 — com sessão aberta em
paralelo.

**Risco da mudança:** se a chave falhar depois de desativar a senha, o acesso remoto se
perde e a recuperação exige teclado e monitor no servidor.

#### Execução e um problema real encontrado no caminho

Criado `/etc/ssh/sshd_config.d/90-hardening.conf` com `PasswordAuthentication no`,
`PermitRootLogin no`, `X11Forwarding no`. Sintaxe validada (`sudo sshd -t`), `sshd`
recarregado (`systemctl reload ssh`, não `restart` — não derruba sessões existentes).

**Primeira tentativa não funcionou.** Teste específico de que a senha não seria mais
aceita:

```bash
ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no -o BatchMode=yes ubnt@srv-ubnt-001
→ Permission denied (publickey,password)   ← "password" ainda na lista!
```

`sudo sshd -T | grep passwordauth` confirmou: `passwordauthentication yes`, mesmo com
o `90-hardening.conf` dizendo `no`.

**Causa raiz — comportamento não intuitivo do `sshd_config`:** diferente de quase todo
outro arquivo de configuração Linux, no `sshd_config` **a primeira ocorrência de uma
diretiva vence; ocorrências posteriores da mesma diretiva são ignoradas em silêncio**,
sem erro nem aviso. O `Include /etc/ssh/sshd_config.d/*.conf` expande os arquivos em
ordem alfabética:

```text
50-cloud-init.conf   → PasswordAuthentication yes   ← lido primeiro, vence
90-hardening.conf    → PasswordAuthentication no    ← lido depois, ignorado
```

O `50-cloud-init.conf` foi criado pelo cloud-init na primeira inicialização do servidor
(garante acesso por senha antes de qualquer chave existir) e continuava vencendo mesmo
depois de já termos chave configurada.

**Correção:** sobrescrito o conteúdo de `50-cloud-init.conf` para `PasswordAuthentication no`
diretamente, eliminando a contradição na origem, mantendo `90-hardening.conf` como registro
explícito da decisão de hardening (mesmo que redundante hoje).

**Atenção para o futuro:** se este servidor for reprovisionado do zero e o `cloud-init`
rodar de novo, ele pode recriar `50-cloud-init.conf` com `yes`. Conferir com
`sudo sshd -T | grep passwordauth` depois de qualquer reprovisionamento.

**Validação final, depois da correção:**

```text
ssh ubnt@srv-ubnt-001 'echo CONEXAO_OK'                                    → funciona (chave)
ssh -o PreferredAuthentications=password ... ubnt@srv-ubnt-001            → Permission denied (publickey)
```

A lista de métodos não inclui mais `password` — confirmado.

---

### ~~P2 — SSH escutando em todas as interfaces~~ — DECISÃO TOMADA em 2026-08-15: mitigado, não eliminado

`ss -tulnp` mostra `0.0.0.0:22` e `[::]:22` — o `sshd` continua fazendo bind em todas as
interfaces. Isso, isoladamente, significaria que qualquer dispositivo da LAN alcança a
porta 22 antes de qualquer outra verificação.

**Opções avaliadas:**

| Opção | Como | Risco |
|---|---|---|
| `ListenAddress` fixo (ex.: só IP Tailscale) | `sshd` só abre socket naquele IP | se o IP mudar (LAN/DHCP) ou a interface subir atrasada no boot (Tailscale), o **`sshd` falha ao iniciar** — não é "menos acessível", é "fora do ar" |
| Filtrar por `ufw` (já feito) | firewall filtra pacotes depois que o `sshd` já está de pé | não afeta a inicialização do serviço; IP mudando ou interface atrasando não derruba o SSH |

**Decisão: manter `ListenAddress` no padrão (todas as interfaces) e confiar no `ufw`.**

**Racional:** `ListenAddress` faz bind num IP específico — se esse IP não existir no
momento em que o `sshd` inicia (interface ainda subindo, ou IP mudou por DHCP), o
serviço **não sobe**, exigindo acesso físico para corrigir. Isso trocaria um risco de
segurança (superfície um pouco maior) por um risco de disponibilidade do próprio SSH —
o pior tipo de troca possível neste laboratório, onde SSH é o único canal de
administração remota.

O `ufw`, já configurado, cobre o mesmo objetivo de forma mais robusta: filtra por origem
(IP/interface) **depois** que o socket já está aberto, então mudança de IP ou atraso na
subida de interface não afeta a disponibilidade do serviço — só o próprio filtro, que é
reavaliado a cada pacote.

**Status final: risco mitigado pelo `ufw` (SSH só alcançável via LAN ou Tailscale),
não eliminado na camada do `sshd`. Aceito conscientemente — o item permanece
documentado, não é uma pendência esquecida.**

---

### ~~P2 — Chave de acesso única, sem plano de recuperação~~ — RESOLVIDO em 2026-08-15

**Risco original:** existia **uma** chave em `authorized_keys`, associada só ao notebook
`NTB-UBUNTU`. Se o notebook fosse perdido, roubado ou reinstalado sem backup, o acesso
remoto ao servidor acabaria — restando só teclado e monitor físicos.

**Correção aplicada:** gerado um segundo par de chaves, **independente** do par principal
(mesmo algoritmo ed25519), especificamente para recuperação:

```text
~/.ssh/id_ed25519_recovery       (privada — protegida por passphrase própria)
~/.ssh/id_ed25519_recovery.pub   (pública — adicionada ao authorized_keys do servidor)
```

**Por que uma chave separada, e não backup da chave principal:** permite revogar uma sem
afetar a outra. Se um dia a chave do notebook precisar ser revogada (ex.: notebook
comprometido), a chave de recuperação continua íntegra — desde que ela não esteja
guardada no mesmo lugar comprometido.

**Por que com passphrase, diferente da chave principal:** a chave principal fica em uso
corrente no notebook, sem passphrase, para permitir automação (é o que usamos em toda
esta sessão). A de recuperação fica guardada, não em uso diário — uma camada extra de
proteção (passphrase) faz sentido, pois protege contra o cenário de o local de
armazenamento externo ser comprometido.

**Onde a chave privada foi guardada:** no Bitwarden, pasta `Laboratório DevOps`, como
Nota Segura — **fora do notebook**. Confirmado o salvamento, a cópia local do arquivo
(`~/.ssh/id_ed25519_recovery`) foi **removida do disco do notebook** (`rm`, 2026-08-15),
mantendo só a chave pública (`.pub`, não sensível) como referência. Isso preserva o
propósito real da chave: se o notebook for perdido, comprometido ou reinstalado, a
chave de recuperação continua acessível de qualquer dispositivo com acesso à conta do
Bitwarden — e não corre o risco de ser comprometida junto com o notebook.

**Adicionada ao servidor sem remover a chave existente** — `authorized_keys` agora tem
duas entradas: `joao@NTB-UBUNTU` (uso diário) e `recovery-srv-ubnt-001` (emergência).
Permissões conferidas, continuam `600`.

**Validado:** login de teste com `ssh -i ~/.ssh/id_ed25519_recovery ubnt@srv-ubnt-001`
funcionou (após digitar a passphrase), confirmando a chave ativa no servidor.

**Quando usar esta chave:** só em caso de perda, dano ou reinstalação do notebook
`NTB-UBUNTU` — quando a chave principal (`~/.ssh/id_ed25519`) não estiver mais
disponível. Uso normal do dia a dia continua sendo a chave principal.

Ficha de referência rápida em [servidor.md](servidor.md), seção "Chave de recuperação".

Não versionar nenhuma chave privada em hipótese alguma, inclusive neste repositório.

---

### ~~P2 — Kernel desatualizado, reboot pendente~~ — RESOLVIDO em 2026-08-15

**Situação original:** `/var/run/reboot-required.pkgs` listava `libc6`,
`linux-image-7.0.0-29-generic` e `linux-base` — já baixados pelo `unattended-upgrades`,
mas sem efeito até reiniciar. O servidor rodava o kernel antigo (`7.0.0-14`) há mais de
1 dia e 16h.

**Ação:** `sudo reboot`, executado deliberadamente também como **teste de resiliência** —
confirmar que tudo o que configuramos volta sozinho, sem intervenção manual, antes que
isso precisasse ser descoberto numa queda de energia real.

**Resultado, checklist completo pós-reboot:**

| Item | Verificado | Resultado |
|---|---|---|
| Kernel novo em vigor | `uname -r` | `7.0.0-29-generic` (era `7.0.0-14`) |
| Uptime reiniciado | `uptime -p` | `up 6 minutes` |
| SSH remoto sem intervenção | `ssh ubnt@srv-ubnt-001` | funcionou de primeira, por chave |
| Tailscale | `tailscaled` + `tailscale status` | ativo, conexão direta com o notebook restabelecida |
| Firewall | `sudo ufw status verbose` | `active`, as 5 regras idênticas às configuradas |
| Tampa não suspende | `busctl get-property ... HandleLidSwitch` | `"ignore"` — persistiu |
| Sensor de temperatura | `sensors` | `coretemp-isa-0000` presente, carregado sozinho via `/etc/modules-load.d/coretemp.conf` |

**Nenhum item precisou de correção manual.** Todo o hardening feito nesta sessão
(firewall, tampa, persistência de módulo) sobrevive a um boot completo — validado, não
apenas presumido.

---

### ~~P1 — Docker contornando o `ufw`~~ — RESOLVIDO parcialmente em 2026-08-16

**Risco encontrado:** ao publicar a primeira aplicação via Docker Compose (porta 8000,
projeto [contador-visitas](../projects/contador-visitas/)), confirmou-se que o Docker
manipula `iptables` diretamente, contornando por completo as regras do `ufw`. A porta
ficou acessível de **qualquer origem da rede**, mesmo com o `ufw` negando tudo por
padrão — risco idêntico ao que já tínhamos eliminado para o SSH, agora reaberto por
uma superfície diferente (containers).

**Correção aplicada:** regras na chain `DOCKER-USER` (mecanismo oficial do Docker,
avaliado antes das regras automáticas dele), liberando só Tailscale e a LAN de casa,
com `DROP` para qualquer outra origem — mesmo modelo de acesso já usado no `ufw` para
o SSH. Detalhes técnicos completos em [docker.md](docker.md), seção 7.

**Pendência restante:** as regras foram aplicadas ao vivo (`iptables -A ...`) e **não
sobrevivem a um reboot** ainda — falta instalar `iptables-persistent` e validar com um
reboot real. Até isso ser feito, um reboot do servidor reabre o risco original.

**Vale para todo projeto futuro:** qualquer novo container que publicar porta precisa
ser conferido contra esse mesmo problema — o `ufw` sozinho nunca vai proteger portas
publicadas pelo Docker.

---

### 🔴 P0 (NOVO, regressão) — `ufw` removido pelo `iptables-persistent`, SSH sem persistência de firewall

**Introduzido em 2026-08-19**, durante a instalação do `iptables-persistent` (para
finalmente resolver a pendência antiga de persistir as regras `DOCKER-USER`). Os dois
pacotes conflitam nesta versão do Ubuntu — instalar um removeu o outro (`ufw`).

**Estado atual (verificado nesta data):**

- As regras do `ufw` que protegiam o SSH (só LAN `192.168.15.0/24` + interface
  `tailscale0`) **continuam ativas no kernel agora** — confirmado via
  `sudo iptables -L INPUT -n -v`, contadores de pacotes não-zerados nas chains
  `ufw-before-input`/`ufw-after-input`. **O servidor está protegido neste momento.**
- **Não sobrevivem a um reboot.** O serviço `ufw.service` que as recarregaria não
  existe mais (pacote removido), e o `netfilter-persistent save` gravou essas chains
  **vazias** em `/etc/iptables/rules.v4` (confirmado: `grep "^-A ufw"` não retorna
  nada — só as chains foram declaradas, sem as regras de verdade dentro).
- Reboot antes da correção = SSH volta a escutar sem restrição de origem em
  `0.0.0.0/0` (mesmo risco do IPv6 global que já resolvemos uma vez, reaberto).

**Avaliação de risco imediato (2026-08-19, antes de pausar a sessão):** baixo — nenhum
reboot está planejado, e o `unattended-upgrades` não reinicia automaticamente por
padrão. Risco residual só por causa física (queda de energia), fora de controle e
preexistente a este incidente.

**Plano combinado para a próxima sessão:** migrar a proteção do SSH de `ufw` para
regras `iptables` puras na chain `INPUT` (mesma lógica: liberar LAN + `tailscale0` +
conexões estabelecidas, `DROP` no resto), unificando tudo sob o `iptables-persistent`
em vez de dois mecanismos conflitantes. **Não fazer reboot do servidor antes dessa
correção estar aplicada e validada.**

Detalhes técnicos completos em [docker.md](docker.md), seção 7.

---

### P3 — Itens de higiene

- [ ] Criar `~/.ssh/config` no notebook (alias, usuário e chave explícitos)
- [ ] Avaliar passphrase na chave privada + `ssh-agent`
- [ ] Definir estratégia de backup (o servidor ainda não tem dados, mas terá)
- [ ] IP de LAN fixo (ver [rede.md](rede.md))
- [ ] Migrar de Wi-Fi para cabo
- [ ] Revisar periodicamente os dispositivos autorizados no tailnet
- [ ] Instalar `iptables-persistent` e validar as regras `DOCKER-USER` após reboot

## 3. Princípios adotados

- **Menor privilégio:** serviços rodam com o usuário mínimo necessário; `root` só via `sudo`.
- **Nada de segredo em repositório:** senhas, tokens e chaves ficam fora do Git — ver `.gitignore`.
- **Segurança antes da conveniência:** não expor serviço na internet sem entender o que
  está sendo exposto, para quem e com qual autenticação.
- **Toda mudança de risco tem plano de reversão documentado antes de ser executada.**
- **Tailscale ativo não significa servidor seguro.** Ele resolve conectividade, não
  hardening do sistema operacional.

## 4. Registro de alterações

| Data | Alteração |
|---|---|
| 2026-08-15 | Auditoria inicial somente-leitura. Nenhuma configuração do servidor foi alterada. Riscos catalogados. |
| 2026-08-15 | Correção: `ufw` estava registrado como "ativo" com base em `systemctl is-active`, o que é enganoso para units `oneshot`. `sudo ufw status verbose` confirmou `Status: inactive` — o firewall não está aplicando nenhuma regra. Reclassificado como P0, combinado com a exposição em IPv6 global. Confirmado também, via `sshd -T`, que `passwordauthentication yes` e reboot pendente com kernel novo já instalado. |
| 2026-08-15 | **P0 da tampa resolvido.** Drop-in `90-servidor-sem-suspensao.conf` criado, `systemd-logind` reiniciado, `HandleLidSwitch=ignore` confirmado via `busctl`, validado fisicamente. Cooler a `0 RPM` avaliado como leitura incorreta do driver `dell_smm` (hardware funcionando). Módulo `coretemp` persistido via `/etc/modules-load.d/coretemp.conf` (o `/etc/modules` clássico está obsoleto). |
| 2026-08-15 | **P0 do firewall resolvido.** `ufw` ativado com política padrão `deny incoming` / `allow outgoing`, SSH liberado para a LAN (`192.168.15.0/24`) e para a interface `tailscale0` (IPv4 e IPv6), porta 41641/UDP liberada para o Tailscale. Validado com segunda sessão SSH em paralelo, sem incidentes. |
| 2026-08-15 | **P1 da senha no SSH resolvido.** `PasswordAuthentication no`, `PermitRootLogin no`, `X11Forwarding no` aplicados via `/etc/ssh/sshd_config.d/90-hardening.conf`. Encontrado e corrigido um problema real: `50-cloud-init.conf` (lido antes, por ordem alfabética) já definia `PasswordAuthentication yes`, e no `sshd_config` a **primeira** ocorrência de uma diretiva vence — nossa diretiva estava sendo ignorada em silêncio. Corrigido sobrescrevendo o valor no próprio `50-cloud-init.conf`. Validado: chave continua funcionando, senha explicitamente recusada (`Permission denied (publickey)`, sem `password` na lista). |
| 2026-08-15 | **P2 do reboot resolvido.** `sudo reboot` executado como teste de resiliência. Checklist completo pós-boot: kernel `7.0.0-29-generic` em vigor, SSH/Tailscale/ufw/tampa/sensor de temperatura — todos voltaram sozinhos, sem intervenção manual. |
| 2026-08-15 | **P2 da ausência de chave de recuperação resolvido.** Gerado par de chaves independente (`id_ed25519_recovery`, com passphrase), chave pública adicionada ao `authorized_keys` do servidor (sem remover a existente), chave privada guardada no gerenciador de senhas do usuário, fora do notebook. Testado login funcional com a chave nova. `ListenAddress` avaliado e mantido no padrão por decisão consciente (ver item anterior), confiando no `ufw`. |
| 2026-08-16 | **Docker instalado** via repositório oficial e **primeiro projeto Compose** publicado (contador-visitas). **Risco real encontrado:** Docker contorna o `ufw`, expondo a porta 8000 a qualquer origem. **Corrigido parcialmente** com regras na chain `DOCKER-USER` (Tailscale + LAN liberados, resto em `DROP`) — persistência após reboot ainda pendente. |
| 2026-08-19 | Nextcloud instalado. **Segundo problema real encontrado:** faltava regra `ESTABLISHED,RELATED` na chain `DOCKER-USER` — o tráfego de retorno do container caía no `DROP`, causando timeout no acesso. Corrigido. Ao instalar `iptables-persistent` para finalmente persistir essas regras, **`ufw` foi removido pelo `apt`** (pacotes conflitantes). SSH continua protegido *ao vivo* (regras ainda no kernel), mas **não sobreviveria a um reboot** — persistência do `ufw` ficou vazia. Reclassificado como **P0 novo**. Plano: migrar SSH para `iptables` puro na próxima sessão, antes de qualquer reboot. |
