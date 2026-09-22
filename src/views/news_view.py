import threading

import flet as ft

import services.news_service as news_service
from services.ai_service import get_api_url

ALL_NEWS = "All News"

# label -> (category names, category substrings, title substrings)
FILTERS = {
    "Markets": (
        {"markets", "crypto markets today", "prices", "coindesk 20", "coindesk indices"},
        (),
        ("market", "price"),
    ),
    "Bitcoin": (set(), ("bitcoin",), ("bitcoin", " btc ")),
    "Trading": ({"crypto trading", "options", "deribit"}, (), ("trading", "trade", "futures")),
    "Policy": (
        {"policy", "regulation", "tax", "federal reserve"},
        (),
        ("regulation", "policy", "sec ", "fed ", "bill"),
    ),
    "DeFi": ({"defi", "stablecoins", "tokenization"}, (), ("defi", "stablecoin", "token")),
    "ETFs": (set(), ("etf",), ("etf", "spot bitcoin")),
}


def matches_filter(item: dict, label: str) -> bool:
    if label == ALL_NEWS:
        return True
    exact, partial, title_words = FILTERS[label]
    cats = [c.lower() for c in item.get("categories", [])]
    title = f" {item.get('title', '').lower()} "
    return (
        any(c in exact for c in cats)
        or any(p in c for c in cats for p in partial)
        or any(w in title for w in title_words)
    )


def news_view_component(page: ft.Page, on_news_click):
    view_container = ft.Column(expand=True)
    selected_filter = {"value": ALL_NEWS}
    refresh_lock = threading.Lock()

    cached = news_service.load_cached_news()
    if cached:
        news_service.all_news_cache = cached

    def scroll_to_top(e):
        news_list.scroll_to(offset=0, duration=500)

    scroll_top_button = ft.Container(
        content=ft.Icon(ft.Icons.ARROW_UPWARD_ROUNDED, color=ft.Colors.WHITE, size=24),
        bgcolor=ft.Colors.BLUE_500,
        padding=8,
        border_radius=25,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.4, ft.Colors.BLUE_500),
        ),
        on_click=scroll_to_top,
        visible=False,
    )
    scroll_top_row = ft.Row([scroll_top_button], alignment=ft.MainAxisAlignment.CENTER)
    scroll_top_overlay = ft.Container(content=scroll_top_row, top=15, left=0, right=0)

    def handle_scroll(e: ft.OnScrollEvent):
        show = float(e.pixels or 0) > 300
        if show != scroll_top_button.visible:
            scroll_top_button.visible = show
            scroll_top_button.update()

    news_list = ft.ListView(
        expand=True, spacing=10, on_scroll=handle_scroll
    )
    news_container = ft.Container(content=news_list, padding=10, expand=True)
    filter_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=5)
    status_text = ft.Text("Loading latest news…", size=11, color=ft.Colors.GREY_500)

    retry_button = ft.Container(
        content=ft.OutlinedButton(
            "Retry",
            icon=ft.Icons.REFRESH_ROUNDED,
            on_click=lambda _: refresh_in_background(),
        ),
        alignment=ft.alignment.center,
        visible=False,
    )

    def render_news(data):
        news_list.controls.clear()

        if not data:
            news_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.CLOUD_OFF_ROUNDED,
                                color=ft.Colors.GREY_600,
                                size=40,
                            ),
                            ft.Text(
                                "No recent news found in this category.",
                                color=ft.Colors.GREY_400,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )
            page.update()
            return

        for item in data:
            img_url = news_service.get_image_url(item)
            card = ft.Card(
                color=ft.Colors.TRANSPARENT,
                elevation=0,
                content=ft.Container(
                    padding=12,
                    bgcolor="#0F172A",
                    border_radius=16,
                    ink=True,
                    opacity=0,
                    offset=ft.Offset(0, 0.06),
                    animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
                    animate_offset=ft.Animation(400, ft.AnimationCurve.EASE_OUT_CUBIC),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=12,
                        color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                    ),
                    on_click=lambda _, i=item: on_news_click(i),
                    content=ft.Row(
                        [
                            ft.Image(
                                src=img_url,
                                width=80,
                                height=80,
                                fit="cover",
                                border_radius=12,
                                error_content=ft.Container(
                                    width=80,
                                    height=80,
                                    bgcolor="#1E293B",
                                    border_radius=12,
                                    content=ft.Icon(
                                        ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                                        color=ft.Colors.GREY_700,
                                        size=28,
                                    ),
                                    alignment=ft.alignment.center,
                                ),
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        item["title"],
                                        size=14,
                                        weight="bold",
                                        max_lines=2,
                                    ),
                                    ft.Text(
                                        f"{item.get('publisher', 'CoinDesk')} · {news_service.published_label(item)}",
                                        size=11,
                                        color=ft.Colors.GREY_500,
                                    ),
                                ],
                                expand=True,
                            ),
                        ]
                    ),
                ),
            )
            news_list.controls.append(card)

        news_list.controls.append(
            ft.Container(
                padding=ft.padding.only(top=20, bottom=40),
                alignment=ft.alignment.center,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                            color=ft.Colors.GREY_600,
                            size=20,
                        ),
                        ft.Text(
                            "You've reached the end of the latest news.",
                            size=12,
                            color=ft.Colors.GREY_600,
                            italic=True,
                        ),
                        ft.Text(
                            f"Total {len(data)} articles scanned.",
                            size=10,
                            color=ft.Colors.GREY_700,
                        ),
                    ],
                ),
            )
        )

        # Render all cards invisible, then animate them in
        page.update()
        for ctrl in news_list.controls[:-1]:
            ctrl.content.opacity = 1
            ctrl.content.offset = ft.Offset(0, 0)
        page.update()

    def render_current():
        label = selected_filter["value"]
        render_news([item for item in news_service.all_news_cache if matches_filter(item, label)])

    def handle_filter(e):
        selected_filter["value"] = e.control.label.value
        for chip in filter_row.controls:
            chip.selected = chip.label.value == selected_filter["value"]
        render_current()

    filter_row.controls = [
        ft.Chip(label=ft.Text(label), selected=label == ALL_NEWS, on_select=handle_filter)
        for label in (ALL_NEWS, *FILTERS)
    ]

    def update_news():
        if not refresh_lock.acquire(blocking=False):
            return
        try:
            status_text.value = "Refreshing news…"
            retry_button.visible = False
            if status_text.page:
                page.update()

            fresh_news = news_service.fetch_news_from_api(get_api_url())
            if fresh_news:
                news_service.all_news_cache = fresh_news
                news_service.save_news_cache(fresh_news)
                status_text.value = f"Updated just now · {len(fresh_news)} articles"
            elif news_service.all_news_cache:
                status_text.value = "Could not refresh · showing saved news"
            else:
                status_text.value = "No connection · tap Retry"
                retry_button.visible = True
            render_current()
        finally:
            refresh_lock.release()

    def refresh_in_background():
        threading.Thread(target=update_news, daemon=True).start()

    view_container.controls = [
        filter_row,
        ft.Container(
            content=ft.Row([status_text, ft.Container(expand=True), retry_button]),
            padding=ft.padding.only(left=12, top=6, bottom=2, right=12),
        ),
        ft.Stack([news_container, scroll_top_overlay], expand=True),
    ]

    if news_service.all_news_cache:
        status_text.value = "Showing saved news · refreshing…"
        render_current()

    return view_container, update_news
