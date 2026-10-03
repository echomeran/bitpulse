import flet as ft

from views.chat_panel import chat_panel


def ai_view_component(page: ft.Page):
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
            chat_panel(page),
        ],
        expand=True,
    )
