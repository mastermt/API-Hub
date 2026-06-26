# Deploy no Debian 13 (systemd)

Instala a distribuicao compilada (`main.dist`) em **`/srv/api-consulta-cpf`** e configura inicializacao automatica via **systemd**.

## Conteudo da pasta

| Arquivo | Descricao |
|---------|-----------|
| `install.sh` | Copia `main.dist` para `/srv` e habilita o servico |
| `uninstall.sh` | Remove o servico (e a pasta em `/srv`, por padrao) |
| `api-consulta-cpf.service` | Unidade systemd (processada pelo `install.sh`) |
| `env.example` | Modelo de `.env` no servidor |

## Pre-requisitos

1. Build Linux gerado (veja [README principal](../../README.md#compilação-com-nuitka-linux--modo-web)):
   ```bash
   ./compile-linux-web.sh
   ```
2. Servidor **Debian 13** (ou compativel) com **systemd**.
3. Mesma arquitetura da compilacao (ex.: `x86_64`).

## Instalacao rapida

No servidor Debian, copie a pasta `deploy/debian13` e o conteudo de `build/linux-web/main.dist` (ou o tarball da distribuicao).

```bash
# Exemplo: projeto ja esta em /opt/api_consulta_cpf no servidor
cd /opt/api_consulta_cpf
chmod +x deploy/debian13/install.sh deploy/debian13/uninstall.sh

sudo ./deploy/debian13/install.sh build/linux-web/main.dist
```

Porta customizada:

```bash
sudo SERVICE_PORT=9000 ./deploy/debian13/install.sh build/linux-web/main.dist
```

## Configuracao

### 1. Token da API

Edite o `.env` na pasta de instalacao:

```bash
sudo nano /srv/api-consulta-cpf/.env
```

Defina `HUB_TOKEN` com o token do [Hub do Desenvolvedor](https://hubdodesenvolvedor.com.br/sistema/).

Reinicie o servico:

```bash
sudo systemctl restart api-consulta-cpf
```

### 2. Firewall (opcional)

Se usar `ufw` e a porta padrao `8550`:

```bash
sudo ufw allow 8550/tcp
```

Para exposicao publica, considere um proxy reverso (nginx/Caddy) com HTTPS na frente do servico.

## Gerenciamento do servico

```bash
# Status
sudo systemctl status api-consulta-cpf

# Iniciar / parar / reiniciar
sudo systemctl start api-consulta-cpf
sudo systemctl stop api-consulta-cpf
sudo systemctl restart api-consulta-cpf

# Logs do systemd
sudo journalctl -u api-consulta-cpf -f

# Log de erros da aplicacao
sudo tail -f /srv/api-consulta-cpf/logs/erros.log
```

O servico sobe automaticamente no boot (`WantedBy=multi-user.target`).

### Alterar host ou porta depois da instalacao

Crie um override do systemd:

```bash
sudo systemctl edit api-consulta-cpf
```

Exemplo:

```ini
[Service]
ExecStart=
ExecStart=/srv/api-consulta-cpf/api-consulta --host 127.0.0.1 --port 8550
```

Depois:

```bash
sudo systemctl daemon-reload
sudo systemctl restart api-consulta-cpf
```

Use `127.0.0.1` quando houver nginx na frente; `0.0.0.0` para acesso direto pela rede.

## Estrutura em /srv

```
/srv/api-consulta-cpf/
├── api-consulta          # Binario Nuitka
├── .env                  # Configuracao (HUB_TOKEN, etc.)
├── .web-dist             # Marcador build web
├── data/
│   └── consultas.db      # Cache SQLite
├── logs/
│   └── erros.log         # Erros da aplicacao
└── ...                   # Bibliotecas e assets do build
```

Usuario do servico: `api-consulta` (conta de sistema, sem login).

## Desinstalar

Remove servico e pasta `/srv/api-consulta-cpf`:

```bash
sudo ./deploy/debian13/uninstall.sh
```

Manter dados e binarios, removendo apenas o servico:

```bash
sudo ./deploy/debian13/uninstall.sh --keep-data
```

## Atualizar versao

1. Compile nova `main.dist` na maquina de build.
2. Copie para o servidor.
3. Pare o servico, reinstale e reinicie:

```bash
sudo systemctl stop api-consulta-cpf
sudo ./deploy/debian13/install.sh /caminho/nova/main.dist
```

O `install.sh` preserva `.env` existente se ja estiver configurado.
