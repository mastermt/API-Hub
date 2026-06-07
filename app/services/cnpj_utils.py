"""Normalização e extração de campos do retorno WSCNPJ1."""

from typing import Any

ROTULOS_CNPJ = {
    "numero_de_inscricao": "CNPJ",
    "nome": "Razão social",
    "fantasia": "Nome fantasia",
    "tipo": "Tipo",
    "abertura": "Abertura",
    "porte": "Porte",
    "natureza_juridica": "Natureza jurídica",
    "logradouro": "Logradouro",
    "numero": "Número",
    "complemento": "Complemento",
    "cep": "CEP",
    "bairro": "Bairro",
    "municipio": "Município",
    "uf": "UF",
    "email": "E-mail",
    "telefone": "Telefone",
    "entidade_federativo_responsavel": "Entidade federativa responsável",
    "situacao": "Situação",
    "motivo_situacao_cadastral": "Motivo situação cadastral",
    "dt_situacao_cadastral": "Data situação cadastral",
    "situacao_especial": "Situação especial",
    "data_situacao_especial": "Data situação especial",
    "capital_social": "Capital social",
    "atividade_principal": "Atividade principal",
    "atividades_secundarias": "Atividades secundárias",
    "quadro_socios": "Quadro de sócios",
    "inscricoes_estaduais": "Inscrições estaduais",
}

CAMPOS_CNPJ_ORDEM = (
    "numero_de_inscricao",
    "nome",
    "fantasia",
    "tipo",
    "abertura",
    "porte",
    "natureza_juridica",
    "situacao",
    "motivo_situacao_cadastral",
    "dt_situacao_cadastral",
    "situacao_especial",
    "data_situacao_especial",
    "capital_social",
    "logradouro",
    "numero",
    "complemento",
    "cep",
    "bairro",
    "municipio",
    "uf",
    "email",
    "telefone",
    "entidade_federativo_responsavel",
    "atividade_principal",
    "atividades_secundarias",
    "quadro_socios",
    "inscricoes_estaduais",
)


def _formatar_atividade(atividade: dict[str, Any] | None) -> str:
    if not isinstance(atividade, dict):
        return ""
    code = atividade.get("code", "")
    text = atividade.get("text", "")
    if code and text:
        return f"{code} - {text}"
    return str(text or code or "")


def _formatar_atividades_secundarias(itens: Any) -> str:
    if not isinstance(itens, list):
        return ""
    linhas = [_formatar_atividade(item) for item in itens if isinstance(item, dict)]
    return "\n".join(l for l in linhas if l)


def _formatar_quadro_socios(socios: Any) -> str:
    if not isinstance(socios, list):
        return ""
    linhas: list[str] = []
    for item in socios:
        if isinstance(item, str) and item.strip():
            linhas.append(item.strip())
        elif isinstance(item, dict):
            info = item.get("informacoes") or item.get("nome") or str(item)
            if str(info).strip():
                linhas.append(str(info).strip())
    return "\n".join(linhas)


def _formatar_inscricoes_estaduais(ies: Any) -> str:
    if not isinstance(ies, dict):
        return ""
    linhas: list[str] = []
    ret = ies.get("return")
    if ret:
        linhas.append(f"Retorno IE: {ret}")
    if ies.get("ie_uf_origem"):
        linhas.append(f"IE UF origem: {ies['ie_uf_origem']}")
    if ies.get("ie_last_update"):
        linhas.append(f"Última atualização IE: {ies['ie_last_update']}")
    outras = ies.get("outras_ies")
    if isinstance(outras, list):
        for ie in outras:
            if not isinstance(ie, dict):
                continue
            uf = ie.get("uf", "")
            numero = ie.get("numero", "")
            ativo = "ativa" if str(ie.get("ativado")) == "1" else "inativa"
            linhas.append(f"{uf}: {numero} ({ativo})")
    return "\n".join(linhas)


def _valor_campo_cnpj(chave: str, valor: Any) -> str:
    if valor is None:
        return ""
    if chave == "atividade_principal":
        return _formatar_atividade(valor if isinstance(valor, dict) else None)
    if chave == "atividades_secundarias":
        return _formatar_atividades_secundarias(valor)
    if chave == "quadro_socios":
        return _formatar_quadro_socios(valor)
    if chave == "inscricoes_estaduais":
        return _formatar_inscricoes_estaduais(valor)
    if isinstance(valor, (list, dict)):
        return str(valor)
    return str(valor).strip()


def normalizar_resposta_cnpj(raw: dict[str, Any]) -> dict[str, Any]:
    """Garante envelope status/return/consumed quando a API já retorna estruturado."""
    if not raw:
        return {
            "status": False,
            "return": "NOK",
            "message": "Resposta vazia da API.",
            "consumed": 0,
        }
    if raw.get("return") in ("OK", "NOK"):
        return raw
    return {
        "status": False,
        "return": "NOK",
        "message": raw.get("message") or "Formato de resposta não reconhecido.",
        "consumed": int(raw.get("consumed") or 0),
    }


def extrair_campos_cnpj(result: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Retorna (rótulo, valor, chave) para exibição."""
    itens: list[tuple[str, str, str]] = []
    for chave in CAMPOS_CNPJ_ORDEM:
        if chave not in result:
            continue
        valor = _valor_campo_cnpj(chave, result[chave])
        if not valor:
            continue
        rotulo = ROTULOS_CNPJ.get(chave, chave.replace("_", " ").title())
        itens.append((rotulo, valor, chave))
    return itens
