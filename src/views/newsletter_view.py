"""Reader for the Bitcoin Optech weekly newsletter, shown in full under its MIT license."""

import threading

import flet as ft

import services.news_service as news_service
from services.ai_service import get_api_url
from views.chat_panel import chat_panel, markdown_style

OPTECH_LICENSE_URL = "https://bitcoinops.org/en/about/"
CREDIT = "© Bitcoin Optech. Republished in full under the MIT license."


def newsletter_view_component(item: dict, on_back_click, page: ft.Page):
    url = item.get("url", "")
    api_url = get_api_url()
    news_service.mark_newsletter_read(int(item.get("number") or 0))

    body = ft.Markdown(
        item.get("intro", ""),
        selectable=True,
        shrink_wrap=True,
        soft_line_break=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
        md_style_sheet=markdown_style(),
        on_tap_link=lambda e: page.launch_url(e.data),
    )
    loading_row = ft.Row(
        [
            ft.ProgressRing(width=16, height=16, color=ft.Colors.ORANGE_ACCENT),
            ft.Text("Loading the newsletter…", size=13, color=ft.Colors.GREY_500),
        ],
        visible=bool(api_url),
    )

    def load_body():
        markdown = news_service.fetch_newsletter_markdown(api_url, url)
        if markdown:
            body.value = markdown
        loading_row.visible = False
        if not markdown:
            loading_row.controls = [
                ft.Text("Could not load the full newsletter.", size=13, color=ft.Colors.GREY_500)
            ]
            loading_row.visible = True
        if body.page:
            page.update()

    if api_url:
        threading.Thread(target=load_body, daemon=True).start()

    summary_text = ft.Markdown(
        "",
        selectable=True,
        shrink_wrap=True,
        soft_line_break=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
        md_style_sheet=markdown_style(),
    )
    summary_card = ft.Container(
        visible=False,
        padding=14,
        bgcolor="#0F172A",
        border_radius=14,
        margin=ft.margin.only(bottom=12),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.BLUE_400, size=16),
                        ft.Text("In plain words (AI)", size=12, weight="bold", color=ft.Colors.BLUE_300),
                    ],
                ),
                summary_text,
                ft.Text(
                    "Written by AI from the newsletter; it can contain mistakes.",
                    size=11,
                    italic=True,
                    color=ft.Colors.GREY_600,
                ),
            ],
        ),
    )

    def explain(_):
        explain_button.disabled = True
        explain_button.text = "Explaining…"
        page.update()

        def work():
            summary, error = news_service.fetch_article_summary(api_url, url, style="simple")
            summary_text.value = summary or f"*{error}*"
            summary_card.visible = True
            explain_button.text = "Explain simply"
            explain_button.disabled = False
            if explain_button.page:
                page.update()

        threading.Thread(target=work, daemon=True).start()

    explain_button = ft.FilledButton(
        "Explain simply",
        icon=ft.Icons.AUTO_AWESOME,
        disabled=not api_url,
        on_click=explain,
    )

    chat_section = ft.Container(visible=False, margin=ft.margin.only(bottom=12))

    def toggle_chat(_):
        if chat_section.content is None:
            chat_section.content = chat_panel(
                page,
                article_url=url,
                hint="e.g. what does this mean for my wallet?",
                chat_height=320,
            )
        chat_section.visible = not chat_section.visible
        ask_button.text = "Hide questions" if chat_section.visible else "Ask about it"
        page.update()

    ask_button = ft.OutlinedButton(
        "Ask about it",
        icon=ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
        disabled=not api_url,
        on_click=toggle_chat,
    )

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
                ft.Text("Bitcoin Optech", size=13, color=ft.Colors.GREY_400),
            ],
            spacing=0,
        ),
    )

    content = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Text("WEEKLY NEWSLETTER", size=11, weight="bold", color=ft.Colors.ORANGE_ACCENT),
                        ft.Text(item.get("title", "Bitcoin Optech Newsletter"), size=20, weight="bold"),
                        ft.Text(item.get("published_at", ""), size=12, color=ft.Colors.GREY_500),
                        ft.Text(
                            "A weekly technical digest of Bitcoin development. Tap Explain simply "
                            "for a plain-language version.",
                            size=12,
                            color=ft.Colors.GREY_500,
                        ),
                        ft.Divider(height=20, color="#222222"),
                        ft.Row([explain_button, ask_button], wrap=True, spacing=8),
                        ft.Container(height=8),
                        summary_card,
                        chat_section,
                        loading_row,
                        body,
                        ft.Divider(height=30, color="#222222"),
                        ft.Text(CREDIT, size=12, color=ft.Colors.GREY_500),
                        ft.Row(
                            [
                                ft.TextButton(
                                    "Open on bitcoinops.org",
                                    icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                                    on_click=lambda _: page.launch_url(url),
                                ),
                                ft.TextButton(
                                    "License",
                                    on_click=lambda _: page.launch_url(OPTECH_LICENSE_URL),
                                ),
                            ],
                            wrap=True,
                        ),
                        ft.Container(height=30),
                    ]
                ),
            )
        ],
    )

    return ft.Column(
        expand=True,
        spacing=0,
        controls=[back_bar, ft.Container(height=1, bgcolor="#222222"), content],
    )
