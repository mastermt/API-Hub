from typing import Any

import httpx

from app.config import (
    CPF_API_TIMEOUT,
    CPF_API_TIMEOUT_TURBO,
    CPF_CONNECT_TIMEOUT,
    HUB_BASE_URL,
    HUB_TOKEN,
)


class HubClientError(Exception):
    pass


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
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

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
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
