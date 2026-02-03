import flet as ft
import requests
from datetime import datetime, timezone

def fetch_news_from_api():
    # We fetch 50 news items - usually enough to cover the last 12-24 hours
    URL = "https://min-api.cryptocompare.com/data/v2/news/?categories=BTC&limit=50"
    
    # We define our premium list just in case you want to prioritize them
    # But for now, we will accept ALL sources provided by CryptoCompare
    try:
        response = requests.get(URL, timeout=7)
        if response.status_code == 200:
            data = response.json().get("Data", [])
            
            # Since we want the app to feel "full", we just return everything
            # Sorted by time automatically by the API
            return data
        return []
    except Exception as e:
        print(f"Fetch Error: {e}")
        return []

def get_image_url(item):
    raw_url = item.get('imageurl', '')
    return raw_url if raw_url.startswith('http') else f"https://www.cryptocompare.com{raw_url}"

def news_view_component(page: ft.Page, on_news_click):
    view_container = ft.Column(expand=True)
    news_list = ft.ListView(expand=True, spacing=10, padding=10)
    
    # Filter Row declared as a variable to access its children
    filter_row = ft.Row(scroll=ft.ScrollMode.AUTO)

    def show_detail(item):
        img_url = get_image_url(item)
        detail_view = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(padding=10, content=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: back_to_list())),
                ft.Image(src=img_url, width=page.window.width, fit=ft.ImageFit.FIT_WIDTH),
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Text(item['title'], size=22, weight="bold"),
                        ft.Text(f"Source: {item['source_info']['name']}", color=ft.Colors.GREY_400),
                        ft.Divider(),
                        ft.Text(item['body'], size=16, selectable=True, style=ft.TextStyle(height=1.5)),
                    ])
                )
            ]
        )
        view_container.controls.clear()
        view_container.controls.append(detail_view)
        page.update()

    def back_to_list():
        view_container.controls.clear()
        view_container.controls.append(filter_row)
        view_container.controls.append(news_list)
        page.update()

    def render_news(data):
        news_list.controls.clear()
        for item in data:
            img_url = get_image_url(item)
            news_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        # Tıklanınca main.py'dan gelen fonksiyonu çalıştır
                        on_click=lambda _, i=item: on_news_click(i),
                        content=ft.Row([
                            ft.Image(src=img_url, width=80, height=80, fit=ft.ImageFit.COVER, border_radius=8),
                            ft.Column([
                                ft.Text(item['title'], size=14, weight="bold", max_lines=2),
                                ft.Text(item['source_info']['name'], size=11, color=ft.Colors.GREY_500),
                            ], expand=True)
                        ])
                    )
                )
            )
        page.update()

    # LOGIC: Single-select filter logic
    def handle_filter(e):
        selected_label = e.control.label.value
        
        # Deselect all other chips
        for chip in filter_row.controls:
            chip.selected = (chip.label.value == selected_label)
        
        # Filter the data
        if selected_label == "All News":
            render_news(all_news_cache)
        else:
            filtered = [
                i for i in all_news_cache 
                if selected_label.upper() in i.get('categories', '').upper()
            ]
            render_news(filtered)
        
        page.update()

    # Initializing Chips
    filter_row.controls = [
    ft.Chip(label=ft.Text("All News"), selected=True, on_select=handle_filter),
    ft.Chip(label=ft.Text("Regulation"), on_select=handle_filter),
    ft.Chip(label=ft.Text("Trading"), on_select=handle_filter),
    ft.Chip(label=ft.Text("Technology"), on_select=handle_filter),
]

    def update_news():
        global all_news_cache
        news_list.controls.clear()
        news_list.controls.append(ft.ProgressBar(color=ft.Colors.ORANGE_ACCENT))
        page.update()
        
        all_news_cache = fetch_news_from_api()
        render_news(all_news_cache)
        back_to_list()

    return view_container, update_news