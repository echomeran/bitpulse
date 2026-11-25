"""Reader for the Bitcoin Optech weekly newsletter.

Optech publishes plain text under the MIT license, which allows rearranging it. A wall of text
loses most readers, so the issue is shown as a header with its numbers, a plain-language digest
on top, and one collapsible card per item, with an icon for what the item is about.
"""

import threading

import flet as ft

import services.news_service as news_service
from services.ai_service import get_api_url
from views.chat_panel import chat_panel, markdown_style

OPTECH_LICENSE_URL = "https://bitcoinops.org/en/about/"
CREDIT = "© Bitcoin Optech. Republished under the MIT license; the cards rearrange the original text."

# Section heading keyword -> (icon, accent colour, short label for the header chips)
SECTION_STYLES = (
    ("news", ft.Icons.NEWSPAPER, ft.Colors.ORANGE_400, "news"),
    ("services", ft.Icons.APPS, ft.Colors.TEAL_300, "app updates"),
    ("release", ft.Icons.ROCKET_LAUNCH, ft.Colors.PURPLE_200, "releases"),
    ("code", ft.Icons.CODE, ft.Colors.BLUE_300, "code changes"),
)
DEFAULT_SECTION_STYLE = (ft.Icons.ARTICLE_OUTLINED, ft.Colors.GREY_400, "items")

# Item keywords -> icon; the first match wins, otherwise the section's icon is used.
TOPIC_ICONS = (
    (("vulnerab", "security", "exploit", "denial-of-service", "dos ", "disclosure", "cve"), ft.Icons.SHIELD_OUTLINED),
    (("lightning", "htlc", "channel", "lnd", "eclair", "ldk", "core lightning", "bolt"), ft.Icons.BOLT),
    (("mining", "miner", " pool", "hashrate", "coinbase"), ft.Icons.CONSTRUCTION),
    (("privacy", "payjoin", "coinjoin", "tor ", "i2p", "silent payment"), ft.Icons.VISIBILITY_OFF_OUTLINED),
    (("wallet", "hardware", "coldcard", "signing", "backup", "psbt", "descriptor"), ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED),
    (("soft fork", "covenant", "consensus", "opcode", "bip"), ft.Icons.ACCOUNT_TREE_OUTLINED),
    (("fee", "mempool", "relay", "package"), ft.Icons.SPEED),
    (("testnet", "signet", "regtest"), ft.Icons.SCIENCE_OUTLINED),
)


def section_style(title: str):
    lowered = title.lower()
    for keyword, icon, color, label in SECTION_STYLES:
        if keyword in lowered:
            return icon, color, label
    return DEFAULT_SECTION_STYLE


def item_icon(item: dict, fallback):
    haystack = f" {item.get('title', '')} {item.get('preview', '')} {' '.join(item.get('topics', []))} ".lower()
    for keywords, icon in TOPIC_ICONS:
        if any(k in haystack for k in keywords):
            return icon
    return fallback


def _markdown(text: str, page: ft.Page) -> ft.Markdown:
    return ft.Markdown(
        text,
        selectable=True,
        shrink_wrap=True,
        soft_line_break=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
        md_style_sheet=markdown_style(),
        on_tap_link=lambda e: page.launch_url(e.data),
    )


def count_label(count: int, label: str) -> str:
    """'1 release', '2 releases', '1 code change'; 'news' has no singular form."""
    if count == 1 and label.endswith("s") and label != "news":
        label = label[:-1]
    return f"{count} {label}"


def header_card(item: dict, counts: dict, minutes) -> ft.Container:
    chips = []
    for title, count in counts.items():
        icon, color, label = section_style(title)
        chips.append(
            ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.BLACK),
                content=ft.Row(
                    [ft.Icon(icon, size=13, color=ft.Colors.WHITE), ft.Text(count_label(count, label), size=11, color=ft.Colors.WHITE)],
                    spacing=4,
                    tight=True,
                ),
            )
        )
    meta = item.get("published_at", "")
    if minutes:
        meta = f"{meta} · full text ~{minutes} min" if meta else f"Full text ~{minutes} min"
    return ft.Container(
        padding=18,
        border_radius=18,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#F7931A", "#C2410C", "#7C2D12"],
        ),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text("BITCOIN OPTECH · WEEKLY", size=11, weight="bold", color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE)),
                ft.Text(f"Newsletter #{item.get('number', '')}", size=26, weight="bold", color=ft.Colors.WHITE),
                ft.Text(meta, size=12, color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE)),
                ft.Row(chips, wrap=True, spacing=6, run_spacing=6) if chips else ft.Container(),
            ],
        ),
    )


def item_card(item: dict, icon, color, page: ft.Page) -> ft.Container:
    topics = item.get("topics") or []
    body_controls = [_markdown(item.get("markdown", ""), page)]
    if topics:
        body_controls.append(
            ft.Row(
                [
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        border_radius=10,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.4, color)),
                        content=ft.Text(t, size=10, color=color),
                    )
                    for t in topics[:5]
                ],
                wrap=True,
                spacing=4,
                run_spacing=4,
            )
        )
    return ft.Container(
        border_radius=14,
        bgcolor="#0F172A",
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.ExpansionTile(
            leading=ft.Container(
                width=36,
                height=36,
                border_radius=18,
                bgcolor=ft.Colors.with_opacity(0.15, color),
                alignment=ft.alignment.center,
                content=ft.Icon(icon, size=18, color=color),
            ),
            title=ft.Text(item.get("title", ""), size=14, weight="bold", max_lines=2),
            subtitle=ft.Text(item.get("preview", ""), size=12, color=ft.Colors.GREY_400, max_lines=2),
            controls=[ft.Column(body_controls, spacing=10)],
            controls_padding=ft.padding.only(left=16, right=16, bottom=14),
            tile_padding=ft.padding.symmetric(horizontal=12, vertical=4),
            maintain_state=True,
            icon_color=color,
            collapsed_icon_color=ft.Colors.GREY_500,
            shape=ft.RoundedRectangleBorder(radius=14),
            collapsed_shape=ft.RoundedRectangleBorder(radius=14),
        ),
    )


def section_block(section: dict, page: ft.Page) -> ft.Column:
    icon, color, _ = section_style(section.get("title", ""))
    items = section.get("items") or []
    return ft.Column(
        spacing=8,
        controls=[
            ft.Row(
                [
                    ft.Icon(icon, size=16, color=color),
                    ft.Text(section.get("title", "").upper(), size=12, weight="bold", color=color, expand=True),
                    ft.Text(str(len(items)), size=12, color=ft.Colors.GREY_600),
                ],
                spacing=6,
            ),
            *[item_card(i, item_icon(i, icon), color, page) for i in items],
        ],
    )


def digest_card() -> tuple[ft.Container, ft.Markdown, ft.Row]:
    text = ft.Markdown(
        "",
        selectable=True,
        shrink_wrap=True,
        soft_line_break=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
        md_style_sheet=markdown_style(),
    )
    loading = ft.Row(
        [
            ft.ProgressRing(width=14, height=14, color=ft.Colors.BLUE_400),
            ft.Text("Writing a plain-language digest…", size=12, color=ft.Colors.GREY_500),
        ],
        visible=False,
    )
    card = ft.Container(
        padding=16,
        border_radius=16,
        bgcolor="#0F172A",
        border=ft.border.all(1, ft.Colors.with_opacity(0.35, ft.Colors.BLUE_400)),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    [
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.BLUE_400, size=16),
                        ft.Text("This week in plain words", size=13, weight="bold", color=ft.Colors.BLUE_200),
                    ],
                    spacing=6,
                ),
                loading,
                text,
                ft.Text(
                    "Written by AI from the newsletter; it can contain mistakes. Tap a card below for the original.",
                    size=11,
                    italic=True,
                    color=ft.Colors.GREY_600,
                ),
            ],
        ),
    )
    return card, text, loading


def newsletter_view_component(item: dict, on_back_click, page: ft.Page):
    url = item.get("url", "")
    api_url = get_api_url()
    news_service.mark_newsletter_read(int(item.get("number") or 0))

    header_slot = ft.Container(content=header_card(item, item.get("counts") or {}, item.get("reading_minutes")))
    digest, digest_text, digest_loading = digest_card()
    digest.visible = bool(api_url)
    sections_column = ft.Column(spacing=20)
    status = ft.Row(
        [
            ft.ProgressRing(width=16, height=16, color=ft.Colors.ORANGE_ACCENT),
            ft.Text("Loading the newsletter…", size=13, color=ft.Colors.GREY_500),
        ],
        visible=bool(api_url),
    )

    def show_digest(summary, error):
        digest_text.value = summary or f"*{error}*"
        digest_loading.visible = False
        if digest.page:
            page.update()

    def load():
        data = news_service.fetch_newsletter(api_url, url)
        status.visible = False
        if not data:
            status.controls = [ft.Text("Could not load the newsletter. Check your connection.", size=13, color=ft.Colors.GREY_500)]
            status.visible = True
            digest.visible = False
            if status.page:
                page.update()
            return
        header_slot.content = header_card(item, data.get("counts") or {}, data.get("reading_minutes"))
        sections = data.get("sections") or []
        if sections:
            sections_column.controls = [section_block(s, page) for s in sections]
        else:
            sections_column.controls = [_markdown(data.get("markdown", ""), page)]
        if data.get("digest"):
            show_digest(data["digest"], None)
        else:
            digest_loading.visible = True
            if digest.page:
                page.update()
            show_digest(*news_service.fetch_article_summary(api_url, url, style="simple"))
        if sections_column.page:
            page.update()

    if api_url:
        threading.Thread(target=load, daemon=True).start()
    else:
        sections_column.controls = [_markdown(item.get("intro", ""), page)]

    chat_section = ft.Container(visible=False)

    def toggle_chat(_):
        if chat_section.content is None:
            chat_section.content = chat_panel(
                page,
                article_url=url,
                hint="e.g. what does this mean for my wallet?",
                chat_height=320,
            )
        chat_section.visible = not chat_section.visible
        ask_button.text = "Hide questions" if chat_section.visible else "Ask about this issue"
        page.update()

    ask_button = ft.OutlinedButton(
        "Ask about this issue",
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
                padding=ft.padding.symmetric(horizontal=16, vertical=14),
                content=ft.Column(
                    spacing=16,
                    controls=[
                        header_slot,
                        digest,
                        ask_button,
                        chat_section,
                        status,
                        sections_column,
                        ft.Divider(height=20, color="#222222"),
                        ft.Text(CREDIT, size=11, color=ft.Colors.GREY_600),
                        ft.Row(
                            [
                                ft.TextButton(
                                    "Open on bitcoinops.org",
                                    icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                                    on_click=lambda _: page.launch_url(url),
                                ),
                                ft.TextButton("License", on_click=lambda _: page.launch_url(OPTECH_LICENSE_URL)),
                            ],
                            wrap=True,
                        ),
                        ft.Container(height=20),
                    ],
                ),
            )
        ],
    )

    return ft.Column(
        expand=True,
        spacing=0,
        controls=[back_bar, ft.Container(height=1, bgcolor="#222222"), content],
    )
