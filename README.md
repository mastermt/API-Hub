# API Consulta CPF

Sistema em **Python** e **Flet** para consultas na API do [Hub do Desenvolvedor](https://hubdodesenvolvedor.com.br/), com cache em banco SQLite local.

Atualmente implementado: **consulta CPF**, **consulta CNPJ** e **consulta CEP**. Estrutura preparada para Correios e Outros.

## Funcionalidades

- Interface **Web** por padrão (também suporta Desktop)
- Cache local: consulta primeiro o banco; se não houver registro, chama a API e grava o resultado
- Tabelas separadas: `cpf`, `cnpj`, `cep`, `correios`, `outros`
- Controle de créditos consumidos na tabela `config` e histórico em `consumo_log`
- Opções: forçar API (ignorar cache) e modo Turbo

## Requisitos

- Python 3.12 ou superior
- Token do Hub do Desenvolvedor
- [uv](https://docs.astral.sh/uv/) (recomendado) ou pip/Conda

## Instalação

### Com uv (recomendado)

Instale o [uv](https://docs.astral.sh/uv/getting-started/installation/) e, na pasta do projeto:

```bash
cd c:\projetos\api_consulta_cpf
uv sync
```

O `uv sync` cria o ambiente virtual em `.venv` e instala as dependências definidas em `pyproject.toml` (lock em `uv.lock`).

Para usar outra versão do Python:

```bash
uv python install 3.14
uv sync --python 3.14
```

### Com pip / Conda

```bash
conda activate api-consulta
cd c:\projetos\api_consulta_cpf
pip install -r requirements.txt
```

### Configurar o token

Copie o arquivo de ambiente e configure o token:

```bash
copy .env.example .env
```

Edite `.env`:

```env
HUB_TOKEN=seu_token_aqui
```

> **Importante:** nunca commite o arquivo `.env` nem tokens no repositório.

## Execução

### Com uv

Web (padrão — abre o navegador em `http://127.0.0.1:8550`):

```bash
uv run python main.py
# ou
uv run api-consulta
```

Desktop:

```bash
uv run api-consulta --desktop
```

Porta customizada:

```bash
uv run api-consulta --port 8080
```

### Com Python direto

Web (padrão):

```bash
python main.py
```

Abre automaticamente no navegador em `http://127.0.0.1:8550`.

Desktop:

```bash
python main.py --desktop
```

Porta customizada:

```bash
python main.py --port 8080
```

## Compilação com Nuitka (Windows)

Gera um executável desktop standalone com [Nuitka](https://nuitka.net/) usando o compilador [Zig](https://ziglang.org/) (`--zig`).

### Requisitos extras

- [Zig](https://ziglang.org/download/) no `PATH` (`zig` disponível no terminal)
- [uv](https://docs.astral.sh/uv/) com dependências do projeto (inclui Nuitka e `flet-desktop`)
- Python 3.12 ou 3.13 (recomendado; 3.14 ainda é experimental no Nuitka)

### Compilar

Na pasta do projeto:

```batch
cd c:\projetos\api_consulta_cpf
compile.bat
```

Modo **standalone** (padrão, recomendado): gera a pasta `build\nuitka-zig\main.dist` com o executável e todas as dependências.

```batch
compile.bat standalone
```

Modo **onefile** (executável único):

```batch
compile.bat onefile
```

O script `compile.bat` executa automaticamente:

1. `uv sync --group build` — instala dependências e `flet-desktop`
2. `scripts\prepare_flet_desktop.py` — baixa o runtime desktop do Flet (`flet-windows.zip`)
3. Compilação Nuitka com Zig para `build\nuitka-zig`
4. `scripts\post_build_dist.py` — copia runtime Python (ctypes, SQLite, DLLs do Conda), dados do Flet, `.env` e `data\consultas.db`

### Executar o build

```batch
cd build\nuitka-zig\main.dist
api-consulta.exe
```

No `.exe` compilado, o modo **desktop** é o padrão e **não abre janela de console** ao dar duplo clique no Explorer (`--windows-console-mode=disable`).

Para forçar o navegador (somente se o build incluir `flet-web`):

```batch
api-consulta.exe --web
```

### Distribuir

Copie a pasta **`main.dist` inteira** para outro computador. Não mova apenas o `.exe` — as DLLs e bibliotecas ficam na mesma pasta.

Confirme que existem na pasta de distribuição:

- `.env` com `HUB_TOKEN` configurado
- `data\consultas.db` (opcional; criado vazio se não existir)

Erros e mensagens de falha são gravados em **`logs\erros.log`** (na mesma pasta do `.exe`). Caminho customizável via `ERROR_LOG_PATH` no `.env`.

Para reaplicar apenas os arquivos de pós-build (sem recompilar):

```batch
uv run python scripts\post_build_dist.py build\nuitka-zig\main.dist --profile windows-desktop
```

## Compilação com Nuitka (Linux — modo web)

Gera uma distribuição standalone para **Linux** em modo **web** (servidor Flet + navegador).

> **Importante:** a compilação deve ser feita **em Linux** (máquina, VM, WSL ou CI). O Nuitka **não** faz cross-compile do Windows para Linux.

### Requisitos

- Linux x86_64 (ou WSL2)
- [uv](https://docs.astral.sh/uv/) no `PATH`
- Python 3.12 ou 3.13 (recomendado)
- Compilador C (gcc/clang) ou [Zig](https://ziglang.org/) opcional

### Compilar

```bash
cd /caminho/para/api_consulta_cpf
chmod +x compile-linux-web.sh
./compile-linux-web.sh
```

Se aparecer `bash\r: No such file or directory`, o arquivo está com fim de linha Windows (CRLF). Corrija com:

```bash
sed -i 's/\r$//' compile-linux-web.sh
```

Saída: `build/linux-web/main.dist/`

O script executa:

1. `uv sync --group build-linux-web` — instala `flet-web`
2. Compilação Nuitka para `build/linux-web`
3. `scripts/post_build_dist.py --profile linux-web` — runtime Python, assets do Flet Web, `.env`, banco e marcador `.web-dist`

### Executar no servidor

```bash
cd build/linux-web/main.dist
chmod +x api-consulta
./api-consulta --host 0.0.0.0 --port 8550
```

No build Linux web, o modo **web** é o padrão (`--host 0.0.0.0`). Acesse `http://<ip-do-servidor>:8550`.

### Distribuir

Copie a pasta **`main.dist` inteira** para o servidor Linux de destino (mesma arquitetura usada na compilação).

Arquivos necessários na pasta:

- `.env` com `HUB_TOKEN`
- `data/consultas.db` (opcional)

Pós-build manual:

```bash
uv run python scripts/post_build_dist.py build/linux-web/main.dist --profile linux-web
```

## Estrutura do projeto

```
api_consulta_cpf/
├── main.py                 # Entrada Flet (web/desktop)
├── compile.bat             # Compilação Nuitka + Zig (Windows desktop)
├── compile-linux-web.sh  # Compilação Nuitka Linux (modo web)
├── pyproject.toml          # Dependências e metadados (uv)
├── uv.lock                 # Lock de versões (uv)
├── scripts/
│   ├── prepare_flet_desktop.py  # Runtime desktop do Flet
│   └── post_build_dist.py       # Pós-build (DLLs, .env, banco)
├── build/                  # Saída da compilação (gitignored)
│   ├── nuitka-zig/
│   │   └── main.dist/      # Windows desktop
│   └── linux-web/
│       └── main.dist/      # Linux web
├── app/
│   ├── config.py           # Configurações e .env
│   ├── api/
│   │   └── hub_client.py   # Cliente HTTP Hub
│   ├── database/
│   │   └── db.py           # SQLite e tabelas
│   ├── services/
│   │   ├── cpf_service.py  # Lógica cache + API CPF
│   │   ├── cep_service.py  # Lógica cache + API CEP
│   │   └── cep_utils.py    # Normalização WSCEP1J3
│   └── ui/
│       └── app.py          # Interface Flet
├── data/                   # Banco SQLite (gitignored)
├── .env.example
└── requirements.txt        # Alternativa ao pyproject.toml (pip)
```

## Banco de dados

Arquivo padrão: `data/consultas.db`

| Tabela        | Uso                                      |
|---------------|------------------------------------------|
| `cpf`         | Consultas CPF (CPF único, JSON completo) |
| `cnpj`        | Consultas CNPJ (CNPJ único, JSON completo) |
| `cep`         | Consultas CEP (JSON normalizado)         |
| `correios`    | Reservada para Correios                  |
| `outros`      | Reservada para outros serviços           |
| `config`      | Totais de créditos por serviço           |
| `consumo_log` | Histórico de consumo                     |

Chaves em `config`: `cpf_consumed_total`, `cnpj_consumed_total`, etc.

## API CPF (Hub do Desenvolvedor)

- Endpoint: `https://ws.hubdodesenvolvedor.com.br/v2/cpf/`
- Parâmetros: `cpf`, `data` (DD/MM/AAAA), `token`
- Créditos: base 1 | Receita 5 | Turbo 25

## API CNPJ — WSCNPJ1

- Endpoint: `https://ws.hubdodesenvolvedor.com.br/v2/cnpj/`
- Parâmetros: `cnpj` (somente números), `token`
- Opcionais: `ignore_db=1` (Receita direta, 2 créditos), `ie=1` (IE online, +60s, +2 créditos), `ie=3` (IE cache)
- Créditos: base 1 | Receita 2
- Timeout: 300s (360s com `ie=1`)

## API CEP — WSCEP1J3 (Principal)

- Endpoint: `https://ws.hubdodesenvolvedor.com.br/v2/cep3/`
- Parâmetros: `cep` (somente números), `token`
- Busca direto nos Correios (performance depende dos Correios)
- **Sucesso:** JSON plano (`cep`, `logradouro`, `bairro`, `localidade`, `uf`, etc.)
- **Erro:** `return: NOK` + `message` (ex.: `CEP nao encontrado.`, `Parametro Invalido.`)
- O app normaliza o retorno para exibição e grava no cache local

Documentação oficial: [hubdodesenvolvedor.com.br](https://hubdodesenvolvedor.com.br/)

## Próximos passos

- [ ] Consulta Correios
- [ ] Outros serviços

## Licença

Uso interno / projeto privado.
