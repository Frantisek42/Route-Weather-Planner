# ========================
# Ukázka použití
# ========================
from api.mapy_client import MapyCZClient

if __name__ == "__main__":
    client = MapyCZClient()

    print("=== Route Weather Planner ===\n")

    start_name = input("Odkud jedete: ")
    end_name = input("Kam jedete: ")

    print("\n⏳ Hledám trasu...")

    start_coords = client.geocode(start_name)
    end_coords = client.geocode(end_name)

    if start_coords and end_coords:
        route = client.get_route(start_coords, end_coords)
        print("\n" + client.format_route(route))
    else:
        print("❌ Jednu nebo obě adresy se nepodařilo najít.")