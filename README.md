# API Consulta CPF

Sistema em **Python** e **Flet** para consultas na API do [Hub do Desenvolvedor](https://hubdodesenvolvedor.com.br/), com cache em banco SQLite local.

Atualmente implementado: **consulta CPF**, **consulta CNPJ**, **consulta CEP** e **Correios** (frete + rastreio). Estrutura preparada para Outros.

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

### Instalação de desenvolvimento

Ferramentas extras: **pytest**, **pytest-cov**, **pylint** e **mypy**.

**Com uv (recomendado):**

```bash
uv sync --group dev
```

**Com pip / Conda:**

```bash
pip install -r requirements-dev.txt
# ou, a partir da raiz do projeto:
pip install -e ".[dev]"
```

**Scripts auxiliares:**

```batch
scripts\install-dev.bat
```

```bash
chmod +x scripts/install-dev.sh
./scripts/install-dev.sh
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
uv run python scripts\post_build_dist.py build\nuitka-zig\main.dist
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
3. `scripts/post_build_linux.py` — runtime Python, assets do Flet Web, `.env`, banco e marcador `.web-dist`

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
uv run python scripts/post_build_linux.py build/linux-web/main.dist
```

### Instalar no Debian 13 (servico systemd)

Arquivos em [`deploy/debian13/`](deploy/debian13/README.md): instala em `/srv/api-consulta-cpf` com autostart.

```bash
chmod +x deploy/debian13/install.sh
sudo ./deploy/debian13/install.sh build/linux-web/main.dist
sudo nano /srv/api-consulta-cpf/.env   # HUB_TOKEN
sudo systemctl restart api-consulta-cpf
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
│   ├── dist_common.py           # Funções compartilhadas de pós-build
│   ├── prepare_flet_desktop.py  # Runtime desktop do Flet
│   ├── post_build_dist.py       # Pós-build Windows (DLLs, .env, banco)
│   ├── post_build_linux.py      # Pós-build Linux web (.so, flet_web, .web-dist)
│   ├── install-dev.bat          # Instala grupo dev (Windows)
│   ├── install-dev.sh           # Instala grupo dev (Linux)
│   ├── check-dev.bat            # pytest + cov + pylint + mypy
│   └── check-dev.sh
├── deploy/
│   └── debian13/                # Instalação em /srv + systemd (Debian 13)
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
│   │   ├── cpf_service.py
│   │   ├── cnpj_service.py
│   │   ├── cep_service.py
│   │   ├── correios_service.py  # Frete + rastreio
│   │   └── correios_utils.py
│   └── ui/
│       ├── app.py
│       └── resultado_view.py
├── tests/                  # pytest (unitários + cobertura)
│   ├── test_cep_service.py
│   ├── test_cpf_service.py
│   ├── test_correios_*.py
│   └── test_database.py
├── data/                   # Banco SQLite (gitignored)
├── .env.example
├── requirements.txt        # Dependências runtime (pip)
└── requirements-dev.txt    # pytest, pylint, mypy, pytest-cov
```

## Banco de dados

Arquivo padrão: `data/consultas.db`

| Tabela        | Uso                                      |
|---------------|------------------------------------------|
| `cpf`         | Consultas CPF (CPF único, JSON completo) |
| `cnpj`        | Consultas CNPJ (CNPJ único, JSON completo) |
| `cep`         | Consultas CEP (JSON normalizado)         |
| `correios`    | Frete e rastreio (chave + tipo)          |
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

## API Correios — WSFRETEJ / WSRASTREIOJ

Aba **Frete** e aba **Rastreio** (Correios), cada uma com painel Pesquisa | Retorno.

- Endpoint: `https://ws.hubdodesenvolvedor.com.br/v2/correios/`
- **Frete:** `servico=calculoFrete`, CEPs, dimensões (cm), peso (g), `formato` (1=caixa, 2=rolo, 3=envelope), `tipoServico` (40010=SEDEX, 41106=PAC, …)
- Opcionais frete: `avisoRecebimento=S`, `maoPropria=S`
- **Rastreio:** `servico=rastreamento`, `codigo_rastreamento`
- Timeout: 450s

## Testes e qualidade de código

Requer a [instalação de desenvolvimento](#instalação-de-desenvolvimento).

### Testes unitários (pytest)

```bash
uv run pytest
```

Com relatório de cobertura (`pytest-cov`):

```bash
uv run pytest --cov=app --cov-report=term-missing --cov-report=html
```

O HTML fica em `htmlcov/index.html`.

### Análise estática

```bash
uv run pylint app main.py
uv run mypy
```

Ou execute tudo de uma vez (testes + cobertura + pylint + mypy):

```batch
scripts\check-dev.bat
```

```bash
chmod +x scripts/check-dev.sh
./scripts/check-dev.sh
```

Configurações em `pyproject.toml` (`[tool.pylint.*]`, `[tool.mypy]`, `[tool.coverage.*]`).  
Pylint e mypy analisam o backend (`app/api`, `app/services`, `app/database`, `config`); a camada Flet (`app/ui`) fica de fora por não haver stubs tipados.

### Escopo dos testes

- Normalização CEP, CPF e Correios
- Serviços com cache mockado (`CepService`, `CorreiosService`)
- Parâmetros do `HubClient` (Correios)
- Persistência SQLite (`Database`)

## Próximos passos

- [x] Consulta Correios (frete + rastreio)
- [ ] Outros serviços

## Licença

Uso interno / projeto privado.
