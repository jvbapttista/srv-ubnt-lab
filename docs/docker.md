# Docker

Última atualização: **2026-08-16**

## 1. O que é, conceitualmente

Docker empacota uma aplicação junto com tudo que ela precisa para rodar (bibliotecas,
dependências, configuração), como uma unidade isolada e portátil — resolve o clássico
"funciona na minha máquina, mas não no servidor".

| Termo | O que é |
|---|---|
| **Imagem** | Um "molde" read-only com tudo que a aplicação precisa. Não roda sozinha. |
| **Container** | Uma instância em execução de uma imagem. |
| **Dockerfile** | Receita de como construir uma imagem, passo a passo. |
| **Docker daemon** (`dockerd`) | Processo em segundo plano que gerencia containers/imagens de verdade. |
| **Docker CLI** (`docker`) | O comando que você digita — só conversa com o daemon. |
| **Registry** (Docker Hub) | Repositório de imagens prontas, de onde se baixa (`pull`) imagens públicas. |

**Diferença de uma VM:** um container não tem kernel próprio — compartilha o kernel do
hospedeiro (`srv-ubnt-001`), isolado via dois mecanismos do próprio Linux:
- **namespaces** — isolam o que o container *enxerga* (processos, rede, filesystem).
- **cgroups** — limitam quanto de CPU/memória/disco ele pode *usar*.

Por isso containers são muito mais leves e rápidos de iniciar que uma VM.

## 2. Instalação — o que foi feito

Instalado via **repositório oficial do Docker** (não o pacote `docker.io` da distro),
para ter a versão mais recente e o plugin do Compose já integrado.

### Passo a passo executado

```bash
sudo apt-get install -y ca-certificates curl          # pré-requisitos (já estavam presentes)

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc            # chave GPG oficial do Docker

# /etc/apt/sources.list.d/docker.list:
deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu resolute stable

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### O que cada pacote instalado é

| Pacote | Função |
|---|---|
| `docker-ce` | Motor do Docker (Community Edition) — o daemon |
| `docker-ce-cli` | Comando `docker` |
| `containerd.io` | Runtime de baixo nível que efetivamente cria/executa containers |
| `docker-buildx-plugin` | Construção de imagens (usado com `docker build`/`docker buildx`) |
| `docker-compose-plugin` | Compose v2, ativado como `docker compose` (sem hífen) |

### Problema encontrado no caminho

Ao gerar o arquivo do repositório dinamicamente com `$(. /etc/os-release && echo
"$VERSION_CODENAME")` dentro de uma string já entre aspas duplas do `ssh`, o escape das
aspas internas (`\"..\"`) fez o valor final ficar `"resolute"` **com aspas literais
dentro do arquivo** — o que o `apt` não reconhece como nome de código válido. Corrigido
reescrevendo o arquivo com o valor já resolvido, sem aspas:

```text
deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu resolute stable
```

**Lição:** ao gerar arquivos de configuração via comando remoto com múltiplos níveis de
aspas (`ssh '...' com aspas duplas dentro`), sempre conferir o conteúdo final do arquivo
gerado antes de assumir que o comando funcionou — erro de escaping não gera mensagem de
erro, só um valor sutilmente errado.

### Ubuntu 26.04 ("resolute") já suportado

Por ser uma versão de Ubuntu recente, havia risco do repositório oficial do Docker ainda
não ter pacotes publicados para `resolute` (cenário em que seria preciso usar `noble`,
24.04, como substituto temporário). Não foi necessário — o `apt-get update` já retornou
`InRelease` para `resolute` sem erro.

## 3. Estado atual

| Item | Valor |
|---|---|
| Versão Docker | `29.7.2` (build `a7dcaa6`) |
| Versão Compose | `v5.4.0` (plugin, comando `docker compose`) |
| Serviço `docker` | `active`, `enabled` (sobe sozinho no boot) |
| Teste `hello-world` | executado com sucesso em 2026-08-16 |
| Dados do Docker | `/var/lib/docker/` (imagens, containers, volumes) |
| Config do daemon | `/etc/docker/` |

## 4. Decisão: grupo `docker` — mantido **sem** o usuário `ubnt`

**O que o grupo `docker` faria:** permitiria rodar `docker ...` sem `sudo`.

**Por que decidimos não usar:** pertencer ao grupo `docker` **equivale a acesso root**
na prática, não é uma permissão limitada. O daemon roda como `root`, e qualquer membro
do grupo pode montar o filesystem real do host dentro de um container:

```bash
docker run -v /:/mnt --rm -it ubuntu chroot /mnt   # shell como root no host, sem sudo
```

**Decisão tomada:** continuar usando `sudo docker ...` para todo comando — mantém o
mesmo nível de proteção que já existe hoje (root exige senha), em troca de um pouco
mais de digitação. Coerente com a postura de segurança adotada no resto do laboratório.

## 5. Comandos do dia a dia

```bash
sudo docker ps                    # containers em execução
sudo docker ps -a                 # todos os containers (inclusive parados)
sudo docker images                # imagens baixadas/construídas localmente
sudo docker run hello-world       # testar que tudo funciona
sudo docker compose version       # confirmar o plugin do Compose
sudo systemctl status docker      # status do serviço
```

## 6. Onde as aplicações vão viver (a definir na prática)

Ainda sem nenhuma aplicação hospedada. Modelo previsto (ver [servidor.md](servidor.md)):

```text
/opt/<nome-do-projeto>/        docker-compose.yml e arquivos de execução
/opt/<nome-do-projeto>/data/   dados persistentes (volumes), fora do Git
```

## 7. Docker e o `ufw` — problema real encontrado e resolvido

Confirmado na prática em 2026-08-16, com o primeiro projeto ([contador de
visitas](../projects/contador-visitas/)): o Docker manipula `iptables` **diretamente**,
contornando as regras do `ufw`. Publicar a porta 8000 (`ports: "8000:5000"` no Compose)
tornou a aplicação acessível de **qualquer origem da rede**, mesmo com o `ufw`
configurado para negar tudo por padrão — confirmado com:

```bash
sudo iptables -L DOCKER -n
# ACCEPT tcp -- 0.0.0.0/0  <IP-do-container>  tcp dpt:5000
```

### Correção aplicada: chain `DOCKER-USER`

O Docker reserva uma chain específica, `DOCKER-USER`, avaliada **antes** das regras
automáticas do Docker — é o mecanismo oficial para o usuário reprender controle sobre
o que alcança containers, sem precisar de ferramentas de terceiros (ex.: `ufw-docker`).

```bash
sudo iptables -A DOCKER-USER -i tailscale0 -j ACCEPT        # Tailscale, sempre liberado
sudo iptables -A DOCKER-USER -s 192.168.15.0/24 -j ACCEPT   # LAN de casa
sudo iptables -A DOCKER-USER -j DROP                         # qualquer outra origem
```

**Ordem importa:** `iptables` avalia regras em sequência e para na primeira que casar.
As liberações (`ACCEPT`) precisam vir antes do bloqueio geral (`DROP`), que deve ser a
**última** regra da chain.

Validado com `sudo iptables -L DOCKER-USER -n -v --line-numbers` — ordem confirmada
correta (tailscale0 → LAN → DROP).

### Segundo problema real: faltava regra para o tráfego de RETORNO

Ao publicar o Nextcloud (porta 8080) em 2026-08-19, o acesso via Tailscale/navegador
travava indefinidamente (timeout), mesmo com as regras acima aparentemente corretas.
Diagnóstico com uma regra `LOG` temporária na chain revelou a causa: as regras só
liberavam o tráfego de **entrada** (por interface/origem), mas a **resposta** do
container (`SYN ACK` voltando pro cliente) tem origem no bridge do Docker
(`br-...`), não bate com nenhuma regra de liberação, e caía no `DROP` final.

**Correção:** adicionar uma regra de conexão **estabelecida**, no topo da chain —
padrão universal para qualquer firewall com estado:

```bash
sudo iptables -I DOCKER-USER 1 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

**Lição geral:** toda regra de "aceitar só de tal origem" precisa vir acompanhada de uma
regra "aceitar retorno de conexões já estabelecidas" — sem isso, a resposta do próprio
serviço fica bloqueada, mesmo com o pedido original tendo sido aceito.

Ordem final correta, validada com `sudo iptables -L DOCKER-USER -n -v --line-numbers`:

```text
1  ACCEPT  ctstate RELATED,ESTABLISHED
2  ACCEPT  in tailscale0
3  ACCEPT  from 192.168.15.0/24
4  DROP    tudo o resto
```

### ⚠️ Terceiro problema real: `iptables-persistent` removeu o `ufw`

Ao instalar `iptables-persistent` (2026-08-19) para finalmente persistir as regras
acima, o `apt` **removeu o pacote `ufw`** como parte da mesma transação — os dois
pacotes conflitam nesta versão do Ubuntu (26.04 "resolute"), aparentemente por ambos
tentarem gerenciar a persistência de regras do `iptables` à sua maneira.

**Risco:** as regras do `ufw` que protegiam o SSH (só LAN + Tailscale) continuam **ativas
no kernel neste exato momento** (remover o pacote não flusha regras já carregadas), mas
**não sobreviveriam a um reboot** — o serviço que as recarregaria (`ufw.service`) não
existe mais, e o `netfilter-persistent save` salvou as chains do `ufw` **vazias**
(confirmado via `grep "^-A ufw" /etc/iptables/rules.v4` — nenhum resultado), só as
regras `DOCKER-USER` foram persistidas corretamente.

**Decisão tomada (2026-08-19):** migrar a proteção do SSH de `ufw` para regras
`iptables` puras na chain `INPUT`, unificando tudo num único mecanismo de persistência
(`iptables-persistent`), em vez de dois se conflitando. **Implementação pendente para a
próxima sessão** — ver [seguranca.md](seguranca.md) para o estado detalhado e o plano.

## 8. Troubleshooting

| Sintoma | Causa provável | Verificação |
|---|---|---|
| `permission denied` ao rodar `docker ps` | usuário não está no grupo `docker` (decisão consciente, ver seção 4) | usar `sudo docker ...` |
| `Cannot connect to the Docker daemon` | serviço parado | `sudo systemctl status docker` |
| Arquivo de repositório com aspas erradas | escaping de múltiplos níveis de aspas no SSH | conferir `cat /etc/apt/sources.list.d/docker.list` |
| `404 Not Found` no `apt update` para `download.docker.com` | repo do Docker sem pacotes para a versão do Ubuntu ainda | trocar o codename por uma LTS anterior suportada (ex.: `noble`) |

## 9. Registro de alterações

| Data | Alteração |
|---|---|
| 2026-08-16 | Docker instalado via repositório oficial (`docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`, `docker-compose-plugin`). Testado com `hello-world`. Decisão consciente de **não** adicionar `ubnt` ao grupo `docker` — continuar usando `sudo docker`. |
