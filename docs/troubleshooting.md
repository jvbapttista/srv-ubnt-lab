# Troubleshooting

Problemas reais encontrados no laboratório, com causa e solução. Cada entrada só entra
aqui depois de ter sido efetivamente diagnosticada.

---

## `sudo: A terminal is required to authenticate`

**Data:** 2026-08-15
**Contexto:** executar comando com `sudo` remotamente, em uma linha só.

### Sintoma

```bash
ssh ubnt@srv-ubnt-001 'sudo ufw status verbose'
sudo: A terminal is required to authenticate
```

### Causa

`ssh host 'comando'` executa em modo não-interativo e **não aloca pseudo-terminal (PTY)**.
O `sudo` se recusa a ler a senha de um `stdin` que não seja um terminal real — proteção
contra captura ou injeção de senha por scripts.

```text
ssh host 'cmd'       sem PTY    → sudo recusa
ssh host             com PTY    → sudo funciona
ssh -t host 'cmd'    força PTY  → sudo funciona
```

### Solução

Flag `-t` do cliente SSH:

```bash
ssh -t ubnt@srv-ubnt-001 'sudo ufw status verbose'
```

### Observações

- Use `;` em vez de `&&` ao encadear comandos de diagnóstico. Com `&&`, um comando que
  retorna código diferente de zero interrompe a cadeia e a saída dos demais se perde.
- Comandos **sem** `sudo` não precisam de `-t`. Coleta de estado somente-leitura
  (`ss`, `ip`, `systemctl is-active`, `lsblk`) funciona normalmente em modo não-interativo,
  o que é útil para scripts de auditoria.
- `ssh -t` com `sudo` também é o caminho quando o comando remoto precisa de saída
  formatada para terminal (paginadores, cores).

### O que NÃO fazer

```bash
# NUNCA:
echo 'minhasenha' | sudo -S comando
```

Expõe a senha em `~/.bash_history`, na lista de processos (`ps`, visível por qualquer
usuário) e possivelmente em logs. Para automação legítima, a forma correta é uma regra
`NOPASSWD` no `sudoers` restrita a comandos específicos — nunca senha em linha de comando.

---

## Diretiva do `sshd_config` não faz efeito mesmo com sintaxe válida

**Data:** 2026-08-15
**Contexto:** desativar `PasswordAuthentication` criando um drop-in em
`/etc/ssh/sshd_config.d/`.

### Sintoma

Criado `/etc/ssh/sshd_config.d/90-hardening.conf` com `PasswordAuthentication no`.
`sudo sshd -t` validou sem erro. `sudo systemctl reload ssh` rodou sem erro. Mesmo assim,
um teste forçando autenticação por senha ainda listava `password` como método aceito:

```bash
ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no -o BatchMode=yes ubnt@servidor
→ Permission denied (publickey,password)
```

### Causa

No `sshd_config`, diferente de quase todo outro arquivo de configuração Linux, **a
primeira ocorrência de uma diretiva vence; ocorrências posteriores são silenciosamente
ignoradas** — sem aviso, sem erro. O `Include /etc/ssh/sshd_config.d/*.conf` expande os
arquivos em ordem alfabética. Um drop-in pré-existente com nome alfabeticamente anterior
(`50-cloud-init.conf`, criado pelo cloud-init) já definia `PasswordAuthentication yes`,
e continuava vencendo sobre o `90-hardening.conf` criado depois.

### Diagnóstico correto

`sshd -t` só valida **sintaxe**, nunca revela qual diretiva está de fato em vigor.
A forma correta de auditar é sempre a configuração **efetiva**:

```bash
sudo sshd -T | grep -i passwordauth
```

E, ao suspeitar de conflito entre drop-ins, buscar todas as ocorrências:

```bash
sudo grep -rn "PasswordAuthentication" /etc/ssh/sshd_config.d/
```

### Solução

Editar a diretiva no arquivo que realmente está vencendo (neste caso, o próprio
`50-cloud-init.conf`), em vez de confiar que um arquivo novo com nome "maior"
sobrescreveria o comportamento.

### Lição geral

Antes de criar qualquer novo drop-in em `sshd_config.d/`, `logind.conf.d/`, ou qualquer
diretório `.d/` do systemd que use o mesmo padrão de "primeiro vence": conferir se a
diretiva já existe em outro arquivo, e sempre validar o valor **efetivo** depois da
mudança — nunca só a sintaxe.

---
