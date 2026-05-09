import flet as ft
import requests
import urllib3
import urllib3
from datetime import datetime
import flet as ftc
import time

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


def fetch_btc_price_history(period="1D"):
    global price_cache, time_cache

    config = {
        "1H": {"interval": "2m", "range": "1d", "slice": -30},  # Son 30 data (60dk)
        "1D": {"interval": "15m", "range": "1d", "slice": None},
        "1W": {"interval": "1h", "range": "1mo", "slice": -168}, # Son 168 saat (7 gün)
        "1M": {"interval": "1d", "range": "1mo", "slice": None}
    }
    
    cfg = config.get(period, config["1D"])
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD?interval={cfg['interval']}&range={cfg['range']}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            result = data.get("chart", {}).get("result", [])
            if result:
                timestamps = result[0].get("timestamp", [])
                indicators = result[0].get("indicators", {}).get("quote", [{}])[0]
                close_prices = indicators.get("close", [])
                
                valid_data = [(t, p) for t, p in zip(timestamps, close_prices) if p is not None]
                if cfg["slice"]:
                    valid_data = valid_data[cfg["slice"]:]
                    
                time_cache = [d[0] for d in valid_data]
                price_cache = [d[1] for d in valid_data]
                return [ftc.LineChartDataPoint(i, p) for i, p in enumerate(price_cache)]
    except Exception as e:
        print(f"Chart fetch error: {e}")
    
    return []


# ---------------- UI BİLEŞENİ ----------------
def market_view_component(page: ft.Page):
    global loading
    view_container = ft.Column(expand=True)

    fng_value = ft.Text("--", size=24, weight="bold")
    fng_label = ft.Text("Loading...", size=12, color=ft.Colors.GREY_500)
    fng_ring = ft.ProgressRing(width=40, height=40, stroke_width=5, value=0.0, bgcolor="#1E293B")
    current_price_label = ft.Text("$ --", size=32, weight="bold")
    current_time_label = ft.Text(
        "Waiting for data...", size=12, color=ft.Colors.GREY_500
    )
    high_label = ft.Text("High: --", size=12, color=ft.Colors.GREEN_400, weight="bold")
    low_label = ft.Text("Low: --", size=12, color=ft.Colors.RED_400, weight="bold")

    def create_chart(points=None):
        if points is None:
            points = []
        return ftc.LineChart(
            data_series=[
                ftc.LineChartData(
                    data_points=points,
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
            left_axis=ftc.ChartAxis(show_labels=False),
            bottom_axis=ftc.ChartAxis(show_labels=False),
            tooltip_bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.BLACK),
        )

    # Başlangıçta boş grafik oluşturmuyoruz, container bekleyecek
    chart_container = ft.Container(
        height=250,  # Statik yükseklik Flet'in siyah ekran / infinite height bug'ını kesin çözer
        expand=True,
        bgcolor="#0F172A",
        border_radius=20,
        padding=15,
        alignment=ft.alignment.center, # Dikey sosis gibi uzamasını önler
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=20, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
        content=ft.ProgressRing(width=40, height=40, color=ft.Colors.ORANGE_ACCENT) # Yükleniyor efekti
    )

    def update_data(period):
        global live_price_ref, loading
        if loading:
            return
        loading = True
        page.update()

        points = fetch_btc_price_history(period)

        if points and price_cache:
            try:
                # Yeni grafik objesini oluştur ve container'a ata (siyah ekranı kesin çözer)
                chart_container.content = create_chart(points)

                # 3. Başlıkları, fiyatı ve min/max değerlerini güncelle
                min_v, max_v = min(price_cache), max(price_cache)
                live_price_ref = f"${price_cache[-1]:,.2f}"
                current_price_label.value = live_price_ref
                high_label.value = f"High: ${max_v:,.2f}"
                low_label.value = f"Low: ${min_v:,.2f}"
                current_time_label.value = (
                    f"Live • {datetime.now().strftime('%H:%M:%S')}"
                )
                
                # Grafik güncellendiğinde container'ı tetikle
                if chart_container.page:
                    chart_container.update()
                else:
                    page.update() # Fallback

            except Exception as ex:
                print(f"Grafik çizim hatası: {ex}")
                current_time_label.value = f"Error: {ex}"
                current_time_label.color = ft.Colors.RED_ACCENT
        else:
            current_time_label.value = "Connection lost! Please check your internet."
            current_time_label.color = ft.Colors.RED_ACCENT

        loading = False
        page.update()

    def update_market_ui():
        fng = fetch_fng_data()
        if fng:
            val = int(fng["value"])
            fng_value.value = str(val)
            fng_label.value = fng["value_classification"]
            fng_color = ft.Colors.GREEN_ACCENT if val > 50 else (ft.Colors.ORANGE_ACCENT if val > 30 else ft.Colors.RED_ACCENT)
            fng_value.color = fng_color
            fng_ring.color = fng_color
            fng_ring.value = val / 100.0
        update_data("1D")

    main_view = ft.Column(
        expand=True,
        controls=[
            # Widgets Row (F&G + Halving)
            ft.Container(
                padding=ft.padding.only(left=20, right=20, top=20, bottom=10),
                content=ft.Row(
                    spacing=15,
                    controls=[
                        # Fear & Greed Card
                        ft.Container(
                            expand=True,
                            padding=15,
                            bgcolor="#0F172A",
                            border_radius=15,
                            shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)),
                            content=ft.Row(
                                [
                                    ft.Stack([fng_ring], alignment=ft.alignment.center),
                                    ft.Column(
                                        [
                                            ft.Text("Sentiment", size=10, color=ft.Colors.GREY_500, weight="bold"),
                                            ft.Row([fng_value, fng_label], spacing=6),
                                        ],
                                        spacing=0,
                                    ),
                                ]
                            ),
                        ),
                        # Halving Card
                        ft.Container(
                            expand=True,
                            padding=15,
                            bgcolor="#0F172A",
                            border_radius=15,
                            shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)),
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.BLUE_400, size=30),
                                    ft.Column(
                                        [
                                            ft.Text("Next Halving", size=10, color=ft.Colors.GREY_500, weight="bold"),
                                            ft.Text("~1390 Days", size=16, weight="bold", color=ft.Colors.WHITE),
                                        ],
                                        spacing=0,
                                    ),
                                ]
                            ),
                        ),
                    ]
                )
            ),
            # Grafik ve Fiyat Kartı
            ft.Container(
                padding=ft.padding.symmetric(horizontal=20),
                expand=True,
                content=ft.Column(
                    [
                        ft.Text("BTC / USD", size=13, color=ft.Colors.GREY_500),
                        current_price_label,
                        current_time_label,
                        ft.Row([high_label, low_label], spacing=15),
                        chart_container,
                        ft.Row(
                            [
                                ft.TextButton(
                                    "1H", on_click=lambda _: update_data("1H")
                                ),
                                ft.TextButton(
                                    "1D", on_click=lambda _: update_data("1D")
                                ),
                                ft.TextButton(
                                    "1W", on_click=lambda _: update_data("1W")
                                ),
                                ft.TextButton(
                                    "1M", on_click=lambda _: update_data("1M")
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
