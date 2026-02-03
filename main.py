import flet as ft
from views.news_view import news_view_component
from views.news_detail_view import news_detail_view_component
from views.whale_view import whale_view_component
from views.ai_view import ai_view_component

def main(page: ft.Page):
    # WINDOW CONFIGURATION: Fixed size for mobile-app feel
    page.title = "BitPulse"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 400
    page.window.height = 750
    page.window.resizable = False
    page.padding = 0
    page.bgcolor = "#121212"

    # NAVIGATION AND CONTENT MANAGEMENT
    main_container = ft.Container(expand=True)

    def go_back_to_list(e):
        main_container.content = news_layout
        page.update()

    def open_news_detail(item):
        # Switches the view to the detail page
        main_container.content = news_detail_view_component(item, go_back_to_list)
        page.update()

    # INITIALIZING VIEW COMPONENTS
    # Passing the detail function as a parameter
    news_layout, update_news = news_view_component(page, open_news_detail)
    whale_layout = whale_view_component()
    ai_layout = ai_view_component()

    # PIXEL-PERFECT SYMMETRICAL HEADER
    header = ft.Container(
        height=48, # Standard modern UI header height
        bgcolor="#121212",
        padding=ft.padding.symmetric(horizontal=5),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # LEFT: Action button with fixed width
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.REFRESH_ROUNDED,
                        on_click=lambda _: update_news(),
                        icon_color=ft.Colors.ORANGE_ACCENT,
                        icon_size=20,
                        padding=0,
                    ),
                    width=40,
                ),
                # CENTER: Circular Logo (Centered via expand)
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    content=ft.Container(
                        width=32,
                        height=32,
                        border_radius=16, # radius = width/2 for a perfect circle
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Image(src="icon_clean.png", fit=ft.ImageFit.COVER),
                    ),
                ),
                # RIGHT: Empty container to balance the Row and center the logo
                ft.Container(width=40), 
            ]
        )
    )

    # NAVIGATION LOGIC
    def handle_nav_change(e):
        idx = e.control.selected_index
        if idx == 0:
            main_container.content = news_layout
            update_news()
        elif idx == 1:
            main_container.content = ai_layout
        elif idx == 2:
            main_container.content = whale_layout
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=handle_nav_change,
        bgcolor="#1A1A1A",
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.NEWSPAPER, label="News"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="AI Advisor"),
            ft.NavigationBarDestination(icon=ft.Icons.QUERY_STATS, label="Whales"),
        ]
    )

    main_container.content = news_layout
    
    # Adding the final components to the page
    page.add(
        header,
        # 1px line to remove the unwanted spacing from ft.Divider
        ft.Container(height=1, bgcolor="#222222"), 
        main_container
    )
    
    update_news()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")