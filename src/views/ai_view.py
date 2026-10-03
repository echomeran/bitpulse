import flet as ft

from views.chat_panel import chat_panel

GREETING = (
    "Hi, I'm BitPulse. I can see the live BTC price, the Fear & Greed index and today's "
    "headlines, so ask me things like \"why is the price down today?\", \"what does this "
    "week's news mean?\" or \"explain the halving\"."
)


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
            chat_panel(page, greeting=GREETING),
        ],
        expand=True,
    )
