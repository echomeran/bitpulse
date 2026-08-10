import flet as ft

from services.ai_service import get_api_url
import services.news_service as news_service
import services.market_service as market_service


def create_chat_bubble(text, is_user):
    bubble = ft.Container(
        content=ft.Text(text, color=ft.Colors.WHITE, size=14, selectable=True),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#2563EB", "#1D4ED8"] if is_user else ["#0F172A", "#1E293B"],
        ),
        padding=ft.padding.all(14),
        border_radius=ft.border_radius.only(
            top_left=18,
            top_right=18,
            bottom_left=18 if is_user else 4,
            bottom_right=4 if is_user else 18,
        ),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
        ),
        width=290,
    )
    bubble.constraints = ft.BoxConstraints(max_width=280)
    return ft.Row(
        controls=[bubble],
        alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
    )


def ai_view_component(page: ft.Page):
    import asyncio
    from services.ai_service import send_chat_message

    chat_list = ft.ListView(expand=True, spacing=15, auto_scroll=True, padding=10)
    conversation_history: list[dict] = []

    async def send_message_click(e):
        user_text = chat_input.value.strip()
        if not user_text:
            return

        api_url = get_api_url()
        if not api_url:
            chat_list.controls.append(
                create_chat_bubble(
                    "AI is being prepared for the mobile release. Please try again soon.",
                    is_user=False,
                )
            )
            page.update()
            return

        chat_list.controls.append(create_chat_bubble(user_text, is_user=True))
        chat_input.value = ""
        page.update()

        typing_indicator = ft.Container(
            content=ft.Row(
                [
                    ft.ProgressRing(
                        width=16, height=16, stroke_width=2, color=ft.Colors.BLUE_400
                    ),
                    ft.Text(
                        "BitPulse is thinking…",
                        size=13,
                        italic=True,
                        color=ft.Colors.BLUE_300,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.all(12),
            bgcolor="#0F172A",
            border_radius=20,
            width=180,
        )
        chat_list.controls.append(typing_indicator)
        page.update()

        payload_news = [
            {"title": item.get("title", ""), "publisher": item.get("publisher", "Unknown")}
            for item in news_service.all_news_cache[:12]
        ]

        try:
            reply, error_message = await asyncio.to_thread(
                send_chat_message,
                api_url,
                user_text,
                conversation_history,
                market_service.live_price_ref,
                payload_news,
            )
            if typing_indicator in chat_list.controls:
                chat_list.controls.remove(typing_indicator)
            if error_message:
                chat_list.controls.append(
                    create_chat_bubble(error_message, is_user=False)
                )
            else:
                conversation_history.extend(
                    [
                        {"role": "user", "text": user_text},
                        {"role": "assistant", "text": reply},
                    ]
                )
                del conversation_history[:-8]
                chat_list.controls.append(
                    create_chat_bubble(reply, is_user=False)
                )
        except Exception:
            if typing_indicator in chat_list.controls:
                chat_list.controls.remove(typing_indicator)
            chat_list.controls.append(
                create_chat_bubble(
                    "Could not reach the AI service. Check your connection and try again.",
                    is_user=False,
                )
            )
        finally:
            page.update()

    chat_input = ft.TextField(
        hint_text="Ask BitPulse something…",
        hint_style=ft.TextStyle(color=ft.Colors.GREY_600),
        expand=True,
        on_submit=send_message_click,
        border_radius=25,
        bgcolor="#0F172A",
        border_color="#1E293B",
        focused_border_color=ft.Colors.BLUE_500,
        content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
        max_length=600,
    )

    send_button = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            on_click=send_message_click,
            icon_color=ft.Colors.WHITE,
            icon_size=20,
            tooltip="Send message",
        ),
        bgcolor=ft.Colors.BLUE_600,
        shape=ft.BoxShape.CIRCLE,
        margin=ft.padding.only(left=8),
    )

    return ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("BitPulse AI Advisor", size=24, weight="bold"),
                        ft.Text(
                            "Market education only — not financial advice.",
                            size=11,
                            color=ft.Colors.GREY_500,
                        ),
                    ],
                    spacing=2,
                ),
                padding=ft.padding.only(left=10, top=10),
            ),
            ft.Divider(height=1, color="#333333"),
            chat_list,
            ft.Container(padding=10, content=ft.Row([chat_input, send_button])),
        ],
        expand=True,
    )
