from typing import Any

import httpx

from app.config import (
    CNPJ_API_TIMEOUT,
    CNPJ_API_TIMEOUT_IE_ONLINE,
    CORREIOS_API_TIMEOUT,
    CPF_API_TIMEOUT,
    CPF_API_TIMEOUT_TURBO,
    CPF_CONNECT_TIMEOUT,
    HUB_BASE_URL,
    HUB_TOKEN,
)


class HubClientError(Exception):
    pass


def _parse_json_dict(response: httpx.Response) -> dict[str, Any]:
    data = response.json()
    if not isinstance(data, dict):
        raise HubClientError("Resposta JSON inválida da API.")
    return data


class HubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or HUB_TOKEN
        if not self.token:
            raise HubClientError(
                "Token não configurado. Defina HUB_TOKEN no arquivo .env"
            )

    def consultar_cpf(
        self,
        cpf: str,
        data_nascimento: str | None = None,
        *,
        ignore_db: bool = False,
        turbo: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, str] = {
            "cpf": cpf,
            "token": self.token,
        }
        if data_nascimento:
            params["data"] = data_nascimento
        if ignore_db:
            params["ignore_db"] = "1"
        if turbo:
            params["turbo"] = "1"

        url = f"{HUB_BASE_URL}/cpf/"
        read_timeout = CPF_API_TIMEOUT_TURBO if turbo else CPF_API_TIMEOUT
        timeout = httpx.Timeout(
            connect=CPF_CONNECT_TIMEOUT,
            read=read_timeout,
            write=CPF_CONNECT_TIMEOUT,
            pool=CPF_CONNECT_TIMEOUT,
        )

        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return _parse_json_dict(response)

    def consultar_cep(
        self,
        cep: str,
        *,
        timeout_seconds: int = 450,
    ) -> dict[str, Any]:
        """
        WSCEP1J3 — CEP nos Correios (somente números no parâmetro cep).

        GET {HUB_BASE_URL}/cep3/?cep=...&token=...
        Sucesso: JSON plano (cep, logradouro, bairro, localidade, uf, ...).
        Erro: return=NOK e message conforme documentação oficial.
        """
        params: dict[str, str] = {"cep": cep, "token": self.token}
        url = f"{HUB_BASE_URL}/cep3/"

        timeout = httpx.Timeout(
            connect=CPF_CONNECT_TIMEOUT,
            read=timeout_seconds,
            write=CPF_CONNECT_TIMEOUT,
            pool=CPF_CONNECT_TIMEOUT,
        )
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return _parse_json_dict(response)

    def consultar_cnpj(
        self,
        cnpj: str,
        *,
        ignore_db: bool = False,
        ie: str | None = None,
    ) -> dict[str, Any]:
        """
        WSCNPJ1 — CNPJ Receita Federal (somente números no parâmetro cnpj).

        ie=1: IE em tempo real (+60s timeout, +2 créditos extras).
        ie=3: IE em cache do hub.
        ignore_db=1: consulta direto na Receita (2 créditos).
        """
        params: dict[str, str] = {"cnpj": cnpj, "token": self.token}
        if ignore_db:
            params["ignore_db"] = "1"
        if ie in ("1", "3"):
            params["ie"] = ie

        url = f"{HUB_BASE_URL}/cnpj/"
        read_timeout = CNPJ_API_TIMEOUT_IE_ONLINE if ie == "1" else CNPJ_API_TIMEOUT
        timeout = httpx.Timeout(
            connect=CPF_CONNECT_TIMEOUT,
            read=read_timeout,
            write=CPF_CONNECT_TIMEOUT,
            pool=CPF_CONNECT_TIMEOUT,
        )
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return _parse_json_dict(response)

    def consultar_frete_correios(
        self,
        *,
        cep_origem: str,
        cep_destino: str,
        altura: str,
        largura: str,
        comprimento: str,
        peso: str,
        formato: str,
        tipo_servico: str,
        aviso_recebimento: bool = False,
        mao_propria: bool = False,
        timeout_seconds: int = CORREIOS_API_TIMEOUT,
    ) -> dict[str, Any]:
        """
        WSFRETEJ — cálculo de frete Correios.

        GET {HUB_BASE_URL}/correios/?servico=calculoFrete&...
        """
        params: dict[str, str] = {
            "servico": "calculoFrete",
            "cepOrigem": cep_origem,
            "cepDestino": cep_destino,
            "altura": altura,
            "largura": largura,
            "comprimento": comprimento,
            "peso": peso,
            "formato": formato,
            "tipoServico": tipo_servico,
            "token": self.token,
        }
        if aviso_recebimento:
            params["avisoRecebimento"] = "S"
        if mao_propria:
            params["maoPropria"] = "S"

        url = f"{HUB_BASE_URL}/correios/"
        timeout = httpx.Timeout(
            connect=CPF_CONNECT_TIMEOUT,
            read=timeout_seconds,
            write=CPF_CONNECT_TIMEOUT,
            pool=CPF_CONNECT_TIMEOUT,
        )
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return _parse_json_dict(response)

    def consultar_rastreio_correios(
        self,
        codigo_rastreamento: str,
        *,
        timeout_seconds: int = CORREIOS_API_TIMEOUT,
    ) -> dict[str, Any]:
        """
        WSRASTREIOJ — rastreamento de objeto nos Correios.

        GET {HUB_BASE_URL}/correios/?servico=rastreamento&codigo_rastreamento=...&token=...
        """
        params: dict[str, str] = {
            "servico": "rastreamento",
            "codigo_rastreamento": codigo_rastreamento,
            "token": self.token,
        }
        url = f"{HUB_BASE_URL}/correios/"
        timeout = httpx.Timeout(
            connect=CPF_CONNECT_TIMEOUT,
            read=timeout_seconds,
            write=CPF_CONNECT_TIMEOUT,
            pool=CPF_CONNECT_TIMEOUT,
        )
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return _parse_json_dict(response)
