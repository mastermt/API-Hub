import re
from datetime import datetime
from typing import Any

from app.api.hub_client import HubClient, HubClientError
from app.database.db import Database


def normalizar_cpf(cpf: str) -> str:
    return re.sub(r"\D", "", cpf)


def validar_data_nascimento(data: str) -> bool:
    data = data.strip()
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        return False
    try:
        # Garante datas reais (ex.: não permite 31/02/2020)
        datetime.strptime(data, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def formatar_data_nascimento(data: str) -> str | None:
    """
    Ajusta a entrada para DD/MM/AAAA antes de enviar à API.

    Aceita, por exemplo:
    - 23091967  -> 23/09/1967
    - 23/09/1967, 23-09-1967, 23.09.1967
    """
    texto = (data or "").strip()
    if not texto:
        return None

    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", texto) and validar_data_nascimento(texto):
        return texto

    digitos = re.sub(r"\D", "", texto)
    if len(digitos) == 8:
        candidato = f"{digitos[0:2]}/{digitos[2:4]}/{digitos[4:8]}"
        if validar_data_nascimento(candidato):
            return candidato
        return None

    partes = [p for p in re.split(r"\D+", texto) if p]
    if len(partes) == 3:
        dia, mes, ano = partes[0], partes[1], partes[2]
        if len(ano) == 2:
            ano = f"20{ano}" if int(ano) < 50 else f"19{ano}"
        if len(ano) == 4 and len(dia) <= 2 and len(mes) <= 2:
            candidato = f"{int(dia):02d}/{int(mes):02d}/{ano}"
            if validar_data_nascimento(candidato):
                return candidato

    return None


class CpfService:
    def __init__(self, db: Database, hub: HubClient | None = None) -> None:
        self.db = db
        self.hub = hub or HubClient()

    def consultar(
        self,
        cpf: str,
        data_nascimento: str | None = None,
        *,
        forcar_api: bool = False,
        turbo: bool = False,
    ) -> dict[str, Any]:
        cpf_limpo = normalizar_cpf(cpf)
        if len(cpf_limpo) != 11:
            return {
                "source": "validacao",
                "data": {
                    "status": False,
                    "return": "NOK",
                    "message": "CPF deve conter 11 dígitos.",
                    "consumed": 0,
                },
            }

        texto_data = (data_nascimento or "").strip()
        data = formatar_data_nascimento(texto_data) if texto_data else None

        if texto_data and data is None:
            return {
                "source": "validacao",
                "data": {
                    "status": False,
                    "return": "NOK",
                    "message": (
                        "Data de nascimento inválida. Use DD/MM/AAAA "
                        "ou 8 dígitos (DDMMAAAA), ex.: 23091967."
                    ),
                    "consumed": 0,
                },
            }

        if turbo and not data:
            return {
                "source": "validacao",
                "data": {
                    "status": False,
                    "return": "NOK",
                    "message": "Data de nascimento é obrigatória para consulta Turbo (online). Use DD/MM/AAAA.",
                    "consumed": 0,
                },
            }
        if not forcar_api:
            cached = self.db.get_cpf(cpf_limpo, data)
            if cached:
                return cached

        try:
            payload = self.hub.consultar_cpf(
                cpf_limpo,
                data,
                # "forcar_api" aqui significa ignorar o cache local.
                # O hub só deve ignorar a base (ignore_db=1) quando estivermos
                # de fato fazendo a modalidade "turbo" (consulta online).
                ignore_db=turbo,
                turbo=turbo,
            )
        except HubClientError as exc:
            return {
                "source": "erro",
                "data": {
                    "status": False,
                    "return": "NOK",
                    "message": str(exc),
                    "consumed": 0,
                },
            }
        except Exception as exc:
            return {
                "source": "erro",
                "data": {
                    "status": False,
                    "return": "NOK",
                    "message": f"Erro na consulta: {exc}",
                    "consumed": 0,
                },
            }

        self.db.save_cpf(cpf_limpo, data, payload)
        return {"source": "api", "data": payload}
