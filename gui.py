import customtkinter as ctk
from datetime import datetime, timedelta
from api.mapy_client import MapyCZClient
from api.weather_client import WeatherClient
from api.logger_file import logger
from db.routes_db import RoutesDB
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RouteWeatherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.client = MapyCZClient()
        self.weather = WeatherClient()
        self.db = RoutesDB()

        self.title("🗺️ Route Weather Planner")
        self.geometry("700x900")
        self.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        # ── Nadpis ──
        header = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="🗺️  Route Weather Planner",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#4fc3f7"
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            header,
            text="Zadej trasu a zjisti vzdálenost i počasí po cestě",
            font=ctk.CTkFont(size=12),
            text_color="#90a4ae"
        ).pack(pady=(0, 14))

        # ── Vstupní sekce ──
        input_frame = ctk.CTkFrame(self, corner_radius=12)
        input_frame.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(input_frame, text="📍 Trasa", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(input_frame, text="Odkud:").grid(row=1, column=0, sticky="w", padx=16, pady=4)
        self.start_entry = ctk.CTkEntry(input_frame, width=380, placeholder_text="Praha nebo nechej prázdné pro aktuální polohu")
        self.start_entry.grid(row=1, column=1, padx=(0, 16), pady=4, sticky="w")

        ctk.CTkLabel(input_frame, text="Kam:").grid(row=2, column=0, sticky="w", padx=16, pady=4)
        self.end_entry = ctk.CTkEntry(input_frame, width=380, placeholder_text="Zadejte kam chete jet")
        self.end_entry.grid(row=2, column=1, padx=(0, 16), pady=4, sticky="w")

        ctk.CTkLabel(input_frame, text="Doprava:").grid(row=3, column=0, sticky="w", padx=16, pady=4)
        self.transport_var = ctk.StringVar(value="🚗 Auto")
        self.transport_menu = ctk.CTkOptionMenu(
            input_frame,
            values=list(MapyCZClient.TRANSPORT_MODES.keys()),
            variable=self.transport_var,
            width=200
        )
        self.transport_menu.grid(row=3, column=1, padx=(0, 16), pady=4, sticky="w")

        ctk.CTkLabel(input_frame, text="Odjezd:").grid(row=4, column=0, sticky="w", padx=16, pady=4)
        departure_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        departure_frame.grid(row=4, column=1, padx=(0, 16), pady=4, sticky="w")

        self.departure_var = ctk.StringVar(value="Nyní")
        self.departure_menu = ctk.CTkOptionMenu(
            departure_frame,
            values=["Nyní", "Zadat čas"],
            variable=self.departure_var,
            width=120,
            command=self._toggle_time_entry
        )
        self.departure_menu.pack(side="left", padx=(0, 8))

        self.time_entry = ctk.CTkEntry(departure_frame, width=160, placeholder_text="15.02.2026 12:00")
        self.time_entry.pack(side="left")
        self.time_entry.configure(state="disabled")

        ctk.CTkLabel(input_frame, text="Optimalizace:").grid(row=5, column=0, sticky="w", padx=16, pady=(4, 12))
        self.opt_var = ctk.StringVar(value="Vyrazit za hezkého počasí")
        self.opt_menu = ctk.CTkOptionMenu(
            input_frame,
            values=["Vyrazit za hezkého počasí", "Přijet za hezkého počasí", "Pouze předpověď"],
            variable=self.opt_var,
            width=260
        )
        self.opt_menu.grid(row=5, column=1, padx=(0, 16), pady=(4, 12), sticky="w")

        # ── Tlačítka ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(4, 4))

        self.search_btn = ctk.CTkButton(
            btn_frame,
            text="🔍  Vypočítat trasu a počasí",
            command=self._start_calculation,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0288d1",
            hover_color="#01579b"
        )
        self.search_btn.pack(fill="x", pady=(0, 6))

        db_btn_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        db_btn_frame.pack(fill="x")

        self.save_btn = ctk.CTkButton(
            db_btn_frame,
            text="💾 Uložit trasu",
            command=self._save_route,
            height=36,
            fg_color="#2e7d32",
            hover_color="#1b5e20"
        )
        self.save_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.load_btn = ctk.CTkButton(
            db_btn_frame,
            text="📂 Načíst trasu",
            command=self._load_route,
            height=36,
            fg_color="#5d4037",
            hover_color="#3e2723"
        )
        self.load_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # ── Status ──
        self.status_label = ctk.CTkLabel(
            self,
            text="Zadej trasu a klikni na tlačítko.",
            font=ctk.CTkFont(size=12),
            text_color="#90a4ae"
        )
        self.status_label.pack(pady=(6, 0))

        # ── Výsledky ──
        result_frame = ctk.CTkFrame(self, corner_radius=12)
        result_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        ctk.CTkLabel(result_frame, text="📊 Výsledky", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=16, pady=(12, 4))

        self.result_text = ctk.CTkTextbox(
            result_frame,
            font=ctk.CTkFont(family="Courier New", size=12),
            state="disabled",
            wrap="word"
        )
        self.result_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _toggle_time_entry(self, value):
        if value == "Zadat čas":
            self.time_entry.configure(state="normal")
        else:
            self.time_entry.configure(state="disabled")

    def _validate_departure_time(self, departure_time: datetime) -> bool:
        """Zkontroluje zda je čas odjezdu v rozsahu předpovědi (max 5 dní)."""
        max_date = datetime.now() + timedelta(days=5)
        if departure_time > max_date:
            msg = (
                f"❌ OpenWeatherMap poskytuje předpověď pouze na 5 dní dopředu.\n"
                f"   Zadej datum do: {max_date.strftime('%d.%m.%Y %H:%M')}"
            )
            self._append_result(msg)
            self._set_status("❌ Neplatné datum.")
            logger.warning(f"Datum odjezdu mimo rozsah předpovědi: {departure_time}")
            return False
        return True

    def _save_route(self):
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        transport = self.transport_var.get()

        if not start or not end:
            self._set_status("❌ Vyplň odkud a kam před uložením.")
            return

        name = f"{start} → {end}"
        if self.db.route_exists(start, end):
            self._set_status("⚠️ Tato trasa je již uložena.")
            return

        if self.db.save_route(name, start, end, transport):
            self._set_status(f"✅ Trasa '{name}' uložena.")
        else:
            self._set_status("❌ Nepodařilo se uložit trasu.")

    def _load_route(self):
        routes = self.db.get_all_routes()
        if not routes:
            self._set_status("⚠️ Žádné uložené trasy.")
            return

        window = ctk.CTkToplevel(self)
        window.title("📂 Uložené trasy")
        window.geometry("440x360")
        window.grab_set()

        ctk.CTkLabel(window, text="Vyberte trasu:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=12)

        scroll = ctk.CTkScrollableFrame(window)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        for route in routes:
            frame = ctk.CTkFrame(scroll)
            frame.pack(fill="x", pady=4)

            ctk.CTkLabel(
                frame,
                text=f"{route['name']}  |  {route['transport']}",
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10, pady=6)

            ctk.CTkButton(
                frame, text="🗑️", width=40,
                fg_color="#c62828", hover_color="#b71c1c",
                command=lambda r=route: self._delete_route(r, window)
            ).pack(side="right", padx=4, pady=4)

            ctk.CTkButton(
                frame, text="Načíst", width=80,
                command=lambda r=route: self._apply_route(r, window)
            ).pack(side="right", padx=4, pady=4)

    def _apply_route(self, route: dict, window):
        self.start_entry.delete(0, "end")
        self.start_entry.insert(0, route["start"])
        self.end_entry.delete(0, "end")
        self.end_entry.insert(0, route["end"])
        self.transport_var.set(route["transport"])
        window.destroy()
        self._set_status(f"✅ Trasa '{route['name']}' načtena.")
        logger.info(f"Načtena uložená trasa: {route['name']}")

    def _delete_route(self, route: dict, window):
        if self.db.delete_route(route["id"]):
            window.destroy()
            self._set_status(f"🗑️ Trasa '{route['name']}' smazána.")
        else:
            self._set_status("❌ Nepodařilo se smazat trasu.")

    def _start_calculation(self):
        self.search_btn.configure(state="disabled", text="⏳  Počítám...")
        self.status_label.configure(text="⏳ Zpracovávám...")
        self._clear_results()
        thread = threading.Thread(target=self._calculate, daemon=True)
        thread.start()

    def _calculate(self):
        try:
            # Odkud
            start_name = self.start_entry.get().strip()
            if start_name == "":
                self._set_status("⏳ Zjišťuji vaši polohu...")
                start_coords = self.client.get_current_location()
            else:
                start_coords = self.client.geocode(start_name)

            # Kam
            end_name = self.end_entry.get().strip()
            if not end_name:
                self._append_result("❌ Zadej cílové město.")
                return
            end_coords = self.client.geocode(end_name)

            if not start_coords or not end_coords:
                self._append_result("❌ Jednu nebo obě adresy se nepodařilo najít.")
                return

            # Čas odjezdu
            if self.departure_var.get() == "Zadat čas":
                try:
                    departure_time = datetime.strptime(self.time_entry.get(), "%d.%m.%Y %H:%M")
                except ValueError:
                    self._append_result("❌ Neplatný formát času. Použij DD.MM.YYYY HH:MM")
                    return
            else:
                departure_time = datetime.now()

            # Validace času
            if not self._validate_departure_time(departure_time):
                return

            # Dopravní prostředek
            mode = MapyCZClient.TRANSPORT_MODES[self.transport_var.get()]

            # Trasa
            self._set_status("⏳ Hledám trasu...")
            route = self.client.get_route(start_coords, end_coords, mode)
            if not route:
                self._append_result("❌ Trasu se nepodařilo vypočítat.")
                return

            route_info = self.client.format_route(route)
            self._append_result("─" * 45)
            self._append_result(route_info)
            logger.info(route_info)

            # Počasí
            self._set_status("⏳ Zjišťuji počasí...")
            duration_seconds = route["parts"][0]["duration"]
            arrival_time = departure_time + timedelta(seconds=duration_seconds)

            mid_coords = (
                (start_coords[0] + end_coords[0]) / 2,
                (start_coords[1] + end_coords[1]) / 2
            )

            self._append_result("\n🌤️  Počasí na trase:")
            self._append_result("─" * 45)

            bad_weather_found = False
            for label, coords in [("🚀 Start", start_coords), ("🛣️  Počasí na trase", mid_coords), ("🏁 Počasí při příjezdu", end_coords)]:
                forecast = self.weather.get_forecast(*coords)
                item = self.weather.get_weather_at_time(forecast, departure_time)
                weather_info = self.weather.format_weather_item(item, label)
                self._append_result(weather_info)
                logger.info(weather_info)

                if self.weather.is_bad_weather(item) and not bad_weather_found:
                    bad_weather_found = True
                    logger.warning(f"Špatné počasí detekováno: {label}")

            # Optimalizace
            self._append_result("\n" + "─" * 45)
            opt = self.opt_var.get()

            if opt == "Vyrazit za hezkého počasí":
                if bad_weather_found:
                    forecast_start = self.weather.get_forecast(*start_coords)
                    optimal = self.weather.find_optimal_departure(forecast_start, departure_time)
                    if optimal:
                        msg = f"⚠️  Lepší čas odjezdu: {optimal.strftime('%d.%m.%Y %H:%M')}"
                        logger.warning(msg)
                    else:
                        msg = "⚠️  Špatné počasí na celých 5 dní dopředu!"
                        logger.warning(msg)
                else:
                    msg = "✅ Počasí na trase je v pořádku, vyrazte dle plánu!"
                    logger.info(msg)
                self._append_result(msg)

            elif opt == "Přijet za hezkého počasí":
                forecast_end = self.weather.get_forecast(*end_coords)
                result = self.weather.find_optimal_arrival(forecast_end, duration_seconds)
                if result:
                    optimal_departure, optimal_arrival = result
                    msg1 = f"🏁 Pro hezký příjezd vyrazte: {optimal_departure.strftime('%d.%m.%Y %H:%M')}"
                    msg2 = f"   Příjezd v: {optimal_arrival.strftime('%d.%m.%Y %H:%M')}"
                    self._append_result(msg1)
                    self._append_result(msg2)
                    logger.info(msg1)
                    logger.info(msg2)
                else:
                    msg = "⚠️  Hezké počasí v cíli nenalezeno na 5 dní dopředu."
                    self._append_result(msg)
                    logger.warning(msg)

            else:
                if bad_weather_found:
                    msg = "⚠️  Na trase se vyskytuje špatné počasí."
                    logger.warning(msg)
                else:
                    msg = "✅ Počasí na celé trase je v pořádku!"
                    logger.info(msg)
                self._append_result(msg)

            self._set_status("✅ Hotovo!")

        except Exception as e:
            logger.error(f"Neočekávaná chyba: {e}")
            self._append_result(f"❌ Neočekávaná chyba: {e}")
            self._set_status("❌ Chyba.")
        finally:
            self.after(0, lambda: self.search_btn.configure(state="normal", text="🔍  Vypočítat trasu a počasí"))

    def _append_result(self, text: str):
        def _update():
            self.result_text.configure(state="normal")
            self.result_text.insert("end", text + "\n")
            self.result_text.configure(state="disabled")
            self.result_text.see("end")
        self.after(0, _update)

    def _clear_results(self):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.configure(state="disabled")

    def _set_status(self, text: str):
        self.after(0, lambda: self.status_label.configure(text=text))


if __name__ == "__main__":
    app = RouteWeatherApp()
    app.mainloop()