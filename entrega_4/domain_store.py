import sqlite3
from contextlib import contextmanager
from pathlib import Path


class ScoutingStore:
    """Persistent SQLite ledger for explicitly requested scouting follow-up notes."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scouting_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player TEXT NOT NULL,
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                )
                """
            )

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def add_note(self, player: str, note: str) -> int:
        """Persist one scouting note and return its database ID."""
        player = player.strip()
        note = note.strip()
        if not player or len(player) > 120:
            raise ValueError("El jugador debe tener entre 1 y 120 caracteres.")
        if not note or len(note) > 1000:
            raise ValueError("La nota debe tener entre 1 y 1000 caracteres.")
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO scouting_notes (player, note) VALUES (?, ?)",
                (player, note),
            )
            return int(cursor.lastrowid)

    def list_notes(self, player: str, limit: int = 20) -> list[dict[str, object]]:
        """Read the most recent saved scouting notes for a player."""
        if not player.strip() or len(player) > 120:
            raise ValueError("El jugador debe tener entre 1 y 120 caracteres.")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, player, note, created_at
                FROM scouting_notes
                WHERE player = ? COLLATE NOCASE
                ORDER BY id DESC
                LIMIT ?
                """,
                (player.strip(), limit),
            ).fetchall()
        return [
            {"id": row[0], "jugador": row[1], "nota": row[2], "creado_en": row[3]}
            for row in rows
        ]
