import flet as ft
import requests
import urllib3
from datetime import datetime
import flet_charts as ftc

# Sertifika uyarılarını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Global Değişkenler ---
price_cache = []
time_cache = []
live_price_ref = "$ --"
loading = False
session = requests.Session()


# ---------------- API FONKSİYONLARI ----------------
def fetch_fng_data():
    try:
        r = session.get("https://api.alternative.me/fng/", timeout=5, verify=False)
        return r.json()["data"][0] if r.status_code == 200 else None
    except:
        return None


def fetch_btc_price_history(days="1"):
    global price_cache, time_cache

    intervals = {"0.04": "1m", "1": "15m", "7": "1h", "30": "4h", "365": "1d"}
    interval = intervals.get(days, "15m")

    # --- 1. SEÇENEK: BİNANCE (HIZLI) ---
    endpoints = [
        f"https://api3.binance.com/api/v3/klines",
        f"https://api1.binance.com/api/v3/klines",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0 Safari/537.36"
    }

    for url in endpoints:
        try:
            r = session.get(
                url,
                params={"symbol": "BTCUSDT", "interval": interval, "limit": 100},
                headers=headers,
                timeout=5,
                verify=False,
            )
            if r.status_code == 200:
                data = r.json()
                time_cache = [int(item[0]) for item in data]
                price_cache = [float(item[4]) for item in data]
                return [ftc.LineChartDataPoint(i, p) for i, p in enumerate(price_cache)]
        except:
            continue

    # --- 2. SEÇENEK: COINGECKO (YEDEK) ---
    # Eğer Binance 10054 verirse burası devreye girer
    try:
        cg_url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
        r = session.get(cg_url, timeout=10)
        if r.status_code == 200:
            prices = r.json().get("prices", [])
            step = 1 if days in ["0.04", "1"] else 12
            sliced = prices[::step]
            time_cache = [p[0] for p in sliced]
            price_cache = [p[1] for p in sliced]
            return [ftc.LineChartDataPoint(i, p) for i, p in enumerate(price_cache)]
    except:
        pass

    return []


# ---------------- UI BİLEŞENİ ----------------
def market_view_component(page: ft.Page):
    global loading
    view_container = ft.Column(expand=True)

    fng_value = ft.Text("--", size=24, weight="bold")
    fng_label = ft.Text("Loading...", size=12, color=ft.Colors.GREY_500)
    current_price_label = ft.Text("$ --", size=32, weight="bold")
    current_time_label = ft.Text(
        "Veri bekleniyor...", size=12, color=ft.Colors.GREY_500
    )

    def create_chart():
        return ftc.LineChart(
            data_series=[
                ftc.LineChartData(
                    color=ft.Colors.ORANGE_ACCENT,
                    stroke_width=2,
                    curved=True,
                    below_line_bgcolor=ft.Colors.with_opacity(
                        0.08, ft.Colors.ORANGE_ACCENT
                    ),
                )
            ],
            expand=True,
            interactive=True,
            # label_size=60 yaparak sayıların sığmasını garanti ediyoruz
            left_axis=ftc.ChartAxis(label_size=60, show_labels=True),
            bottom_axis=ftc.ChartAxis(show_labels=False),
            tooltip=ftc.LineChartTooltip(
                bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.BLACK)
            ),
        )

    chart = create_chart()

    def update_data(days):
        global live_price_ref, loading
        if loading:
            return
        loading = True
        page.update()

        points = fetch_btc_price_history(days)

        if points and price_cache:
            try:
                # 1. Veri noktalarını bas
                chart.data_series[0].points = points

                min_v, max_v = min(price_cache), max(price_cache)
                chart.min_y = min_v * 0.999
                chart.max_y = max_v * 1.001

                # 2. EKSENİ SIFIRDAN YARAT (Boş kalma sorununu bu çözer)
                # Sayıları beyaz yapıyoruz ve sola biraz daha geniş alan (label_size=65) veriyoruz.
                chart.left_axis = ftc.ChartAxis(
                    label_size=65,
                    show_labels=True,
                    labels=[
                        ftc.ChartAxisLabel(
                            value=min_v,
                            label=ft.Text(
                                f"{min_v/1000:.1f}K", color=ft.Colors.WHITE, size=11
                            ),
                        ),
                        ftc.ChartAxisLabel(
                            value=(min_v + max_v) / 2,
                            label=ft.Text(
                                f"{(min_v + max_v)/2000:.1f}K",
                                color=ft.Colors.WHITE,
                                size=11,
                            ),
                        ),
                        ftc.ChartAxisLabel(
                            value=max_v,
                            label=ft.Text(
                                f"{max_v/1000:.1f}K", color=ft.Colors.WHITE, size=11
                            ),
                        ),
                    ],
                )

                # 3. Başlıkları ve fiyatı güncelle
                live_price_ref = f"${price_cache[-1]:,.2f}"
                current_price_label.value = live_price_ref
                current_time_label.value = (
                    f"Canlı • {datetime.now().strftime('%H:%M:%S')}"
                )

                chart.update()  # Grafiği zorla yenile
            except Exception as ex:
                print(f"Grafik çizim hatası: {ex}")
        else:
            current_time_label.value = "Bağlantı koptu! Lütfen interneti kontrol edin."
            current_time_label.color = ft.Colors.RED_ACCENT

        loading = False
        page.update()

    def update_market_ui():
        fng = fetch_fng_data()
        if fng:
            fng_value.value = fng["value"]
            fng_label.value = fng["value_classification"]
            fng_value.color = (
                ft.Colors.GREEN_ACCENT
                if int(fng["value"]) > 50
                else ft.Colors.RED_ACCENT
            )
        update_data("1")

    main_view = ft.Column(
        expand=True,
        controls=[
            # Korku Endeksi Kartı
            ft.Container(
                padding=20,
                content=ft.Container(
                    padding=15,
                    bgcolor="#1A1A1A",
                    border_radius=12,
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.SPEED, color=ft.Colors.ORANGE_ACCENT, size=26
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Piyasa Duyarlılığı",
                                        size=10,
                                        color=ft.Colors.GREY_500,
                                    ),
                                    ft.Row([fng_value, fng_label], spacing=6),
                                ],
                                spacing=0,
                            ),
                        ]
                    ),
                ),
            ),
            # Grafik ve Fiyat Kartı
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=20),
                expand=True,
                content=ft.Column(
                    [
                        ft.Text("BTC / USD", size=13, color=ft.Colors.GREY_500),
                        current_price_label,
                        current_time_label,
                        ft.Container(
                            expand=True,
                            bgcolor="#1A1A1A",
                            border_radius=16,
                            padding=15,
                            content=chart,
                        ),
                        ft.Row(
                            [
                                ft.TextButton(
                                    "1S", on_click=lambda _: update_data("0.04")
                                ),
                                ft.TextButton(
                                    "1G", on_click=lambda _: update_data("1")
                                ),
                                ft.TextButton(
                                    "1H", on_click=lambda _: update_data("7")
                                ),
                                ft.TextButton(
                                    "1A", on_click=lambda _: update_data("30")
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=10,
                ),
            ),
        ],
    )

    view_container.controls.append(main_view)
    return view_container, update_market_ui
