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

## Estrutura do projeto

```
api_consulta_cpf/
├── main.py                 # Entrada Flet (web/desktop)
├── pyproject.toml          # Dependências e metadados (uv)
├── uv.lock                 # Lock de versões (uv)
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
