import flet as ft
import requests
from datetime import datetime, timezone

all_news_cache = []


import xml.etree.ElementTree as ET
import html
import re

def fetch_news_from_api():
    URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(URL, headers=headers, timeout=7)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            news_list = []
            for item in items:
                title_node = item.find('title')
                title = title_node.text if title_node is not None else "Crypto News"
                
                link_node = item.find('link')
                link = link_node.text if link_node is not None else ""
                
                creator = item.find('{http://purl.org/dc/elements/1.1/}creator')
                publisher = creator.text if creator is not None else "CoinDesk"
                
                media = item.find('{http://search.yahoo.com/mrss/}content')
                img_url = media.attrib.get('url', '') if media is not None else ""
                
                # Önce detaylı içeriği aramayı deneriz
                content_node = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
                if content_node is not None and content_node.text:
                    description = content_node.text
                else:
                    # Bulamazsa kısa özete (description) düşeriz
                    desc_node = item.find('description')
                    description = desc_node.text if desc_node is not None else ""
                
                # Basit HTML temizliği
                if description:
                    description = html.unescape(description)
                    description = re.sub('<[^<]+>', '', description)
                
                news_list.append({
                    "title": title,
                    "link": link,
                    "publisher": publisher,
                    "description": description.strip(),
                    "thumbnail": {"resolutions": [{"url": img_url}]} if img_url else {}
                })
            return news_list
        return []
    except Exception as e:
        print(f"Fetch Error: {e}")
        return []


def get_image_url(item):
    try:
        return item["thumbnail"]["resolutions"][0]["url"]
    except:
        return "icon_clean.png"


def news_view_component(page: ft.Page, on_news_click):
    view_container = ft.Column(expand=True)
    
    def scroll_to_top(e):
        news_list.scroll_to(offset=0, duration=500)

    twitter_logo = ft.Container(
        content=ft.Icon(ft.Icons.ARROW_UPWARD_ROUNDED, color=ft.Colors.WHITE, size=24),
        bgcolor=ft.Colors.BLUE_500,
        padding=8,
        border_radius=25,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.Colors.with_opacity(0.4, ft.Colors.BLUE_500)),
        on_click=scroll_to_top,
        visible=False
    )
    logo_wrapper = ft.Row([twitter_logo], alignment=ft.MainAxisAlignment.CENTER)
    logo_stack_item = ft.Container(content=logo_wrapper, top=15, left=0, right=0)

    def handle_scroll(e: ft.OnScrollEvent):
        try:
            if float(e.pixels) > 300 and not twitter_logo.visible:
                twitter_logo.visible = True
                twitter_logo.update()
            elif float(e.pixels) < 300 and twitter_logo.visible:
                twitter_logo.visible = False
                twitter_logo.update()
        except:
            pass

    news_list = ft.ListView(expand=True, spacing=10, padding=10, on_scroll=handle_scroll)
    filter_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=5)

    def render_news(data):
        news_list.controls.clear()

        if not data:
            news_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No recent news found in this category.",
                        color=ft.Colors.GREY_400,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
            page.update()
            return

        for item in data:
            img_url = get_image_url(item)
            news_list.controls.append(
                ft.Card(
                    color=ft.Colors.TRANSPARENT,
                    elevation=0,
                    content=ft.Container(
                        padding=12,
                        bgcolor="#0F172A",
                        border_radius=16,
                        shadow=ft.BoxShadow(spread_radius=1, blur_radius=12, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)),
                        on_click=lambda _, i=item: on_news_click(i),
                        content=ft.Row(
                            [
                                ft.Image(
                                    src=img_url,
                                    width=80,
                                    height=80,
                                    fit="cover",
                                    border_radius=12,
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
                                            item.get("publisher", "CoinDesk"),
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
                padding=ft.padding.only(top=20, bottom=40),
                alignment=ft.alignment.center,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                            color=ft.Colors.GREY_600,
                            size=20,
                        ),
                        ft.Text(
                            "You've reached the end of the latest news.",
                            size=12,
                            color=ft.Colors.GREY_600,
                            italic=True,
                        ),
                        ft.Text(
                            f"Total {len(data)} articles scanned.",
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
                if selected_label.upper() in i.get("title", "").upper()
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
        view_container.controls.append(ft.Stack([news_list, logo_stack_item], expand=True))
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
