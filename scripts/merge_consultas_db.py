"""Mescla consultas.db das 3 localizações do projeto em data/consultas.db."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from collections.abc import Callable, Iterable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.database.db import Database

DB_LOCATIONS = (
    Path("data/consultas.db"),
    Path("build/linux-web/main.dist/data/consultas.db"),
    Path("build/nuitka-zig/main.dist/data/consultas.db"),
)

CONFIG_TOTAL_KEYS = (
    "cpf_consumed_total",
    "cnpj_consumed_total",
    "cep_consumed_total",
    "correios_consumed_total",
    "outros_consumed_total",
)


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_verdadeiro(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, int):
        return valor != 0
    if isinstance(valor, str):
        return valor.strip().lower() in {"true", "1", "sim", "ok"}
    return False


def payload_sucesso(
    response_json: str | None,
    *,
    return_code: str | None = None,
    status: int | None = None,
) -> bool:
    """Retorna False para consultas com falha (NOK / status inválido)."""
    if return_code == "NOK":
        return False
    if status is not None and status == 0:
        pass  # ainda pode ser sucesso se o JSON indicar OK

    if not response_json or not str(response_json).strip():
        return False

    try:
        payload = json.loads(response_json)
    except json.JSONDecodeError:
        return False

    if not isinstance(payload, dict):
        return False

    if payload.get("return") == "NOK":
        return False

    status_payload = payload.get("status")
    if status_payload is not None and not _status_verdadeiro(status_payload):
        return False

    if payload.get("return") == "OK":
        return True

    if payload.get("result"):
        return True

    if payload.get("dados"):
        return True

    if status == 1:
        return True

    return False


def _row_as_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def _ler_tabela(conn: sqlite3.Connection, tabela: str) -> list[dict[str, Any]]:
    cursor = conn.execute(f"SELECT * FROM {tabela}")
    return [_row_as_dict(row) for row in cursor.fetchall()]


def _tabelas_existentes(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row[0] for row in rows}


def _escolher_mais_recente(
    atual: dict[str, Any] | None,
    candidato: dict[str, Any],
) -> dict[str, Any]:
    if atual is None:
        return candidato
    atual_ts = str(atual.get("updated_at") or "")
    candidato_ts = str(candidato.get("updated_at") or "")
    if candidato_ts >= atual_ts:
        return candidato
    return atual


def mesclar_por_chave(
    registros: Iterable[dict[str, Any]],
    chave_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
    *,
    filtrar_sucesso: bool = True,
) -> list[dict[str, Any]]:
    mesclados: dict[tuple[Any, ...], dict[str, Any]] = {}

    for registro in registros:
        if filtrar_sucesso and not payload_sucesso(
            registro.get("response_json"),
            return_code=registro.get("return_code"),
            status=registro.get("status"),
        ):
            continue

        chave = chave_fn(registro)
        mesclados[chave] = _escolher_mais_recente(mesclados.get(chave), registro)

    return list(mesclados.values())


def mesclar_config(registros: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    agregados: dict[str, dict[str, Any]] = {}
    agora = _utc_now()

    for registro in registros:
        chave = str(registro.get("chave") or "")
        if not chave:
            continue

        if chave not in agregados:
            agregados[chave] = {
                "chave": chave,
                "valor": registro.get("valor", "0"),
                "updated_at": registro.get("updated_at") or agora,
            }
            continue

        existente = agregados[chave]
        if chave in CONFIG_TOTAL_KEYS:
            try:
                total = int(existente["valor"]) + int(registro.get("valor") or 0)
            except (TypeError, ValueError):
                total = int(existente.get("valor") or 0)
            existente["valor"] = str(total)
        elif str(registro.get("updated_at") or "") >= str(existente.get("updated_at") or ""):
            existente["valor"] = registro.get("valor", existente["valor"])
            existente["updated_at"] = registro.get("updated_at") or agora

    return list(agregados.values())


def coletar_fontes(raiz: Path) -> list[tuple[Path, list[dict[str, Any]], list[dict[str, Any]]]]:
    """Retorna (caminho, tabelas_lidas, cpf_ignorados_por_fonte)."""
    fontes: list[tuple[Path, dict[str, list[dict[str, Any]]], int]] = []

    for relativo in DB_LOCATIONS:
        caminho = (raiz / relativo).resolve()
        if not caminho.is_file():
            print(f"[ignorado] não encontrado: {caminho}")
            continue

        dados: dict[str, list[dict[str, Any]]] = {}
        cpf_ignorados = 0

        conn = sqlite3.connect(caminho)
        conn.row_factory = sqlite3.Row
        try:
            tabelas = _tabelas_existentes(conn)
            for nome in ("cpf", "cnpj", "cep", "correios", "outros", "config", "consumo_log"):
                if nome in tabelas:
                    dados[nome] = _ler_tabela(conn, nome)

            for registro in dados.get("cpf", []):
                if not payload_sucesso(
                    registro.get("response_json"),
                    return_code=registro.get("return_code"),
                    status=registro.get("status"),
                ):
                    cpf_ignorados += 1
        finally:
            conn.close()

        print(f"[lido] {caminho} — CPF ignorados (falha): {cpf_ignorados}")
        fontes.append((caminho, dados, cpf_ignorados))

    return fontes


def _inserir_registros(
    conn: sqlite3.Connection,
    tabela: str,
    colunas: Sequence[str],
    registros: Iterable[dict[str, Any]],
    *,
    substituir: bool = False,
) -> int:
    if not registros:
        return 0

    placeholders = ", ".join("?" for _ in colunas)
    cols = ", ".join(colunas)
    verbo = "INSERT OR REPLACE" if substituir else "INSERT"
    sql = f"{verbo} INTO {tabela} ({cols}) VALUES ({placeholders})"

    valores = [tuple(registro.get(col) for col in colunas) for registro in registros]
    conn.executemany(sql, valores)
    return len(valores)


def gravar_mesclado(destino: Path, blocos: dict[str, list[dict[str, Any]]]) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        destino.unlink()

    Database(destino)

    conn = sqlite3.connect(destino)
    try:
        _inserir_registros(
            conn,
            "cpf",
            (
                "cpf",
                "data_nascimento",
                "status",
                "return_code",
                "message",
                "consumed",
                "response_json",
                "created_at",
                "updated_at",
            ),
            blocos.get("cpf", []),
        )
        _inserir_registros(
            conn,
            "cnpj",
            (
                "cnpj",
                "return_code",
                "message",
                "consumed",
                "response_json",
                "created_at",
                "updated_at",
            ),
            blocos.get("cnpj", []),
        )
        _inserir_registros(
            conn,
            "cep",
            (
                "cep",
                "return_code",
                "message",
                "consumed",
                "response_json",
                "created_at",
                "updated_at",
            ),
            blocos.get("cep", []),
        )
        _inserir_registros(
            conn,
            "correios",
            (
                "chave",
                "tipo",
                "return_code",
                "message",
                "consumed",
                "response_json",
                "created_at",
                "updated_at",
            ),
            blocos.get("correios", []),
        )
        _inserir_registros(
            conn,
            "outros",
            (
                "servico",
                "chave",
                "return_code",
                "message",
                "consumed",
                "response_json",
                "created_at",
                "updated_at",
            ),
            blocos.get("outros", []),
        )
        _inserir_registros(
            conn,
            "config",
            ("chave", "valor", "updated_at"),
            blocos.get("config", []),
            substituir=True,
        )
        _inserir_registros(
            conn,
            "consumo_log",
            ("servico", "chave", "consumed", "origem", "created_at"),
            blocos.get("consumo_log", []),
        )
        conn.commit()
    finally:
        conn.close()


def mesclar_blocos(fontes: list[tuple[Path, dict[str, list[dict[str, Any]]], int]]) -> dict[str, list[dict[str, Any]]]:
    cpf_rows: list[dict[str, Any]] = []
    cnpj_rows: list[dict[str, Any]] = []
    cep_rows: list[dict[str, Any]] = []
    correios_rows: list[dict[str, Any]] = []
    outros_rows: list[dict[str, Any]] = []
    config_rows: list[dict[str, Any]] = []
    consumo_rows: list[dict[str, Any]] = []

    for _, dados, _ in fontes:
        cpf_rows.extend(dados.get("cpf", []))
        cnpj_rows.extend(dados.get("cnpj", []))
        cep_rows.extend(dados.get("cep", []))
        correios_rows.extend(dados.get("correios", []))
        outros_rows.extend(dados.get("outros", []))
        config_rows.extend(dados.get("config", []))
        consumo_rows.extend(dados.get("consumo_log", []))

    return {
        "cpf": mesclar_por_chave(cpf_rows, lambda r: (r["cpf"],), filtrar_sucesso=True),
        "cnpj": mesclar_por_chave(cnpj_rows, lambda r: (r["cnpj"],), filtrar_sucesso=True),
        "cep": mesclar_por_chave(cep_rows, lambda r: (r["cep"],), filtrar_sucesso=True),
        "correios": mesclar_por_chave(
            correios_rows,
            lambda r: (r["chave"], r.get("tipo") or ""),
            filtrar_sucesso=True,
        ),
        "outros": mesclar_por_chave(
            outros_rows,
            lambda r: (r["servico"], r["chave"]),
            filtrar_sucesso=True,
        ),
        "config": mesclar_config(config_rows),
        "consumo_log": consumo_rows,
    }


def backup_principal(raiz: Path) -> Path | None:
    origem = raiz / "data" / "consultas.db"
    if not origem.is_file():
        print("[backup] data/consultas.db não existe — nada para renomear.")
        return None

    destino = raiz / "data" / "consultas_old.db"
    if destino.exists():
        destino.unlink()

    shutil.move(str(origem), str(destino))
    print(f"[backup] {origem} -> {destino}")
    return destino


def executar_merge(*, dry_run: bool = False) -> int:
    raiz = project_root()
    fontes = coletar_fontes(raiz)

    if not fontes:
        raise SystemExit("Nenhum consultas.db encontrado nas 3 localizações.")

    blocos = mesclar_blocos(fontes)

    print("\nResumo da mesclagem:")
    for tabela, registros in blocos.items():
        print(f"  {tabela}: {len(registros)} registro(s)")

    if dry_run:
        print("\n[dry-run] Nenhum arquivo foi alterado.")
        return 0

    backup = backup_principal(raiz)
    destino = raiz / "data" / "consultas.db"
    try:
        gravar_mesclado(destino, blocos)
    except Exception:
        if backup is not None and backup.is_file():
            if destino.exists():
                destino.unlink()
            shutil.move(str(backup), str(destino))
            print(f"[restaurado] Falha na gravação — backup devolvido para {destino}")
        raise
    print(f"\n[ok] Nova base criada em: {destino}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mescla consultas.db de data/ e builds em data/consultas.db.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas mostra o que seria mesclado, sem alterar arquivos.",
    )
    args = parser.parse_args()
    raise SystemExit(executar_merge(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
