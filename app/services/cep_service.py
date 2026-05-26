import re
from typing import Any

from app.api.hub_client import HubClient, HubClientError
from app.database.db import Database
from app.services.cep_utils import normalizar_resposta_cep


def normalizar_cep(cep: str) -> str:
    return re.sub(r"\D", "", cep)


class CepService:
    def __init__(self, db: Database, hub: HubClient | None = None) -> None:
        self.db = db
        self.hub = hub or HubClient()

    def consultar(
        self,
        cep: str,
        *,
        forcar_api: bool = False,
    ) -> dict[str, Any]:
        cep_limpo = normalizar_cep(cep)

        if len(cep_limpo) != 8:
            return {
                "source": "validacao",
                "data": {
                    "status": False,
                    "return": "NOK",
                    "message": "CEP deve conter 8 dígitos.",
                    "consumed": 0,
                },
            }

        if not forcar_api:
            cached = self.db.get_cep(cep_limpo)
            if cached:
                cached["data"] = normalizar_resposta_cep(cached["data"])
                return cached

        try:
            raw = self.hub.consultar_cep(cep_limpo)
            payload = normalizar_resposta_cep(raw)
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

        self.db.save_cep(cep_limpo, payload)
        return {"source": "api", "data": payload}

