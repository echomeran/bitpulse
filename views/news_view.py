import flet as ft
import requests
from datetime import datetime, timezone

all_news_cache = []


def fetch_news_from_api():
    URL = "https://min-api.cryptocompare.com/data/v2/news/?categories=BTC&limit=50"
    try:
        response = requests.get(URL, timeout=7)
        if response.status_code == 200:
            return response.json().get("Data", [])
        return []
    except Exception as e:
        print(f"Fetch Error: {e}")
        return []


def get_image_url(item):
    raw_url = item.get("imageurl", "")
    return (
        raw_url
        if raw_url.startswith("http")
        else f"https://www.cryptocompare.com{raw_url}"
    )


def news_view_component(page: ft.Page, on_news_click):
    view_container = ft.Column(expand=True)
    news_list = ft.ListView(expand=True, spacing=10, padding=10)
    filter_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=5)

    def render_news(data):
        news_list.controls.clear()

        if not data:
            news_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Bu kategoride güncel haber bulunamadı.",
                        color=ft.Colors.GREY_400,
                    ),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                )
            )
            page.update()
            return

        for item in data:
            img_url = get_image_url(item)
            news_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        on_click=lambda _, i=item: on_news_click(i),
                        content=ft.Row(
                            [
                                ft.Image(
                                    src=img_url,
                                    width=80,
                                    height=80,
                                    fit="cover",
                                    border_radius=8,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            item["title"],
                                            size=14,
                                            weight="bold",
                                            max_lines=2,
                                        ),
                                        ft.Text(
                                            item["source_info"]["name"],
                                            size=11,
                                            color=ft.Colors.GREY_500,
                                        ),
                                    ],
                                    expand=True,
                                ),
                            ]
                        ),
                    )
                )
            )

        news_list.controls.append(
            ft.Container(
                padding=ft.Padding.only(top=20, bottom=40),
                alignment=ft.Alignment.CENTER,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                            color=ft.Colors.GREY_600,
                            size=20,
                        ),
                        ft.Text(
                            "En güncel haberlerin sonuna geldin.",
                            size=12,
                            color=ft.Colors.GREY_600,
                            italic=True,
                        ),
                        ft.Text(
                            f"Toplam {len(data)} içerik tarandı.",
                            size=10,
                            color=ft.Colors.GREY_700,
                        ),
                    ],
                ),
            )
        )
        page.update()

    def handle_filter(e):
        selected_label = e.control.label.value
        for chip in filter_row.controls:
            chip.selected = chip.label.value == selected_label

        if selected_label == "All News":
            render_news(all_news_cache)
        else:
            filtered = [
                i
                for i in all_news_cache
                if selected_label.upper() in i.get("categories", "").upper()
            ]
            render_news(filtered)

    filter_row.controls = [
        ft.Chip(label=ft.Text("All News"), selected=True, on_select=handle_filter),
        ft.Chip(label=ft.Text("Trading"), on_select=handle_filter),
        ft.Chip(label=ft.Text("Regulation"), on_select=handle_filter),
        ft.Chip(label=ft.Text("Mining"), on_select=handle_filter),
        ft.Chip(label=ft.Text("Market"), on_select=handle_filter),
        ft.Chip(label=ft.Text("Blockchain"), on_select=handle_filter),
    ]

    def back_to_list():
        view_container.controls.clear()
        view_container.controls.append(filter_row)
        view_container.controls.append(news_list)
        page.update()

    def update_news():
        global all_news_cache
        news_list.controls.clear()
        news_list.controls.append(ft.ProgressBar(color=ft.Colors.ORANGE_ACCENT))
        page.update()

        all_news_cache = fetch_news_from_api()
        render_news(all_news_cache)
        back_to_list()

    return view_container, update_news
