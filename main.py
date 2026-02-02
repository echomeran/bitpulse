import flet as ft
from views.news_view import news_view_component
from views.whale_view import whale_view_component
from views.ai_view import ai_view_component

def main(page: ft.Page):
    # PAGE INITIALIZATION
    page.title = "BitPulse"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 400
    page.window.height = 750
    page.window.resizable = False

    # LOADING COMPONENTS FROM OTHER FILES
    # We initialize them as variables
    news_page = news_view_component()
    whale_page = whale_view_component()
    ai_page = ai_view_component()

    # MAIN CONTENT CONTAINER
    # Default is set to news_page
    container = ft.Container(content=news_page, expand=True)

    # NAVIGATION LOGIC
    def handle_nav_change(e):
        idx = e.control.selected_index
        if idx == 0:
            container.content = news_page
        elif idx == 1:
            container.content = ai_page
        elif idx == 2:
            container.content = whale_page
        page.update()

    # BOTTOM NAVIGATION BAR
    # Order: News (Left), AI (Center), Whales (Right)
    page.navigation_bar = ft.NavigationBar(
        selected_index=0, # This sets 'News' as the default tab
        on_change=handle_nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.NEWSPAPER, label="News"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="AI Advisor"),
            ft.NavigationBarDestination(icon=ft.Icons.QUERY_STATS, label="Whales"),
        ]
    )

    page.add(container)

if __name__ == "__main__":
    ft.app(target=main)