# ========================
# Ukázka použití
# ========================
from api.mapy_client import MapyCZClient
from api.logger_file import logger

if __name__ == "__main__":
    client = MapyCZClient()

    logger.info("=== Route Weather Planner ===\n")

    # Výběr dopravního prostředku
    print("\nVyberte dopravní prostředek:")
    modes = list(MapyCZClient.TRANSPORT_MODES.items())
    for i, (label, _) in enumerate(modes, 1):
        print(f"  {i}) {label}")

    choice = input("\nZadejte číslo (1-3): ")
    try:
        mode = modes[int(choice) - 1][1]
        logger.info(mode)
    except (ValueError, IndexError):
        print("Neplatná volba, použiji auto.")
        mode = "car_fast"

    # Zadání počátečního bodu
    start_name = input("\nOdkud jedete (pokud chcete využít aktuální polohu, zmáčkněte enter): ")

    # Získání aktuální polohy
    if start_name.strip() == "":
        logger.info("⏳ Zjišťuji vaši polohu...")
        start_coords = client.get_current_location()
    else:
        start_coords = client.geocode(start_name)

    # Získání koncového bodu
    end_name = input("\nKam jedete: ")

    while end_name.strip() == "":
        end_name = input("\nKam jedete: ")

    end_coords = client.geocode(end_name)

    logger.info("⏳ Hledám trasu...")
    print("⏳ Hledám trasu...")

    # Vypočítání trasy a zobrazení výsledku
    if start_coords and end_coords:
        route = client.get_route(start_coords, end_coords, mode)
        logger.info("\n" + client.format_route(route))
        print("\n" + client.format_route(route))
    else:
        logger.warning("❌ Jednu nebo obě adresy se nepodařilo najít.")
        print("❌ Jednu nebo obě adresy se nepodařilo najít.")