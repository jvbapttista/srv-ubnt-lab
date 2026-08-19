# Servidor `srv-ubnt-001` — ficha técnica

**Este é o documento de referência rápida do servidor.** Para o "porquê" e o
raciocínio por trás de cada configuração, ver os documentos específicos linkados
em cada seção. Aqui fica o "o que é e como uso", sempre atualizado.

Última atualização: **2026-08-15**

---

## 1. Identificação

| Item | Valor |
|---|---|
| Hostname | `srv-ubnt-001` |
| Propósito | Servidor do laboratório DevOps — hospeda serviços, containers e aplicações de estudo |
| Hardware | Dell Inspiron 3501 (notebook reaproveitado como servidor) |
| SO | Ubuntu 26.04 LTS (Server, sem interface gráfica) |
| Localização física | Rede doméstica do João, sempre ligado, tampa fechada |
| IP LAN | `192.168.15.182` (Wi-Fi, via DHCP — pode mudar, ver [rede.md](rede.md)) |
| IP Tailscale | `100.96.168.97` (fixo, é o que se usa no dia a dia) |
| Usuário administrativo | `ubnt` (grupo `sudo`) |

Detalhes de hardware (CPU, RAM, disco) em [inventario.md](inventario.md).

---

## 2. Como logar

```bash
ssh ubnt@srv-ubnt-001
```

Funciona a partir do notebook `NTB-UBUNTU` (ou qualquer outro dispositivo autorizado
no tailnet), por chave SSH, sem senha — a autenticação por senha está **desativada**.
O nome `srv-ubnt-001` é resolvido automaticamente pelo MagicDNS do Tailscale.

Se o comando acima não resolver o nome, usar o IP Tailscale diretamente:

```bash
ssh ubnt@100.96.168.97
```

Acesso pela LAN (rede de casa) também funciona, como caminho alternativo:

```bash
ssh ubnt@192.168.15.182
```

> O IP de LAN é dinâmico (DHCP) e pode mudar — se parar de funcionar, confirmar o IP
> atual com `tailscale status` a partir de outra máquina do tailnet, ou olhando o
> roteador.

Detalhes de autenticação, chaves e hardening em [ssh.md](ssh.md).
Problemas de conexão: ver [troubleshooting.md](troubleshooting.md).

### Chave de recuperação (acesso de emergência)

**Por que existe:** o acesso normal ao servidor depende de uma única chave privada,
guardada só no notebook `NTB-UBUNTU` (`~/.ssh/id_ed25519`). Se o notebook for perdido,
danificado ou reinstalado sem backup, essa chave desaparece junto — e sem ela, o único
jeito de entrar no servidor seria fisicamente, com teclado e monitor.

Para não depender só disso, foi criado um **segundo par de chaves, independente**,
pensado exclusivamente para esse cenário de emergência.

| Item | Detalhe |
|---|---|
| Chave privada | **não fica no notebook** — guardada só no Bitwarden (removida do disco em 2026-08-15) |
| Chave pública (referência) | `~/.ssh/id_ed25519_recovery.pub`, ainda no notebook — não é sensível |
| Protegida por | passphrase própria (diferente da chave principal, que não tem) |
| Cadastrada no servidor como | `recovery-srv-ubnt-001` em `~/.ssh/authorized_keys` |
| Onde a chave privada está guardada | Bitwarden, pasta `Laboratório DevOps`, item "SSH Recovery Key - srv-ubnt-001" |
| Criada em | 2026-08-15 |

**Quando usar esta chave:** só se a chave principal do notebook não estiver mais
disponível — notebook perdido, roubado, com o disco corrompido, ou reinstalado do zero
sem ter feito backup da chave principal antes. **No dia a dia, continue usando o acesso
normal** (`ssh ubnt@srv-ubnt-001`, seção anterior) — não há motivo para usar a chave de
recuperação em uso corrente.

**Como usar, quando precisar** (a chave privada não está mais no notebook — foi
removida do disco em 2026-08-15 depois de confirmado o backup no Bitwarden):

1. Abrir o item "SSH Recovery Key - srv-ubnt-001" no Bitwarden, no dispositivo que você
   tiver disponível (não precisa ser o notebook original).
2. Copiar o conteúdo da chave privada (campo de notas) para um arquivo novo, por
   exemplo `~/.ssh/id_ed25519_recovery`.
3. Ajustar a permissão do arquivo: `chmod 600 ~/.ssh/id_ed25519_recovery`.
4. Conectar especificando essa chave:
   ```bash
   ssh -i ~/.ssh/id_ed25519_recovery ubnt@srv-ubnt-001
   ```
5. Vai pedir a passphrase salva no mesmo item do Bitwarden — sem ela, a chave sozinha
   não autentica.

**Por que uma chave separada em vez de só um backup da principal:** permite revogar uma
sem afetar a outra. Se um dia a chave do notebook precisar ser invalidada (por exemplo,
notebook comprometido), a de recuperação continua funcionando — desde que o gerenciador
de senhas em si não tenha sido comprometido junto.

**Nunca:** colar o conteúdo da chave privada em chat, documento, ou qualquer lugar que
não seja o gerenciador de senhas. A chave pública (`.pub`) não é sensível e pode
circular livremente — é o que fica em `authorized_keys` no servidor.

Racional completo e histórico da decisão em [seguranca.md](seguranca.md).

---

## 3. Tailscale — como o acesso remoto funciona

O servidor faz parte de uma rede privada Tailscale (WireGuard), que é o caminho usado
para alcançá-lo sem expor a porta SSH na internet.

| Item | Valor |
|---|---|
| Dispositivo no tailnet | `srv-ubnt-001` |
| IP Tailscale (IPv4) | `100.96.168.97` |
| Dispositivos autorizados hoje | `ntb-ubuntu` (notebook do João) e o próprio servidor |
| MagicDNS | ativo — permite usar o hostname em vez do IP |

Comandos do dia a dia:

```bash
tailscale status          # lista dispositivos do tailnet e tipo de conexão
tailscale ping srv-ubnt-001   # testa conectividade e mostra se é direta ou via relay
```

Documentação completa (conceitos, ACLs, troubleshooting) em [tailscale.md](tailscale.md).

---

## 4. O que roda hoje no servidor

| Serviço | Status | Observação |
|---|---|---|
| SSH (`ssh.socket`) | ativo, inicia no boot | único ponto de administração |
| Tailscale (`tailscaled`) | ativo, inicia no boot | camada de acesso remoto |
| Firewall (`ufw`) | ativo | libera SSH só via LAN e Tailscale — ver [seguranca.md](seguranca.md) |
| `lm-sensors` | instalado | monitoramento de temperatura sob demanda (`sensors`) |
| `unattended-upgrades` | ativo | atualizações de segurança automáticas |
| Docker | ativo, `v29.7.2` + Compose `v5.4.0` | instalado via repo oficial em 2026-08-16, ver [docker.md](docker.md) |

Esta tabela é atualizada conforme novos serviços/projetos entrarem.

---

## 5. Diretórios — onde tudo fica

### No servidor

Hoje o servidor não tem nenhum diretório de projeto próprio — ainda não hospeda nada.
Conforme formos instalando Docker, subindo containers e hospedando projetos, esta
seção vai listar, para cada aplicação, exatamente onde os arquivos vivem no servidor.

Modelo que será seguido (a definir na prática quando o primeiro projeto chegar):

```text
/opt/<nome-do-projeto>/        arquivos de execução (docker-compose.yml, etc.)
/opt/<nome-do-projeto>/data/   dados persistentes (volumes), fora do Git
```

`/opt` é o caminho convencional do Linux para software de terceiros/aplicações que não
vêm do gerenciador de pacotes da distribuição — por isso a escolha, quando chegarmos lá.

### No notebook (`NTB-UBUNTU`) — raiz do laboratório

Toda a documentação, scripts e configuração versionável do laboratório ficam em:

```text
/home/joao/Documentos/SRV_UBNT/
├── README.md                  índice geral
├── docs/                      documentação técnica da infraestrutura
│   ├── arquitetura.md
│   ├── inventario.md
│   ├── rede.md
│   ├── ssh.md
│   ├── tailscale.md
│   ├── seguranca.md
│   ├── docker.md
│   ├── servidor.md            ← este arquivo
│   └── troubleshooting.md
├── notes/                     código explicado, bloco por bloco (estudo/referência)
│   └── README.md
├── projects/                  código funcional de cada projeto hospedado
│   └── filehub/               (em fase de arquitetura — ver docs/filehub-arquitetura.md)
└── scripts/                   (a criar conforme necessário)
```

**Nota:** não existe pasta `docker/` própria — cada projeto carrega seu próprio
`Dockerfile`/`docker-compose.yml` dentro de `projects/<nome>/`, e a documentação
conceitual do Docker fica centralizada em [docker.md](docker.md).

Por que a raiz fica no notebook e não no servidor: ver a decisão registrada em
[arquitetura.md](arquitetura.md), seção 3.

---

## 6. Aplicações e projetos hospedados

*(Nenhum ainda no ar. O projeto "Contador de Visitas" foi cancelado em 2026-08-16 —
serviu de aprendizado de Docker Compose, mas não agregava valor de portfólio. O
achado de segurança que ele revelou (Docker contorna o `ufw`) e a correção via
`DOCKER-USER` continuam válidos e documentados em [seguranca.md](seguranca.md).)*

**Projeto atual: FileHub** — plataforma pessoal de armazenamento de arquivos, em fase
de arquitetura. Ver [`docs/filehub-arquitetura.md`](filehub-arquitetura.md) e
[`projects/filehub/`](../projects/filehub/).

Modelo para as próximas entradas, quando o FileHub (ou outro projeto) for hospedado:

```markdown
### <nome do projeto>

- **O que é:** breve descrição
- **Por que existe:** o que ele ensina/serve no laboratório
- **Onde vive no servidor:** caminho completo
- **Onde vive no repositório:** `projects/<nome>/`
- **Código explicado bloco a bloco:** `notes/<nome>/`
- **Como iniciar:** comando(s)
- **Como parar:** comando(s)
- **Portas usadas:** lista
- **Como acessar:** URL/IP:porta
- **Dependências:** o que precisa estar rodando antes
- **Documentação própria:** link para `projects/<nome>/README.md`, se houver
```

---

## 7. Estado das pendências de segurança

Resumo rápido — detalhes completos, riscos e como cada um foi resolvido em
[seguranca.md](seguranca.md):

- [x] Servidor não suspende mais ao fechar a tampa
- [x] Firewall ativo (SSH liberado só para LAN e Tailscale)
- [x] Autenticação por senha desativada no SSH
- [x] Reboot feito — kernel `7.0.0-29-generic` em vigor, checklist pós-boot 100% ok
- [x] SSH escutando em todas as interfaces — decisão consciente de manter assim, mitigado pelo `ufw` (restringir o bind arriscaria o SSH não subir no boot)
- [x] Chave de recuperação criada e guardada fora do notebook (ver seção 2)
- [ ] IP de LAN fixo
- [ ] Migrar de Wi-Fi para cabo

---

## 8. Registro de alterações deste documento

| Data | Alteração |
|---|---|
| 2026-08-15 | Criado como ficha técnica central do servidor, consolidando o estado após a primeira rodada de hardening (tampa, firewall, SSH). |
