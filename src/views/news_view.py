import threading

import flet as ft

import services.news_service as news_service
from services.ai_service import get_api_url
from services.i18n import t

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


REGULATORS = {"SEC", "CFTC"}

# Newsletter edge tab: wide while there is an unread issue, a slim handle once read.
TAB_COLLAPSED_WIDTH = 36
TAB_EXPANDED_WIDTH = 210
TAB_AUTO_COLLAPSE_SECONDS = 5


def matches_filter(item: dict, label: str) -> bool:
    if label == ALL_NEWS:
        return True
    if label == "Policy" and item.get("publisher") in REGULATORS:
        return True
    exact, partial, title_words = FILTERS[label]
    cats = [c.lower() for c in item.get("categories", [])]
    title = f" {item.get('title', '').lower()} "
    return (
        any(c in exact for c in cats)
        or any(p in c for c in cats for p in partial)
        or any(w in title for w in title_words)
    )


def news_view_component(page: ft.Page, on_news_click, on_newsletter_click=None):
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
    status_text = ft.Text(t("Loading latest news…"), size=11, color=ft.Colors.GREY_500)

    retry_button = ft.Container(
        content=ft.OutlinedButton(
            t("Retry"),
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
                                t("No recent news found in this category."),
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
                            # The placeholder sits behind the picture, so a thumbnail that never
                            # paints (some large publisher PNGs) still shows a tile, not a gap.
                            ft.Container(
                                width=80,
                                height=80,
                                bgcolor="#1E293B",
                                border_radius=12,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                content=ft.Stack(
                                    [
                                        ft.Container(
                                            width=80,
                                            height=80,
                                            alignment=ft.alignment.center,
                                            content=ft.Icon(ft.Icons.IMAGE_OUTLINED, color=ft.Colors.GREY_700, size=28),
                                        ),
                                        ft.Image(
                                            src=img_url,
                                            width=80,
                                            height=80,
                                            fit="cover",
                                            border_radius=12,
                                            error_content=ft.Container(),
                                        ),
                                    ]
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
                                        f"{news_service.byline(item)} · {news_service.display_time(item)}",
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
                            t("You've reached the end of the latest news."),
                            size=12,
                            color=ft.Colors.GREY_600,
                            italic=True,
                        ),
                        ft.Text(
                            t("Total {count} articles scanned.", count=len(data)),
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
        # The chip's data is the English filter key; its label is in the interface language.
        selected_filter["value"] = e.control.data
        for chip in filter_row.controls:
            chip.selected = chip.data == selected_filter["value"]
        render_current()

    filter_row.controls = [
        ft.Chip(label=ft.Text(t(label)), data=label, selected=label == ALL_NEWS, on_select=handle_filter)
        for label in (ALL_NEWS, *FILTERS)
    ]

    # ---- Bitcoin Optech edge tab ----
    newsletter = {"item": None, "expanded": False, "timer": None}
    tab_label = ft.Text("", size=12, weight="bold", color=ft.Colors.WHITE, no_wrap=True)
    tab_icon = ft.Icon(ft.Icons.MARK_EMAIL_UNREAD_OUTLINED, color=ft.Colors.WHITE, size=18)
    edge_tab = ft.Container(
        visible=False,
        right=0,
        top=110,
        width=TAB_COLLAPSED_WIDTH,
        height=44,
        padding=ft.padding.only(left=9, right=10),
        alignment=ft.alignment.center_left,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        border_radius=ft.border_radius.only(top_left=22, bottom_left=22),
        animate=ft.Animation(280, ft.AnimationCurve.EASE_OUT_CUBIC),
        shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.45, ft.Colors.BLACK)),
        content=ft.Row([tab_icon, tab_label], spacing=8, tight=True),
        tooltip=t("Bitcoin Optech weekly newsletter"),
    )

    def is_unread(item) -> bool:
        return int(item.get("number") or 0) > news_service.last_read_newsletter()

    def style_tab(expanded: bool):
        item = newsletter["item"]
        unread = is_unread(item)
        newsletter["expanded"] = expanded
        edge_tab.width = TAB_EXPANDED_WIDTH if expanded else TAB_COLLAPSED_WIDTH
        edge_tab.bgcolor = ft.Colors.ORANGE_700 if unread else "#334155"
        tab_icon.name = ft.Icons.MARK_EMAIL_UNREAD_OUTLINED if unread else ft.Icons.MAIL_OUTLINE_ROUNDED
        number = item.get("number", "")
        tab_label.value = t("New newsletter #{number}", number=number) if unread else t("Optech newsletter #{number}", number=number)
        if edge_tab.page:
            edge_tab.update()

    def collapse_later():
        if newsletter["timer"]:
            newsletter["timer"].cancel()
        timer = threading.Timer(TAB_AUTO_COLLAPSE_SECONDS, lambda: style_tab(False))
        timer.daemon = True
        newsletter["timer"] = timer
        timer.start()

    def handle_tab_click(_):
        item = newsletter["item"]
        if not item:
            return
        if not newsletter["expanded"]:
            style_tab(True)
            collapse_later()
            return
        if newsletter["timer"]:
            newsletter["timer"].cancel()
        news_service.mark_newsletter_read(int(item.get("number") or 0))
        if on_newsletter_click:
            on_newsletter_click(item)
        style_tab(False)  # opening marks it read, so it shrinks to the handle

    edge_tab.on_click = handle_tab_click

    def show_newsletter(items: list[dict]):
        if not items:
            return
        newsletter["item"] = items[0]
        edge_tab.visible = True
        style_tab(is_unread(items[0]))

    def update_newsletter():
        show_newsletter(news_service.fetch_newsletters(get_api_url()))

    show_newsletter(news_service.load_cached_newsletters())

    def update_news():
        if not refresh_lock.acquire(blocking=False):
            return
        try:
            status_text.value = t("Refreshing news…")
            retry_button.visible = False
            if status_text.page:
                page.update()

            fresh_news = news_service.fetch_news_from_api(get_api_url())
            if fresh_news:
                news_service.all_news_cache = fresh_news
                news_service.save_news_cache(fresh_news)
                status_text.value = t("Updated just now · {count} articles", count=len(fresh_news))
            elif news_service.all_news_cache:
                status_text.value = t("Could not refresh · showing saved news")
            else:
                status_text.value = t("No connection · tap Retry")
                retry_button.visible = True
            render_current()
        finally:
            refresh_lock.release()

    def refresh_in_background():
        threading.Thread(target=update_news, daemon=True).start()

    threading.Thread(target=update_newsletter, daemon=True).start()

    view_container.controls = [
        filter_row,
        ft.Container(
            content=ft.Row([status_text, ft.Container(expand=True), retry_button]),
            padding=ft.padding.only(left=12, top=6, bottom=2, right=12),
        ),
        ft.Stack([news_container, scroll_top_overlay, edge_tab], expand=True),
    ]

    if news_service.all_news_cache:
        status_text.value = t("Showing saved news · refreshing…")
        render_current()

    return view_container, update_news
