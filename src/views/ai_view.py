import flet as ft

from views.chat_panel import chat_panel

GREETING = (
    "I'm BitPulse, a Bitcoin market assistant. I follow the live price, market sentiment "
    "and today's crypto headlines, and I can explain what's going on."
)


PRIVACY_POLICY_URL = "https://echomeran.github.io/bitpulse/privacy.html"

# Shown above the chat. The answers are AI-generated and educational, so say so plainly.
DISCLAIMER = (
    "For education only, not financial advice. Answers are AI-generated and can be wrong; "
    "check important facts and do your own research before any decision."
)


def ai_view_component(page: ft.Page):
    return ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("BitPulse AI Assistant", size=24, weight="bold"),
                        ft.Text(DISCLAIMER, size=11, color=ft.Colors.GREY_500),
                        ft.TextButton(
                            "Privacy policy",
                            on_click=lambda _: page.launch_url(PRIVACY_POLICY_URL),
                            style=ft.ButtonStyle(
                                color=ft.Colors.BLUE_300, padding=ft.padding.all(0)
                            ),
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
