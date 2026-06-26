import re
from typing import Any

from app.api.hub_client import HubClient, HubClientError
from app.database.db import Database
from app.services.correios_utils import (
    FORMATOS_EMBALAGEM,
    TIPOS_SERVICO_FRETE,
    chave_cache_frete,
    normalizar_codigo_rastreio,
    normalizar_cep,
    normalizar_resposta_correios,
)


class CorreiosService:
    def __init__(self, db: Database, hub: HubClient | None = None) -> None:
        self.db = db
        self.hub = hub or HubClient()

    def calcular_frete(
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
        forcar_api: bool = False,
    ) -> dict[str, Any]:
        cep_o = normalizar_cep(cep_origem)
        cep_d = normalizar_cep(cep_destino)

        if len(cep_o) != 8 or len(cep_d) != 8:
            return self._erro_validacao("CEP de origem e destino devem conter 8 dígitos.")

        if formato not in FORMATOS_EMBALAGEM:
            return self._erro_validacao("Formato inválido. Use 1 (caixa), 2 (rolo) ou 3 (envelope).")

        if tipo_servico not in TIPOS_SERVICO_FRETE:
            return self._erro_validacao("Tipo de serviço inválido.")

        dims = (altura, largura, comprimento, peso)
        if not all(re.fullmatch(r"\d+", v or "") for v in dims):
            return self._erro_validacao(
                "Altura, largura, comprimento e peso devem ser números inteiros."
            )

        cache_key = chave_cache_frete(
            cep_origem=cep_o,
            cep_destino=cep_d,
            altura=altura,
            largura=largura,
            comprimento=comprimento,
            peso=peso,
            formato=formato,
            tipo_servico=tipo_servico,
            aviso_recebimento=aviso_recebimento,
            mao_propria=mao_propria,
        )

        if not forcar_api:
            cached = self.db.get_correios(cache_key, "frete")
            if cached:
                return cached

        try:
            raw = self.hub.consultar_frete_correios(
                cep_origem=cep_o,
                cep_destino=cep_d,
                altura=altura,
                largura=largura,
                comprimento=comprimento,
                peso=peso,
                formato=formato,
                tipo_servico=tipo_servico,
                aviso_recebimento=aviso_recebimento,
                mao_propria=mao_propria,
            )
            payload = normalizar_resposta_correios(raw)
        except HubClientError as exc:
            return {"source": "erro", "data": self._erro_payload(str(exc))}
        except Exception as exc:
            return {
                "source": "erro",
                "data": self._erro_payload(f"Erro na consulta: {exc}"),
            }

        self.db.save_correios(cache_key, "frete", payload)
        return {"source": "api", "data": payload}

    def rastrear(
        self,
        codigo: str,
        *,
        forcar_api: bool = False,
    ) -> dict[str, Any]:
        codigo_limpo = normalizar_codigo_rastreio(codigo)

        if len(codigo_limpo) < 10:
            return self._erro_validacao("Código de rastreamento inválido.")

        if not forcar_api:
            cached = self.db.get_correios(codigo_limpo, "rastreio")
            if cached:
                return cached

        try:
            raw = self.hub.consultar_rastreio_correios(codigo_limpo)
            payload = normalizar_resposta_correios(raw)
        except HubClientError as exc:
            return {"source": "erro", "data": self._erro_payload(str(exc))}
        except Exception as exc:
            return {
                "source": "erro",
                "data": self._erro_payload(f"Erro na consulta: {exc}"),
            }

        self.db.save_correios(codigo_limpo, "rastreio", payload)
        return {"source": "api", "data": payload}

    @staticmethod
    def _erro_payload(message: str) -> dict[str, Any]:
        return {
            "status": False,
            "return": "NOK",
            "message": message,
            "consumed": 0,
        }

    def _erro_validacao(self, message: str) -> dict[str, Any]:
        return {"source": "validacao", "data": self._erro_payload(message)}
