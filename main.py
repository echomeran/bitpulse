import flet as ft
import threading
from views.news_view import news_view_component
from views.news_detail_view import news_detail_view_component
from views.market_view import market_view_component
from views.ai_view import ai_view_component


def main(page: ft.Page):
    page.title = "BitPulse"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = "#121212"

    if page.platform not in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
        page.window.width = 400
        page.window.height = 750
        page.window.resizable = False

    main_container = ft.Container(expand=True)

    def go_back_to_list(e=None):
        main_container.content = news_layout
        page.update()

    def open_news_detail(item):
        main_container.content = news_detail_view_component(item, go_back_to_list)
        page.update()

    def handle_view_pop(e):
        if main_container.content != news_layout:
            go_back_to_list()
        else:
            page.window_destroy()

    page.on_view_pop = handle_view_pop

    news_layout, update_news = news_view_component(page, open_news_detail)
    market_layout, update_market = market_view_component(page)
    ai_layout = ai_view_component(page)

    def handle_nav_change(e):
        idx = e.control.selected_index

        refresh_button_container.visible = idx == 0
        right_placeholder.visible = idx == 0

        if idx == 0:
            main_container.content = news_layout
            threading.Thread(target=update_news, daemon=True).start()
        elif idx == 1:
            main_container.content = ai_layout
        elif idx == 2:
            main_container.content = market_layout
            threading.Thread(target=update_market, daemon=True).start()
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=handle_nav_change,
        bgcolor="#1A1A1A",
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.NEWSPAPER, label="News"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="AI Advisor"),
            ft.NavigationBarDestination(icon=ft.Icons.INSIGHTS, label="Market"),
        ],
    )

    refresh_button_container = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.REFRESH_ROUNDED,
            on_click=lambda _: threading.Thread(
                target=update_news, daemon=True
            ).start(),
            icon_color=ft.Colors.ORANGE_ACCENT,
            icon_size=20,
        ),
        width=40,
    )

    right_placeholder = ft.Container(width=40)

    header = ft.Container(
        height=48,
        bgcolor="#121212",
        padding=ft.Padding.symmetric(horizontal=5),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                refresh_button_container,
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Container(
                        width=32,
                        height=32,
                        border_radius=16,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Image(src="icon_clean.png", fit="cover"),
                    ),
                ),
                ft.Container(width=40),
            ],
        ),
    )

    main_container.content = news_layout

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    header,
                    ft.Container(height=1, bgcolor="#222222"),
                    main_container,
                ],
            ),
        )
    )

    threading.Thread(target=update_news, daemon=True).start()


if __name__ == "__main__":

    ft.run(main, assets_dir="assets")
