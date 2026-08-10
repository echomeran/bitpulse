import flet as ft
import threading

from views.ai_view import ai_view_component
from views.market_view import market_view_component
from views.news_detail_view import news_detail_view_component
from views.news_view import news_view_component


def main(page: ft.Page):
    page.title = "BitPulse"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = "#121212"
    page.safe_area_padding = False

    if page.platform not in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
        page.window.width = 400
        page.window.height = 750
        page.window.resizable = False

    main_container = ft.Container(expand=True)
    selected_news_item = {"value": None}

    def go_back_to_list(e=None):
        selected_news_item["value"] = None
        page.go("/")

    def open_news_detail(item):
        selected_news_item["value"] = item
        page.go("/news-detail")

    news_layout, update_news = news_view_component(page, open_news_detail)
    market_layout, update_market = market_view_component(page)
    ai_layout = ai_view_component(page)

    refresh_button_container = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.REFRESH_ROUNDED,
            on_click=lambda _: threading.Thread(target=update_news, daemon=True).start(),
            icon_color=ft.Colors.ORANGE_ACCENT,
            icon_size=20,
            tooltip="Refresh news",
        ),
        width=40,
    )

    def handle_nav_change(e):
        idx = e.control.selected_index
        refresh_button_container.visible = idx == 0

        if idx == 0:
            main_container.content = news_layout
        elif idx == 1:
            main_container.content = ai_layout
        else:
            main_container.content = market_layout
            threading.Thread(target=update_market, daemon=True).start()
        page.update()

    navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=handle_nav_change,
        bgcolor="#1A1A1A",
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.NEWSPAPER, label="News"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="AI Advisor"),
            ft.NavigationBarDestination(icon=ft.Icons.INSIGHTS, label="Market"),
        ],
    )

    header = ft.Container(
        height=48,
        bgcolor="#121212",
        padding=ft.padding.symmetric(horizontal=5),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                refresh_button_container,
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
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
    home_content = ft.SafeArea(
        expand=True,
        minimum_padding=ft.padding.only(top=0),
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

    def route_change(e=None):
        if not page.views or page.views[0].route != "/":
            page.views.clear()
            page.views.append(
                ft.View(
                    route="/",
                    bgcolor="#121212",
                    padding=0,
                    controls=[home_content],
                    navigation_bar=navigation_bar,
                )
            )

        if page.route == "/":
            # If we returned to home, pop any extra views
            while len(page.views) > 1:
                page.views.pop()

        elif page.route == "/news-detail" and selected_news_item["value"]:
            if len(page.views) == 1 or page.views[-1].route != "/news-detail":
                page.views.append(
                    ft.View(
                        route="/news-detail",
                        bgcolor="#121212",
                        padding=0,
                        controls=[
                            ft.SafeArea(
                                expand=True,
                                minimum_padding=ft.padding.only(top=0),
                                content=news_detail_view_component(
                                    selected_news_item["value"], go_back_to_list, page
                                ),
                            )
                        ],
                    )
                )
        page.update()

    def handle_view_pop(e):
        """Handle Android back button and view stack pops correctly."""
        if len(page.views) > 1:
            page.views.pop()
            # Clean up the selected item when leaving detail view
            if selected_news_item["value"] and page.views[-1].route == "/":
                selected_news_item["value"] = None
            page.route = page.views[-1].route
            page.update()
        else:
            # Already at root — let the OS handle the back press (minimize app)
            pass

    page.on_route_change = route_change
    page.on_view_pop = handle_view_pop
    route_change()
    threading.Thread(target=update_news, daemon=True).start()


if __name__ == "__main__":
    ft.app(main, assets_dir="assets")
