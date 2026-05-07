import requests
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from api.logger_file import logger

load_dotenv()


class WeatherClient:
    """
    Třída pro komunikaci s OpenWeatherMap API.
    Získává předpověď počasí a navrhuje optimální čas odjezdu.
    """

    BAD_CONDITIONS = ["thunderstorm", "drizzle", "rain", "snow", "sleet", "fog", "storm"]

    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        self.units = "metric"
        self.language = "cz"

    def get_forecast(self, lat: float, lon: float) -> list | None:
        """
        Získá předpověď počasí po 3 hodinách na 5 dní.
        Vrací list předpovědí nebo None při chybě.
        """
        try:
            response = requests.get(
                self.forecast_url,
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": self.units,
                    "lang": self.language,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("list", [])

        except requests.exceptions.ConnectionError:
            logger.error("Chyba: Není připojení k internetu.")
            return None
        except requests.exceptions.Timeout:
            logger.error("Chyba: Požadavek vypršel (timeout).")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"Chyba HTTP: {e}")
            return None

    def get_weather_at_time(self, forecast: list, departure_time: datetime) -> dict | None:
        """
        Najde předpověď počasí nejblíže zadanému času odjezdu.
        """
        if not forecast:
            return None

        closest = None
        min_diff = float("inf")

        for item in forecast:
            item_time = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone().replace(tzinfo=None)
            diff = abs((item_time - departure_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest = item

        return closest

    def is_bad_weather(self, weather_item: dict) -> bool:
        """
        Zkontroluje zda předpověď obsahuje špatné počasí.
        """
        if not weather_item:
            return False
        condition = weather_item["weather"][0]["main"].lower()
        return any(bad in condition for bad in self.BAD_CONDITIONS)

    def find_optimal_departure(self, forecast: list, departure_time: datetime) -> datetime | None:
        """
        Najde nejbližší čas s hezkým počasím po zadaném čase odjezdu.
        Prohledá předpověď po 3hodinových blocích.
        Vrací optimální čas odjezdu nebo None pokud je všude špatné počasí.
        """
        if not forecast:
            return None

        for item in forecast:
            item_time = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone().replace(tzinfo=None)

            # Hledáme pouze časy po plánovaném odjezdu A v budoucnosti
            if item_time < departure_time or item_time < datetime.now():
                continue

            if not self.is_bad_weather(item):
                return item_time

        return None

    def format_weather_item(self, weather_item: dict, label: str) -> str:
        """
        Naformátuje jeden záznam předpovědi do čitelného řetězce.
        """
        if not weather_item:
            return f"{label}\n  Data nedostupná."

        desc = weather_item["weather"][0]["description"].capitalize()
        temp = weather_item["main"]["temp"]
        feels_like = weather_item["main"]["feels_like"]
        humidity = weather_item["main"]["humidity"]
        wind = weather_item["wind"]["speed"]

        return (
            f"{label}\n"
            f"  🌡️  Teplota: {temp:.1f}°C (pocitová {feels_like:.1f}°C)\n"
            f"  🌤️  Počasí: {desc}\n"
            f"  💧  Vlhkost: {humidity}%\n"
            f"  💨  Vítr: {wind} m/s"
        )

    def find_optimal_arrival(self, forecast: list, duration_seconds: int) -> tuple[datetime, datetime] | None:
        """
        Najde nejbližší čas příjezdu s hezkým počasím.
        Odečte dobu jízdy a vrátí (čas odjezdu, čas příjezdu).
        """
        if not forecast:
            return None

        duration = timedelta(seconds=duration_seconds)

        for item in forecast:
            item_time = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone().replace(tzinfo=None)

            # Pouze budoucí časy
            if item_time < datetime.now():
                continue

            # Našli jsme okno hezkého počasí v cíli
            if not self.is_bad_weather(item):
                departure = item_time - duration

                # Odjezd musí být také v budoucnosti
                if departure < datetime.now():
                    continue

                return departure, item_time

        return None