import re
from typing import Any

from app.api.hub_client import HubClient, HubClientError
from app.database.db import Database
from app.services.cnpj_utils import normalizar_resposta_cnpj


def normalizar_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj)


class CnpjService:
    def __init__(self, db: Database, hub: HubClient | None = None) -> None:
        self.db = db
        self.hub = hub or HubClient()

    def consultar(
        self,
        cnpj: str,
        *,
        forcar_api: bool = False,
        receita_direta: bool = False,
        ie: str | None = None,
    ) -> dict[str, Any]:
        cnpj_limpo = normalizar_cnpj(cnpj)

        if len(cnpj_limpo) != 14:
            return {
                "source": "validacao",
                "data": {
                    "status": False,
                    "return": "NOK",
                    "message": "CNPJ deve conter 14 dígitos.",
                    "consumed": 0,
                },
            }

        if ie and ie not in ("1", "3"):
            return {
                "source": "validacao",
                "data": {
                    "status": False,
                    "return": "NOK",
                    "message": "Parâmetro IE inválido. Use 1 (online) ou 3 (cache).",
                    "consumed": 0,
                },
            }

        if not forcar_api:
            cached = self.db.get_cnpj(cnpj_limpo)
            if cached:
                cached["data"] = normalizar_resposta_cnpj(cached["data"])
                return cached

        try:
            raw = self.hub.consultar_cnpj(
                cnpj_limpo,
                ignore_db=receita_direta,
                ie=ie,
            )
            payload = normalizar_resposta_cnpj(raw)
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

        self.db.save_cnpj(cnpj_limpo, payload)
        return {"source": "api", "data": payload}
