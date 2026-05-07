import sqlite3
from api.logger_file import logger


class RoutesDB:
    """
    Třída pro správu databáze uložených tras.
    """

    def __init__(self, db_path: str = "routes.db"):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        """Vytvoří tabulku tras pokud neexistuje."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS routes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        start TEXT NOT NULL,
                        end TEXT NOT NULL,
                        transport TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info("Databáze inicializována.")
        except sqlite3.Error as e:
            logger.error(f"Chyba při vytváření tabulky: {e}")

    def save_route(self, name: str, start: str, end: str, transport: str) -> bool:
        """
        Uloží trasu do databáze.
        Vrací True při úspěchu, False při chybě.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO routes (name, start, end, transport) VALUES (?, ?, ?, ?)",
                    (name, start, end, transport)
                )
                conn.commit()
                logger.info(f"Trasa uložena: {name} ({start} → {end})")
                return True
        except sqlite3.Error as e:
            logger.error(f"Chyba při ukládání trasy: {e}")
            return False

    def get_all_routes(self) -> list[dict]:
        """
        Vrátí všechny uložené trasy jako list slovníků.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id, name, start, end, transport, created_at FROM routes ORDER BY created_at DESC"
                )
                rows = cursor.fetchall()
                return [
                    {"id": r[0], "name": r[1], "start": r[2], "end": r[3], "transport": r[4], "created_at": r[5]}
                    for r in rows
                ]
        except sqlite3.Error as e:
            logger.error(f"Chyba při načítání tras: {e}")
            return []

    def delete_route(self, route_id: int) -> bool:
        """
        Smaže trasu podle ID.
        Vrací True při úspěchu, False při chybě.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM routes WHERE id = ?", (route_id,))
                conn.commit()
                logger.info(f"Trasa ID {route_id} smazána.")
                return True
        except sqlite3.Error as e:
            logger.error(f"Chyba při mazání trasy: {e}")
            return False

    def route_exists(self, start: str, end: str) -> bool:
        """
        Zkontroluje zda trasa již existuje v databázi.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM routes WHERE start = ? AND end = ?",
                    (start, end)
                )
                return cursor.fetchone()[0] > 0
        except sqlite3.Error as e:
            logger.error(f"Chyba při kontrole trasy: {e}")
            return False