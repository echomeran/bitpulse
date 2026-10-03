import threading

import flet as ft

import services.news_service as news_service
from services import sources
from services.ai_service import get_api_url
from views.chat_panel import chat_panel


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
    can_summarize = bool(api_url) and sources.is_allowed_article_url(article_url)
    if can_summarize:
        loading_row.visible = True
        threading.Thread(target=fetch_full, args=(api_url,), daemon=True).start()

    summary_text = ft.Text("", size=14, selectable=True, color=ft.Colors.WHITE, style=ft.TextStyle(height=1.5))
    summary_card = ft.Container(
        visible=False,
        padding=14,
        bgcolor="#0F172A",
        border_radius=14,
        margin=ft.margin.only(bottom=16),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.BLUE_400, size=16),
                        ft.Text("AI summary", size=12, weight="bold", color=ft.Colors.BLUE_300),
                    ],
                ),
                summary_text,
            ],
        ),
    )

    chat_section = ft.Container(visible=False, margin=ft.margin.only(top=8))

    def toggle_chat(e):
        if chat_section.content is None:
            chat_section.content = ft.Column(
                spacing=0,
                controls=[
                    ft.Divider(height=20, color="#222222"),
                    ft.Text(
                        "Ask about this article",
                        size=12,
                        weight="bold",
                        color=ft.Colors.BLUE_300,
                    ),
                    chat_panel(
                        page,
                        article_url=article_url,
                        hint="e.g. why does this matter?",
                        chat_height=320,
                    ),
                ],
            )
        chat_section.visible = not chat_section.visible
        ask_button.text = "Hide questions" if chat_section.visible else "Ask about this article"
        page.update()

    summarize_button = ft.OutlinedButton(
        "Summarize with AI",
        icon=ft.Icons.AUTO_AWESOME,
        disabled=not can_summarize,
        on_click=lambda e: start_summary(),
    )

    ask_button = ft.OutlinedButton(
        "Ask about this article",
        icon=ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
        disabled=not can_summarize,
        on_click=toggle_chat,
    )

    summarizing = {"value": False}

    def start_summary():
        if summarizing["value"]:
            return
        summarizing["value"] = True
        summarize_button.text = "Summarizing…"
        summarize_button.disabled = True
        if summarize_button.page:
            summarize_button.update()
        threading.Thread(target=fetch_summary, daemon=True).start()

    def fetch_summary():
        summary, error = news_service.fetch_article_summary(api_url, article_url)
        summary_text.value = summary or error
        summary_text.color = ft.Colors.WHITE if summary else ft.Colors.RED_ACCENT
        summary_card.visible = True
        summarize_button.text = "Summarize with AI"
        summarize_button.disabled = False
        summarizing["value"] = False
        if summarize_button.page:
            page.update()

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
                    item.get("publisher") or "CoinDesk",
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
                        ft.Row([summarize_button, ask_button], wrap=True, spacing=8),
                        ft.Container(height=12),
                        summary_card,
                        chat_section,
                        loading_row,
                        content_text,
                        ft.Divider(height=30, color="#222222"),
                        ft.Text("Source: " + news_service.byline(item), color=ft.Colors.GREY_500, size=12),
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
