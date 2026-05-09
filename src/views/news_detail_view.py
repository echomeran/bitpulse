import flet as ft
import requests
from bs4 import BeautifulSoup

def scrape_news(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            paragraphs = soup.find_all('p')
            content = ""
            count = 0
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 50 and "cookie" not in text.lower():
                    content += text + "\n\n"
                    count += 1
                if count >= 8: # Show max 8 paragraphs to keep it clean
                    break
            if content:
                return content
    except:
        pass
    return None


def news_detail_view_component(item, on_back_click):
    try:
        img_url = item["thumbnail"]["resolutions"][0]["url"]
    except:
        img_url = "icon_clean.png"

    scraped_content = scrape_news(item.get("link", ""))
    display_text = scraped_content if scraped_content else item.get("description", "No detailed content available.")

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            # Back Button
            ft.Container(
                padding=10,
                content=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=on_back_click),
            ),
            # Article Image
            ft.Image(src=img_url, fit="fitWidth", border_radius=10),
            # Article Content
            ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Text(item["title"], size=22, weight="bold"),
                        ft.Text(
                            f"Source: {item.get('publisher', 'CoinDesk')}",
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Divider(height=30),
                        ft.Text(
                            display_text,
                            size=15,
                            selectable=True,
                            style=ft.TextStyle(height=1.6),
                        ),
                        ft.Divider(height=30),
                        ft.Text("Read full article on website:", color=ft.Colors.GREY_500, size=12),
                        ft.Text(
                            item.get("link", ""),
                            size=14,
                            selectable=True,
                            color=ft.Colors.BLUE_400,
                        ),
                    ]
                ),
            ),
        ],
    )
