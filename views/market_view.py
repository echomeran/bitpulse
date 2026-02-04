import flet as ft
import requests
from datetime import datetime

price_cache = []
time_cache = []
live_price_ref = "$ --"
loading = False


# ---------------- API ----------------
def fetch_fng_data():
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=5)
        return r.json()["data"][0] if r.status_code == 200 else None
    except:
        return None


def fetch_btc_price_history(days="1"):
    global price_cache, time_cache

    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
    r = requests.get(url, timeout=7)
    if r.status_code != 200:
        return []

    prices = r.json().get("prices", [])
    if not prices:
        return []

    # Binance-style resolution scaling
    if days == "0.04":      # ~1H
        step = 1
    elif days == "1":       # 1D
        step = 1
    elif days == "7":       # 1W
        step = 3
    elif days == "30":      # 1M
        step = 12
    else:                   # 1Y
        step = 48

    sliced = prices[::step]
    time_cache = [p[0] for p in sliced]
    price_cache = [p[1] for p in sliced]

    return [ft.LineChartDataPoint(i, round(p, 2)) for i, p in enumerate(price_cache)]


# ---------------- UI ----------------
def market_view_component(page: ft.Page):
    global loading
    view_container = ft.Column(expand=True)

    # --- Fear & Greed ---
    fng_value = ft.Text("--", size=24, weight="bold")
    fng_label = ft.Text("Loading...", size=12, color=ft.Colors.GREY_500)

    # --- Header price ---
    current_price_label = ft.Text("$ --", size=32, weight="bold")
    current_time_label = ft.Text("Live Market", size=12, color=ft.Colors.GREY_500)

    # --- Crosshair overlay ---
    crosshair_line = ft.Container(width=1, bgcolor=ft.Colors.ORANGE_ACCENT, visible=False)
    crosshair_label = ft.Container(
        bgcolor="#222",
        padding=6,
        border_radius=6,
        visible=False,
        content=ft.Text("", size=11),
    )

    # --- Chart ---
    def create_chart():
        return ft.LineChart(
            data_series=[
                ft.LineChartData(
                    color=ft.Colors.ORANGE_ACCENT,
                    stroke_width=2,
                    curved=True,
                    below_line_bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ORANGE_ACCENT),
                )
            ],
            expand=True,
            interactive=True,
            left_axis=ft.ChartAxis(show_labels=True, labels_size=45),
            bottom_axis=ft.ChartAxis(show_labels=False),
            tooltip_bgcolor=ft.Colors.TRANSPARENT,
        )

    chart = create_chart()
    chart_stack = ft.Stack(expand=True, controls=[chart, crosshair_line, crosshair_label])

    # ---------------- CHART INTERACTION ----------------
    def on_chart_event(e: ft.LineChartEvent):
        global live_price_ref

        if not e.spots:
            crosshair_line.visible = False
            crosshair_label.visible = False
            current_price_label.value = live_price_ref
            current_time_label.value = "Live Market"
            page.update()
            return

        idx = e.spots[0][0].spot_index
        if idx >= len(price_cache):
            return

        price = price_cache[idx]
        ts = time_cache[idx]
        time_str = datetime.fromtimestamp(ts / 1000).strftime("%H:%M")

        current_price_label.value = f"${price:,.2f}"
        current_time_label.value = time_str

        crosshair_line.visible = True
        crosshair_label.visible = True

        chart_width = chart_stack.width or 320
        chart_height = chart_stack.height or 260
        x_pos = (idx / max(1, len(price_cache) - 1)) * chart_width

        crosshair_line.left = x_pos
        crosshair_line.top = 0
        crosshair_line.height = chart_height

        crosshair_label.left = max(0, x_pos - 22)
        crosshair_label.top = 8
        crosshair_label.content.value = time_str

        page.update()

    chart.on_chart_event = on_chart_event

    # ---------------- DATA UPDATE ----------------
    def update_chart_with_points(points):
        nonlocal chart, chart_stack
        chart = create_chart()
        chart.data_series[0].data_points = points
        chart.on_chart_event = on_chart_event
        chart_stack.controls[0] = chart

    def update_data(days):
        global live_price_ref, loading
        if loading:
            return
        loading = True

        points = fetch_btc_price_history(days)
        if points:
            update_chart_with_points(points)
            live_price_ref = f"${price_cache[-1]:,.2f}"
            current_price_label.value = live_price_ref
            current_time_label.value = "Live Market"

        loading = False
        page.update()

    def update_market_ui():
        fng = fetch_fng_data()
        if fng:
            fng_value.value = fng["value"]
            fng_label.value = fng["value_classification"]
            fng_value.color = ft.Colors.GREEN_ACCENT if int(fng["value"]) > 50 else ft.Colors.RED_ACCENT
        update_data("1")

    # ---------------- FULLSCREEN (REAL VIEW SWITCH) ----------------
    def open_full_screen(e):
        def back():
            view_container.controls.clear()
            view_container.controls.append(main_view)
            page.update()

        full_chart = create_chart()
        full_chart.data_series[0].data_points = chart.data_series[0].data_points
        full_chart.on_chart_event = on_chart_event

        full_stack = ft.Stack(expand=True, controls=[full_chart, crosshair_line, crosshair_label])

        layout = ft.Column(
            expand=True,
            controls=[
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: back()),
                    ft.Text("BTC / USD", size=18, weight="bold"),
                ]),
                ft.Container(expand=True, bgcolor="#0A0A0A", padding=10, content=full_stack),
                ft.Row([
                    ft.TextButton("1H", on_click=lambda _: update_data("0.04")),
                    ft.TextButton("1D", on_click=lambda _: update_data("1")),
                    ft.TextButton("1W", on_click=lambda _: update_data("7")),
                    ft.TextButton("1M", on_click=lambda _: update_data("30")),
                    ft.TextButton("1Y", on_click=lambda _: update_data("365")),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ],
        )

        view_container.controls.clear()
        view_container.controls.append(layout)
        page.update()

    # ---------------- MAIN VIEW ----------------
    main_view = ft.Column(
        expand=True,
        controls=[
            # Fear & Greed
            ft.Container(
                padding=20,
                content=ft.Container(
                    padding=15,
                    bgcolor="#1A1A1A",
                    border_radius=12,
                    content=ft.Row([
                        ft.Icon(ft.Icons.SPEED, color=ft.Colors.ORANGE_ACCENT, size=26),
                        ft.Column([
                            ft.Text("Sentiment Index", size=10, color=ft.Colors.GREY_500),
                            ft.Row([fng_value, fng_label], spacing=6),
                        ], spacing=0),
                    ])
                ),
            ),

            # Price + Chart
            ft.Container(
                padding=ft.padding.symmetric(horizontal=20),
                content=ft.Column([
                    ft.Text("BTC / USD", size=13, color=ft.Colors.GREY_500),
                    current_price_label,
                    current_time_label,
                    ft.Container(
                        height=280,
                        bgcolor="#1A1A1A",
                        border_radius=16,
                        padding=10,
                        content=ft.Stack([
                            chart_stack,
                            ft.Container(
                                alignment=ft.alignment.top_right,
                                content=ft.IconButton(
                                    icon=ft.Icons.FULLSCREEN,
                                    icon_color=ft.Colors.GREY_400,
                                    tooltip="Tam ekran",
                                    on_click=open_full_screen,
                                ),
                            ),
                        ]),
                    ),
                    ft.Row([
                        ft.TextButton("1H", on_click=lambda _: update_data("0.04")),
                        ft.TextButton("1D", on_click=lambda _: update_data("1")),
                        ft.TextButton("1W", on_click=lambda _: update_data("7")),
                        ft.TextButton("1M", on_click=lambda _: update_data("30")),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=6),
            ),
        ],
    )

    view_container.controls.append(main_view)
    return view_container, update_market_ui
