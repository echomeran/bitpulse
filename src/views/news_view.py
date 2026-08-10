import flet as ft

from services.ai_service import get_api_url
from services.news_service import (
    all_news_cache as _news_cache_ref,
    fetch_news_from_api,
    get_image_url,
    load_cached_news,
    save_news_cache,
)
import services.news_service as news_service


def news_view_component(page: ft.Page, on_news_click):
    view_container = ft.Column(expand=True)

    # Load cache at startup
    cached = load_cached_news()
    if cached:
        news_service.all_news_cache = cached

    def scroll_to_top(e):
        news_list.scroll_to(offset=0, duration=500)

    twitter_logo = ft.Container(
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
    logo_wrapper = ft.Row([twitter_logo], alignment=ft.MainAxisAlignment.CENTER)
    logo_stack_item = ft.Container(content=logo_wrapper, top=15, left=0, right=0)

    def handle_scroll(e: ft.OnScrollEvent):
        try:
            if float(e.pixels) > 300 and not twitter_logo.visible:
                twitter_logo.visible = True
                twitter_logo.update()
            elif float(e.pixels) < 300 and twitter_logo.visible:
                twitter_logo.visible = False
                twitter_logo.update()
        except Exception:
            pass

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
            on_click=lambda _: update_news(),
        ),
        alignment=ft.alignment.center,
        visible=False,
    )

    def render_news(data):
        news_list.controls.clear()
        retry_button.visible = False

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
            img_url = get_image_url(item)
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
                                        f"{item.get('publisher', 'CoinDesk')} · {item.get('published_at', 'Latest')}",
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
        for ctrl in news_list.controls[:-1]:  # skip footer
            try:
                ctrl.content.opacity = 1
                ctrl.content.offset = ft.Offset(0, 0)
            except Exception:
                pass
        page.update()

    def handle_filter(e):
        selected_label = e.control.label.value
        for chip in filter_row.controls:
            chip.selected = chip.label.value == selected_label

        if selected_label == "All News":
            render_news(news_service.all_news_cache)
            return

        filtered = []
        for item in news_service.all_news_cache:
            item_cats = [c.lower() for c in item.get("categories", [])]
            title = item.get("title", "").lower()

            match = False
            if selected_label == "Markets":
                match = any(
                    c
                    in [
                        "markets",
                        "crypto markets today",
                        "prices",
                        "coindesk 20",
                        "coindesk indices",
                    ]
                    for c in item_cats
                ) or "market" in title or "price" in title
            elif selected_label == "Bitcoin":
                match = (
                    any("bitcoin" in c for c in item_cats)
                    or "bitcoin" in title
                    or " btc " in title
                )
            elif selected_label == "Trading":
                match = any(
                    c in ["crypto trading", "options", "deribit"] for c in item_cats
                ) or "trading" in title or "trade" in title or "futures" in title
            elif selected_label == "Policy":
                match = any(
                    c in ["policy", "regulation", "tax", "federal reserve"]
                    for c in item_cats
                ) or "regulation" in title or "policy" in title or "sec " in title or "fed " in title or "bill" in title
            elif selected_label == "DeFi":
                match = any(
                    c in ["defi", "stablecoins", "tokenization"] for c in item_cats
                ) or "defi" in title or "stablecoin" in title or "token" in title
            elif selected_label == "ETFs":
                match = (
                    any("etf" in c for c in item_cats)
                    or "etf" in title
                    or "spot bitcoin" in title
                )

            if match:
                filtered.append(item)

        render_news(filtered)

    filter_row.controls = [
        ft.Chip(label=ft.Text("All News"), selected=True, on_select=handle_filter),
        ft.Chip(label=ft.Text("Markets"), on_select=handle_filter),
        ft.Chip(label=ft.Text("Bitcoin"), on_select=handle_filter),
        ft.Chip(label=ft.Text("Trading"), on_select=handle_filter),
        ft.Chip(label=ft.Text("Policy"), on_select=handle_filter),
        ft.Chip(label=ft.Text("DeFi"), on_select=handle_filter),
        ft.Chip(label=ft.Text("ETFs"), on_select=handle_filter),
    ]

    def back_to_list():
        view_container.controls.clear()
        view_container.controls.append(filter_row)
        view_container.controls.append(
            ft.Container(
                content=ft.Row([status_text, ft.Container(expand=True), retry_button]),
                padding=ft.padding.only(left=12, top=6, bottom=2, right=12),
            )
        )
        view_container.controls.append(
            ft.Stack([news_container, logo_stack_item], expand=True)
        )
        if view_container.page:
            page.update()

    def update_news():
        status_text.value = "Refreshing news…"
        retry_button.visible = False
        if status_text.page:
            status_text.update()

        api_url = get_api_url()
        fresh_news = fetch_news_from_api(api_url)
        if fresh_news:
            news_service.all_news_cache = fresh_news
            save_news_cache(news_service.all_news_cache)
            status_text.value = f"Updated just now · {len(news_service.all_news_cache)} articles"
            render_news(news_service.all_news_cache)
        elif news_service.all_news_cache:
            status_text.value = "Could not refresh · showing saved news"
        else:
            cached = load_cached_news()
            news_service.all_news_cache = cached
            if cached:
                status_text.value = "Showing cached news · tap refresh to retry"
                render_news(news_service.all_news_cache)
            else:
                status_text.value = "No connection · tap Retry"
                retry_button.visible = True
                render_news([])
        back_to_list()

    if news_service.all_news_cache:
        status_text.value = "Showing saved news · refreshing…"
        render_news(news_service.all_news_cache)
    back_to_list()

    return view_container, update_news
