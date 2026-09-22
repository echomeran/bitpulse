import threading

import flet as ft

import services.news_service as news_service
from services import sources
from services.ai_service import get_api_url


def news_detail_view_component(item, on_back_click, page):
    img_url = news_service.get_image_url(item)
    summary = item.get("description") or "No article summary is available."
    article_url = item.get("link", "")
    can_open = article_url.startswith(("https://", "http://"))

    def open_original_article(e):
        if can_open:
            page.launch_url(article_url)

    content_text = ft.Text(
        summary,
        size=15,
        selectable=True,
        style=ft.TextStyle(height=1.65),
        color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
    )

    loading_indicator = ft.ProgressRing(width=16, height=16, color=ft.Colors.BLUE_400)
    loading_text = ft.Text("Loading full article...", color=ft.Colors.GREY_500, size=13)
    loading_row = ft.Row([loading_indicator, loading_text], visible=False)

    def fetch_full(api_url):
        full_text = news_service.fetch_full_article(api_url, article_url)
        if full_text and len(full_text) > len(summary):
            content_text.value = full_text
        loading_row.visible = False
        if content_text.page:
            content_text.update()
            loading_row.update()

    api_url = get_api_url()
    if api_url and sources.is_allowed_article_url(article_url):
        loading_row.visible = True
        threading.Thread(target=fetch_full, args=(api_url,), daemon=True).start()

    back_bar = ft.Container(
        bgcolor="#121212",
        padding=ft.padding.symmetric(horizontal=4, vertical=4),
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                    icon_color=ft.Colors.WHITE,
                    on_click=on_back_click,
                    icon_size=20,
                    tooltip="Back to news",
                ),
                ft.Text(
                    item.get("publisher", "CoinDesk"),
                    size=13,
                    color=ft.Colors.GREY_400,
                ),
            ],
            spacing=0,
        ),
    )

    scroll_content = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Image(
                src=img_url,
                fit="fitWidth",
                border_radius=10,
                error_content=ft.Container(
                    height=180,
                    bgcolor="#0F172A",
                    border_radius=10,
                    content=ft.Icon(
                        ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                        color=ft.Colors.GREY_700,
                        size=40,
                    ),
                    alignment=ft.alignment.center,
                ),
            ),
            ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Text(item.get("title", "Crypto News"), size=20, weight="bold"),
                        ft.Text(
                            news_service.published_label(item),
                            size=12,
                            color=ft.Colors.GREY_500,
                        ),
                        ft.Divider(height=20, color="#222222"),
                        loading_row,
                        content_text,
                        ft.Divider(height=30, color="#222222"),
                        ft.Text("Source: " + item.get("publisher", "CoinDesk"), color=ft.Colors.GREY_500, size=12),
                        ft.OutlinedButton(
                            "Open original article",
                            icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                            on_click=open_original_article,
                            disabled=not can_open,
                        ),
                        ft.Container(height=30),
                    ]
                ),
            ),
        ],
    )

    return ft.Column(
        expand=True,
        spacing=0,
        controls=[
            back_bar,
            ft.Container(height=1, bgcolor="#222222"),
            scroll_content,
        ],
    )
