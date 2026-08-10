import flet as ft
import threading
from datetime import datetime, timezone

from services.ai_service import get_api_url
from services.market_service import (
    fetch_price_from_api,
    load_cached_market,
    save_market_cache,
)
import services.market_service as market_service


def market_view_component(page: ft.Page):
    loading = False
    view_container = ft.Column(expand=True)

    fng_value = ft.Text(
        "--",
        size=24,
        weight="bold",
        animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
    )
    fng_label = ft.Text("Loading...", size=12, color=ft.Colors.GREY_500)
    fng_ring = ft.ProgressRing(
        width=40, height=40, stroke_width=5, value=0.0, bgcolor="#1E293B"
    )

    current_price_label = ft.Text(
        "$ --",
        size=32,
        weight="bold",
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
    )

    change_label = ft.Text(
        "",
        size=13,
        weight="bold",
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
    )

    current_time_label = ft.Text(
        "Waiting for data...", size=12, color=ft.Colors.GREY_500
    )
    high_label = ft.Text("High: --", size=12, color=ft.Colors.GREEN_400, weight="bold")
    low_label = ft.Text("Low: --", size=12, color=ft.Colors.RED_400, weight="bold")

    selected_period = {"value": "1D"}

    retry_container = ft.Container(
        content=ft.OutlinedButton(
            "Retry",
            icon=ft.Icons.REFRESH_ROUNDED,
            on_click=lambda _: threading.Thread(
                target=update_data,
                args=(selected_period["value"],),
                daemon=True,
            ).start(),
        ),
        alignment=ft.alignment.center,
        visible=False,
    )

    chart_data_series = ft.LineChartData(
        data_points=[],
        color=ft.Colors.ORANGE_ACCENT,
        stroke_width=2,
        curved=True,
        below_line_bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ORANGE_ACCENT),
    )

    persistent_chart = ft.LineChart(
        data_series=[chart_data_series],
        animate=ft.Animation(800, ft.AnimationCurve.EASE_IN_OUT_CUBIC),
        expand=True,
        interactive=True,
        left_axis=ft.ChartAxis(show_labels=False),
        bottom_axis=ft.ChartAxis(show_labels=False),
        tooltip_bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.BLACK),
    )

    chart_container = ft.Container(
        height=220,
        expand=True,
        bgcolor="#0F172A",
        border_radius=20,
        padding=15,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
        ),
        content=ft.ProgressRing(width=36, height=36, color=ft.Colors.ORANGE_ACCENT),
    )

    period_buttons = {}

    def make_period_button(label):
        btn = ft.Container(
            content=ft.Text(label, size=13, weight="bold", color=ft.Colors.GREY_500),
            padding=ft.padding.symmetric(horizontal=14, vertical=6),
            border_radius=20,
            bgcolor="transparent",
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            on_click=lambda _, p=label: threading.Thread(
                target=update_data, args=(p,), daemon=True
            ).start(),
            ink=True,
        )
        period_buttons[label] = btn
        return btn

    def set_active_period(period):
        for p, btn in period_buttons.items():
            if p == period:
                btn.bgcolor = ft.Colors.ORANGE_ACCENT
                btn.content.color = ft.Colors.WHITE
            else:
                btn.bgcolor = "transparent"
                btn.content.color = ft.Colors.GREY_500
            if btn.page:
                btn.update()

    def _apply_market_data(data: dict, is_first_load: bool):
        """Apply fetched market data to all UI elements."""
        prices = data.get("prices", [])
        if not prices:
            return

        last_price = data.get("current_price") or prices[-1]
        change_pct = data.get("change_pct", 0.0)
        high = data.get("high") or max(prices)
        low = data.get("low") or min(prices)

        market_service.live_price_ref = f"${last_price:,.2f}"

        # Animate price
        current_price_label.opacity = 0
        change_label.opacity = 0
        if current_price_label.page:
            current_price_label.update()
            change_label.update()

        current_price_label.value = market_service.live_price_ref
        change_label.value = (
            f"{'▲' if change_pct >= 0 else '▼'} {abs(change_pct):.2f}%"
        )
        change_label.color = (
            ft.Colors.GREEN_400 if change_pct >= 0 else ft.Colors.RED_400
        )
        high_label.value = f"High: ${high:,.2f}"
        low_label.value = f"Low: ${low:,.2f}"
        current_time_label.value = f"Live • {datetime.now().strftime('%H:%M:%S')}"
        current_time_label.color = ft.Colors.GREY_500

        # Build chart points with normalized X axis (0 to 100) for smooth morphing
        n = len(prices)
        if n > 1:
            points = [
                ft.LineChartDataPoint((i / (n - 1)) * 100, p, tooltip=f"${p:,.2f}") for i, p in enumerate(prices)
            ]
        else:
            points = [ft.LineChartDataPoint(0, prices[0])] if prices else []

        # Configure chart limits and padding
        padding = (high - low) * 0.05 if high > low else (high * 0.05 if high else 1)
        persistent_chart.min_y = low - padding
        persistent_chart.max_y = high + padding
        persistent_chart.min_x = 0
        persistent_chart.max_x = 100

        # Right Axis (Price labels)
        mid_p = (high + low) / 2
        persistent_chart.right_axis = ft.ChartAxis(
            labels_size=40,
            labels=[
                ft.ChartAxisLabel(value=low, label=ft.Text(f"{low/1000:.1f}k", size=10, color=ft.Colors.GREY_500)),
                ft.ChartAxisLabel(value=mid_p, label=ft.Text(f"{mid_p/1000:.1f}k", size=10, color=ft.Colors.GREY_500)),
                ft.ChartAxisLabel(value=high, label=ft.Text(f"{high/1000:.1f}k", size=10, color=ft.Colors.GREY_500)),
            ]
        )

        # Bottom Axis (Time labels)
        timestamps = data.get("timestamps", [])
        if timestamps and len(timestamps) >= 2:
            start_ts = timestamps[0]
            mid_ts = timestamps[len(timestamps) // 2]
            end_ts = timestamps[-1]

            def fmt_ts(ts):
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                if selected_period["value"] in ["1H", "1D"]:
                    return dt.strftime("%H:%M")
                elif selected_period["value"] in ["1W", "1M"]:
                    return dt.strftime("%d %b")
                else:
                    return dt.strftime("%b '%y")

            labels = []
            num_labels = 5
            for i in range(num_labels):
                idx = i * (len(timestamps) - 1) // (num_labels - 1)
                x_val = (idx / (len(timestamps) - 1)) * 100
                ts = timestamps[idx]
                labels.append(
                    ft.ChartAxisLabel(
                        value=x_val,
                        label=ft.Text(fmt_ts(ts), size=10, color=ft.Colors.GREY_500)
                    )
                )

            persistent_chart.bottom_axis = ft.ChartAxis(
                labels_size=20,
                labels=labels
            )

            # Ensure left axis takes no space
            persistent_chart.left_axis = ft.ChartAxis(labels_size=0)

        # Add horizontal grid lines
        persistent_chart.horizontal_grid_lines = ft.ChartGridLines(
            interval=(high - low) / 4 if high > low else 1,
            color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            width=1,
        )

        if is_first_load:
            chart_data_series.data_points = points
            chart_container.content = persistent_chart
            if chart_container.page:
                chart_container.update()
        else:
            chart_data_series.data_points = points
            if persistent_chart.page:
                persistent_chart.update()

        current_price_label.opacity = 1
        change_label.opacity = 1
        if current_price_label.page:
            current_price_label.update()
            change_label.update()

        # Fear & Greed
        fng = data.get("fng")
        if fng:
            try:
                val = int(fng["value"])
                fng_value.value = str(val)
                fng_label.value = fng["value_classification"]
                fng_color = (
                    ft.Colors.GREEN_ACCENT
                    if val > 50
                    else (ft.Colors.ORANGE_ACCENT if val > 30 else ft.Colors.RED_ACCENT)
                )
                fng_value.color = fng_color
                fng_ring.color = fng_color
                fng_ring.value = val / 100.0
            except (KeyError, TypeError, ValueError):
                fng_label.value = "Unavailable"
        else:
            fng_label.value = "Unavailable"

        retry_container.visible = False

    def update_data(period):
        nonlocal loading
        if loading:
            return
        loading = True
        selected_period["value"] = period

        is_first_load = chart_container.content != persistent_chart
        if is_first_load:
            chart_container.content = ft.Container(
                alignment=ft.alignment.center,
                content=ft.ProgressRing(
                    width=36, height=36, color=ft.Colors.ORANGE_ACCENT
                ),
            )
            if chart_container.page:
                chart_container.update()
        else:
            current_time_label.value = "Updating..."
            current_time_label.color = ft.Colors.GREY_600
            if current_time_label.page:
                current_time_label.update()

        set_active_period(period)

        api_url = get_api_url()
        data = fetch_price_from_api(api_url, period)

        if data and data.get("prices"):
            try:
                _apply_market_data(data, is_first_load)
                save_market_cache(period, data)
            except Exception as ex:
                print(f"Chart render error: {ex}")
                current_time_label.value = f"Error: {ex}"
                current_time_label.color = ft.Colors.RED_ACCENT
        else:
            # Try local cache
            cached = load_cached_market(period)
            if cached and cached.get("prices"):
                try:
                    _apply_market_data(cached, is_first_load)
                    current_time_label.value = "Showing cached data · connection lost"
                    current_time_label.color = ft.Colors.ORANGE_ACCENT
                except Exception:
                    pass
            else:
                current_time_label.value = "Connection lost · tap Retry"
                current_time_label.color = ft.Colors.RED_ACCENT
                retry_container.visible = True

        loading = False
        page.update()

    def update_market_ui():
        update_data("1D")

    # Halving card — estimated from a reference block
    # Bitcoin block 840,000 mined ~April 2024; next halving at block 1,050,000
    # Average block time ≈ 10 minutes
    LAST_HALVING_BLOCK = 840_000
    NEXT_HALVING_BLOCK = 1_050_000
    BLOCKS_REMAINING_APPROX = NEXT_HALVING_BLOCK - LAST_HALVING_BLOCK
    # Rough estimate: 210,000 blocks × 10 min ≈ 1,458 days from April 2024
    estimated_halving = datetime(2028, 4, 17, tzinfo=timezone.utc)
    remaining_days = max(0, (estimated_halving - datetime.now(timezone.utc)).days)
    halving_text = f"~{remaining_days} Days" if remaining_days > 0 else "Imminent"

    fng_card = ft.Container(
        expand=True,
        padding=15,
        bgcolor="#0F172A",
        border_radius=15,
        animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_OUT),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
        ),
        content=ft.Row(
            [
                ft.Stack([fng_ring], alignment=ft.alignment.center),
                ft.Column(
                    [
                        ft.Text(
                            "Sentiment",
                            size=10,
                            color=ft.Colors.GREY_500,
                            weight="bold",
                        ),
                        ft.Row([fng_value, fng_label], spacing=6),
                    ],
                    spacing=0,
                ),
            ]
        ),
    )

    halving_card = ft.Container(
        expand=True,
        padding=15,
        bgcolor="#0F172A",
        border_radius=15,
        animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_OUT),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
        ),
        content=ft.Row(
            [
                ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.BLUE_400, size=30),
                ft.Column(
                    [
                        ft.Text(
                            "Next Halving",
                            size=10,
                            color=ft.Colors.GREY_500,
                            weight="bold",
                        ),
                        ft.Text(
                            halving_text,
                            size=16,
                            weight="bold",
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            "Estimated",
                            size=9,
                            color=ft.Colors.GREY_600,
                            italic=True,
                        ),
                    ],
                    spacing=0,
                ),
            ]
        ),
    )

    main_view = ft.Column(
        expand=True,
        controls=[
            # Widgets Row (F&G + Halving)
            ft.Container(
                padding=ft.padding.only(left=20, right=20, top=20, bottom=10),
                content=ft.Row(spacing=15, controls=[fng_card, halving_card]),
            ),
            # Chart and Price Card
            ft.Container(
                padding=ft.padding.symmetric(horizontal=10),
                expand=True,
                content=ft.Column(
                    [
                        ft.Text("BTC / USD", size=13, color=ft.Colors.GREY_500),
                        ft.Row(
                            [current_price_label, change_label],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        current_time_label,
                        ft.Row([high_label, low_label], spacing=15),
                        chart_container,
                        ft.Row(
                            [
                                make_period_button("1H"),
                                make_period_button("1D"),
                                make_period_button("1W"),
                                make_period_button("1M"),
                                make_period_button("1Y"),
                                make_period_button("5Y"),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        retry_container,
                    ],
                    spacing=8,
                ),
            ),
        ],
    )

    view_container.controls.append(main_view)
    return view_container, update_market_ui
