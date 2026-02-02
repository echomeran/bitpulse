import flet as ft
import requests # Ensure requests is installed: pip install requests

def fetch_cryptocompare_news(api_key):
    # Base URL for CryptoCompare News API
    # We filter by 'BTC' to get relevant Bitcoin data
    URL = f"https://min-api.cryptocompare.com/data/v2/news/?categories=BTC&api_key={api_key}"
    
    try:
        # Performing the HTTP GET request
        response = requests.get(URL)
        
        # Checking if the server responded correctly (HTTP 200)
        if response.status_code == 200:
            data = response.json()
            # The API returns a dictionary with a 'Data' key containing the list
            return data.get('Data', [])
        else:
            print(f"Server Error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Network Exception: {e}")
        return []

def news_view_component():
    # This is the default landing page for the app
    return ft.ListView(
        expand=True,
        spacing=10,
        padding=20,
        controls=[
            ft.Text("Global Bitcoin Feed", size=24, weight="bold"),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Text("News loading system is ready. Backend will be integrated later.", size=14)
                )
            )
        ]
    )