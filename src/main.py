import logging
import os
import threading

import flet as ft

import services.market_service as market_service
from services import i18n
from services.ai_service import get_api_url
from services.i18n import t
from views.ai_view import ai_view_component
from views.market_view import market_view_component
from views.news_detail_view import news_detail_view_component
from views.news_view import news_view_component
from views.newsletter_view import newsletter_view_component


def exit_with_the_screen(page: ft.Page) -> None:
    """End the process when Android destroys the app's screen (e.g. Back on the home screen).

    Android keeps the process, and with it this Python program, alive after the screen closes.
    The next launch then starts a new screen in the same process, but the embedded Python refuses
    to run a second program ("Python already initialized ... skipping execution"), so the app
    opens blank. Exiting here makes the next launch a clean cold start.
    """

    def leave(_=None):
        logging.getLogger("bitpulse").info("Screen closed; ending the process for a clean restart")
        os._exit(0)

    def on_lifecycle(e):
        if e.state == ft.AppLifecycleState.DETACH:
            leave()

    page.on_disconnect = leave
    page.on_app_lifecycle_state_change = on_lifecycle


def language_menu(on_change) -> ft.PopupMenuButton:
    """Header button for the interface language; the current one is ticked."""
    return ft.PopupMenuButton(
        icon=ft.Icons.TRANSLATE_ROUNDED,
        icon_color=ft.Colors.GREY_400,
        icon_size=20,
        tooltip=t("Language"),
        items=[
            ft.PopupMenuItem(
                text=name,
                checked=code == i18n.language(),
                on_click=lambda _, c=code: on_change(c),
            )
            for code, name in i18n.LANGUAGES.items()
        ],
    )


def main(page: ft.Page):
    i18n.load_language()
    page.title = "BitPulse"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = "#121212"
    page.safe_area_padding = False

    if page.platform not in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
        page.window.width = 400
        page.window.height = 750
        page.window.resizable = False
    else:
        exit_with_the_screen(page)

    main_container = ft.Container(expand=True)
    selected_news_item = {"value": None}
    selected_newsletter = {"value": None}

    def go_back_to_list(e=None):
        selected_news_item["value"] = None
        selected_newsletter["value"] = None
        page.go("/")

    def open_news_detail(item):
        selected_news_item["value"] = item
        page.go("/news-detail")

    def open_newsletter(item):
        selected_newsletter["value"] = item
        page.go("/newsletter")

    news_layout, update_news = news_view_component(page, open_news_detail, open_newsletter)
    market_layout, update_market = market_view_component(page)
    ai_layout = ai_view_component(page)

    refresh_button_container = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.REFRESH_ROUNDED,
            on_click=lambda _: threading.Thread(target=update_news, daemon=True).start(),
            icon_color=ft.Colors.ORANGE_ACCENT,
            icon_size=20,
            tooltip=t("Refresh news"),
        ),
        width=40,
    )

    def change_language(code: str):
        """Save the choice and build every screen again in the new language."""
        if code == i18n.language():
            return
        i18n.set_language(code)
        page.views.clear()
        page.update()
        main(page)

    def handle_nav_change(e):
        idx = e.control.selected_index
        # Hide only the button: the 40 px slot stays, so the logo stays centred on every tab.
        refresh_button_container.content.visible = idx == 0

        if idx == 0:
            main_container.content = news_layout
        elif idx == 1:
            main_container.content = ai_layout
        else:
            main_container.content = market_layout
            update_market()
        page.update()

    navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=handle_nav_change,
        bgcolor="#1A1A1A",
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.NEWSPAPER, label=t("News")),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label=t("AI Assistant")),
            ft.NavigationBarDestination(icon=ft.Icons.INSIGHTS, label=t("Market")),
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
                ft.Container(width=40, content=language_menu(change_language)),
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
        elif page.route == "/newsletter" and selected_newsletter["value"]:
            if page.views[-1].route != "/newsletter":
                page.views.append(
                    ft.View(
                        route="/newsletter",
                        bgcolor="#121212",
                        padding=0,
                        controls=[
                            ft.SafeArea(
                                expand=True,
                                minimum_padding=ft.padding.only(top=0),
                                content=newsletter_view_component(
                                    selected_newsletter["value"], go_back_to_list, page
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

    def prefetch_market():
        """Warm the live price and the 1-month summary used as LLM context."""
        api_url = get_api_url()
        data_1d = market_service.fetch_price_from_api(api_url, "1D")
        if data_1d and data_1d.get("prices"):
            market_service.live_price_ref = f"${data_1d['current_price']:,.2f}"
            market_service.save_market_cache("1D", data_1d)

        data_1m = market_service.fetch_price_from_api(api_url, "1M")
        if data_1m and data_1m.get("prices"):
            market_service.market_summary_ref = market_service.build_market_summary(data_1m)
            market_service.save_market_cache("1M", data_1m)

    threading.Thread(target=update_news, daemon=True).start()
    threading.Thread(target=prefetch_market, daemon=True).start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ft.app(main, assets_dir="assets")
