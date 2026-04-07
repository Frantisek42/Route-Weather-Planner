import requests
import os
from dotenv import load_dotenv
from api.logger_file import logger

load_dotenv()


class MapyCZClient:
    """
    Třída pro komunikaci s Mapy.cz API.
    Ověřuje existence adres a vypočítává trasy.
    """

    TRANSPORT_MODES = {
        "🚗 Auto": "car_fast",
        "🚶 Pěšky": "foot_fast",
        "🚲 Kolo": "bike_road",
    }

    def __init__(self):
        self.api_key = os.getenv("MAPY_CZ_API_KEY")
        self.geocode_url = "https://api.mapy.cz/v1/geocode"
        self.routing_url = "https://api.mapy.cz/v1/routing/route"

    def get_current_location(self) -> tuple[float, float] | None:
        """
        Získá přibližnou polohu uživatele podle IP adresy.
        """
        try:
            response = requests.get("http://ip-api.com/json/", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data["status"] == "success":
                logger.info(f"✅ Poloha získána: {data['city']}, {data['country']}")
                print(f"✅ Poloha získána: {data['city']}, {data['country']}")
                return data["lat"], data["lon"]
            else:
                logger.warning("Polohu se nepodařilo zjistit.")
                print("Polohu se nepodařilo zjistit.")
                return None

        except requests.exceptions.ConnectionError:
            logger.error("Chyba: Není připojení k internetu.")
            return None
        except requests.exceptions.Timeout:
            logger.error("Chyba: Požadavek vypršel (timeout).")
            return None

    def geocode(self, place_name: str) -> tuple[float, float] | None:
        """
        Převede název místa na souřadnice.
        Vrací (lat, lon) nebo None pokud místo neexistuje.
        """
        try:
            response = requests.get(
                self.geocode_url,
                params={
                    "query": place_name,
                    "apikey": self.api_key,
                    "lang": "cs",
                    "limit": 1,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if not items:
                logger.warning(f"Místo '{place_name}' nebylo nalezeno.")
                return None

            pos = items[0]["position"]
            return pos["lat"], pos["lon"]

        except requests.exceptions.ConnectionError:
            logger.error("Chyba: Není připojení k internetu.")
            return None
        except requests.exceptions.Timeout:
            logger.error("Chyba: Požadavek vypršel (timeout).")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"Chyba HTTP: {e}")
            return None

    def get_route(self, start: tuple, end: tuple, mode: str) -> dict | None:
        """
        Vypočítá trasu mezi dvěma body.
        Vrací slovník s délkou a dobou trasy nebo None při chybě.
        """
        try:
            response = requests.get(
                self.routing_url,
                params={
                    "apikey": self.api_key,
                    "start": f"{start[1]},{start[0]}",
                    "end": f"{end[1]},{end[0]}",
                    "routeType": mode,
                    "lang": "cs",
                },
                timeout=10,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            logger.error("Chyba: Není připojení k internetu.")
            return None
        except requests.exceptions.Timeout:
            logger.error("Chyba: Požadavek vypršel (timeout).")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"Chyba HTTP: {e}")
            return None

    def format_route(self, route_data: dict) -> str:
        """
        Naformátuje data trasy do čitelného řetězce.
        """
        if not route_data:
            return "Trasu se nepodařilo vypočítat."

        distance_m = route_data.get("length", 0)
        duration_s = route_data.get("duration", 0)

        distance_km = distance_m / 1000
        duration_min = duration_s // 60
        hours = duration_min // 60
        minutes = duration_min % 60

        if hours > 0:
            time_str = f"{hours} hod {minutes} min"
        else:
            time_str = f"{minutes} min"

        return (
            f"📏 Vzdálenost: {distance_km:.1f} km\n"
            f"⏱️  Doba jízdy: {time_str}"
        )