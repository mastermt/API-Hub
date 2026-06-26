import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _payload_cache_local(payload: dict[str, Any]) -> dict[str, Any]:
    """Resposta do cache local: consulta atual não consome créditos."""
    data = dict(payload)
    data["consumed"] = 0
    return data


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS cpf (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpf TEXT NOT NULL UNIQUE,
                    data_nascimento TEXT,
                    status INTEGER,
                    return_code TEXT,
                    message TEXT,
                    consumed INTEGER DEFAULT 0,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_cpf ON cpf(cpf);

                CREATE TABLE IF NOT EXISTS cnpj (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cnpj TEXT NOT NULL UNIQUE,
                    return_code TEXT,
                    message TEXT,
                    consumed INTEGER DEFAULT 0,
                    response_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_cnpj ON cnpj(cnpj);

                CREATE TABLE IF NOT EXISTS cep (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cep TEXT NOT NULL UNIQUE,
                    return_code TEXT,
                    message TEXT,
                    consumed INTEGER DEFAULT 0,
                    response_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS correios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chave TEXT NOT NULL,
                    tipo TEXT,
                    return_code TEXT,
                    message TEXT,
                    consumed INTEGER DEFAULT 0,
                    response_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS outros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    servico TEXT NOT NULL,
                    chave TEXT NOT NULL,
                    return_code TEXT,
                    message TEXT,
                    consumed INTEGER DEFAULT 0,
                    response_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS config (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consumo_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    servico TEXT NOT NULL,
                    chave TEXT,
                    consumed INTEGER NOT NULL,
                    origem TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            self._migrate_cpf_unique(conn)
            self._ensure_correios_unique(conn)
            self._ensure_config_keys(conn)

    def _migrate_cpf_unique(self, conn: sqlite3.Connection) -> None:
        """Migra tabela antiga (cpf+data) para CPF único, sem duplicidade."""
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='cpf'"
        ).fetchone()
        if not row or not row[0]:
            return

        ddl = row[0]
        if "UNIQUE(cpf, data_nascimento)" not in ddl and "UNIQUE (cpf, data_nascimento)" not in ddl:
            return

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cpf_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpf TEXT NOT NULL UNIQUE,
                data_nascimento TEXT,
                status INTEGER,
                return_code TEXT,
                message TEXT,
                consumed INTEGER DEFAULT 0,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            INSERT INTO cpf_new (
                cpf, data_nascimento, status, return_code, message,
                consumed, response_json, created_at, updated_at
            )
            SELECT
                c.cpf, c.data_nascimento, c.status, c.return_code, c.message,
                c.consumed, c.response_json, c.created_at, c.updated_at
            FROM cpf c
            INNER JOIN (
                SELECT cpf, MAX(updated_at) AS max_updated
                FROM cpf
                GROUP BY cpf
            ) ult ON c.cpf = ult.cpf AND c.updated_at = ult.max_updated
            WHERE c.id = (
                SELECT MAX(c2.id) FROM cpf c2
                WHERE c2.cpf = c.cpf AND c2.updated_at = ult.max_updated
            );

            DROP TABLE cpf;
            ALTER TABLE cpf_new RENAME TO cpf;
            CREATE INDEX IF NOT EXISTS idx_cpf ON cpf(cpf);
            """
        )

    def _ensure_correios_unique(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_correios_chave_tipo
            ON correios(chave, tipo)
            """
        )

    def _ensure_config_keys(self, conn: sqlite3.Connection) -> None:
        defaults = {
            "cpf_consumed_total": "0",
            "cnpj_consumed_total": "0",
            "cep_consumed_total": "0",
            "correios_consumed_total": "0",
            "outros_consumed_total": "0",
        }
        now = _utc_now()
        for chave, valor in defaults.items():
            conn.execute(
                """
                INSERT OR IGNORE INTO config (chave, valor, updated_at)
                VALUES (?, ?, ?)
                """,
                (chave, valor, now),
            )

    def get_cpf(self, cpf: str, data_nascimento: str | None = None) -> dict[str, Any] | None:
        """
        1) Busca somente por CPF.
        2) Se não encontrar e houver data, busca por CPF + data_nascimento.
        """
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM cpf WHERE cpf = ? LIMIT 1",
                (cpf,),
            ).fetchone()

            if not row and data_nascimento:
                row = conn.execute(
                    """
                    SELECT * FROM cpf
                    WHERE cpf = ? AND data_nascimento = ?
                    LIMIT 1
                    """,
                    (cpf, data_nascimento),
                ).fetchone()

        if not row:
            return None
        return {
            "source": "local",
            "data": _payload_cache_local(json.loads(row["response_json"])),
            "updated_at": row["updated_at"],
        }

    def get_cep(self, cep: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM cep
                WHERE cep = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (cep,),
            ).fetchone()
        if not row:
            return None
        return {
            "source": "local",
            "data": _payload_cache_local(json.loads(row["response_json"])),
            "updated_at": row["updated_at"],
        }

    def get_cnpj(self, cnpj: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM cnpj WHERE cnpj = ? LIMIT 1",
                (cnpj,),
            ).fetchone()
        if not row:
            return None
        return {
            "source": "local",
            "data": _payload_cache_local(json.loads(row["response_json"])),
            "updated_at": row["updated_at"],
        }

    def save_cpf(
        self,
        cpf: str,
        data_nascimento: str | None,
        payload: dict[str, Any],
    ) -> None:
        now = _utc_now()
        consumed = int(payload.get("consumed") or 0)
        return_code = payload.get("return", "")
        message = payload.get("message", "")
        status = 1 if payload.get("status") else 0
        response_json = json.dumps(payload, ensure_ascii=False)

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO cpf (
                    cpf, data_nascimento, status, return_code, message,
                    consumed, response_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cpf) DO UPDATE SET
                    data_nascimento = excluded.data_nascimento,
                    status = excluded.status,
                    return_code = excluded.return_code,
                    message = excluded.message,
                    consumed = excluded.consumed,
                    response_json = excluded.response_json,
                    updated_at = excluded.updated_at
                """,
                (
                    cpf,
                    data_nascimento or "",
                    status,
                    return_code,
                    message,
                    consumed,
                    response_json,
                    now,
                    now,
                ),
            )

        self.register_consumption("cpf", cpf, consumed, origem="api")

    def save_cnpj(self, cnpj: str, payload: dict[str, Any]) -> None:
        now = _utc_now()
        consumed = int(payload.get("consumed") or 0)
        return_code = payload.get("return", "")
        message = payload.get("message", "")
        response_json = json.dumps(payload, ensure_ascii=False)

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO cnpj (
                    cnpj, return_code, message, consumed, response_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cnpj) DO UPDATE SET
                    return_code = excluded.return_code,
                    message = excluded.message,
                    consumed = excluded.consumed,
                    response_json = excluded.response_json,
                    updated_at = excluded.updated_at
                """,
                (
                    cnpj,
                    return_code,
                    message,
                    consumed,
                    response_json,
                    now,
                    now,
                ),
            )

        self.register_consumption("cnpj", cnpj, consumed, origem="api")

    def save_cep(self, cep: str, payload: dict[str, Any]) -> None:
        now = _utc_now()
        consumed = int(payload.get("consumed") or 0)
        return_code = payload.get("return", "")
        message = payload.get("message", "")
        response_json = json.dumps(payload, ensure_ascii=False)

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO cep (
                    cep, return_code, message, consumed, response_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cep) DO UPDATE SET
                    return_code = excluded.return_code,
                    message = excluded.message,
                    consumed = excluded.consumed,
                    response_json = excluded.response_json,
                    updated_at = excluded.updated_at
                """,
                (
                    cep,
                    return_code,
                    message,
                    consumed,
                    response_json,
                    now,
                    now,
                ),
            )

        self.register_consumption("cep", cep, consumed, origem="api")

    def get_correios(self, chave: str, tipo: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM correios
                WHERE chave = ? AND tipo = ?
                LIMIT 1
                """,
                (chave, tipo),
            ).fetchone()
        if not row:
            return None
        return {
            "source": "local",
            "data": _payload_cache_local(json.loads(row["response_json"])),
            "updated_at": row["updated_at"],
        }

    def save_correios(self, chave: str, tipo: str, payload: dict[str, Any]) -> None:
        now = _utc_now()
        consumed = int(payload.get("consumed") or 0)
        return_code = payload.get("return", "")
        message = payload.get("message", "")
        response_json = json.dumps(payload, ensure_ascii=False)

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO correios (
                    chave, tipo, return_code, message, consumed,
                    response_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chave, tipo) DO UPDATE SET
                    return_code = excluded.return_code,
                    message = excluded.message,
                    consumed = excluded.consumed,
                    response_json = excluded.response_json,
                    updated_at = excluded.updated_at
                """,
                (
                    chave,
                    tipo,
                    return_code,
                    message,
                    consumed,
                    response_json,
                    now,
                    now,
                ),
            )

        self.register_consumption("correios", chave, consumed, origem="api")

    def register_consumption(
        self,
        servico: str,
        chave: str | None,
        consumed: int,
        *,
        origem: str = "api",
    ) -> None:
        """Registra consumo apenas quando houve chamada à API com créditos."""
        if consumed <= 0 or origem != "api":
            return

        config_key = f"{servico}_consumed_total"
        now = _utc_now()

        with self._conn() as conn:
            row = conn.execute(
                "SELECT valor FROM config WHERE chave = ?", (config_key,)
            ).fetchone()
            total = int(row["valor"]) if row else 0
            new_total = total + consumed

            conn.execute(
                """
                UPDATE config SET valor = ?, updated_at = ?
                WHERE chave = ?
                """,
                (str(new_total), now, config_key),
            )
            conn.execute(
                """
                INSERT INTO consumo_log (servico, chave, consumed, origem, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (servico, chave or "", consumed, origem, now),
            )

    def get_consumed_totals(self) -> dict[str, int]:
        keys = ("cpf", "cnpj", "cep", "correios", "outros")
        totals: dict[str, int] = {}
        with self._conn() as conn:
            for servico in keys:
                row = conn.execute(
                    "SELECT valor FROM config WHERE chave = ?",
                    (f"{servico}_consumed_total",),
                ).fetchone()
                totals[servico] = int(row["valor"]) if row else 0
        return totals
