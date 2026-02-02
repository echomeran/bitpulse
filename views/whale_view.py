import flet as ft

def whale_view_component():
    # Placeholder for the Whale Alerts tracker
    return ft.ListView(
        expand=True,
        spacing=10,
        padding=20,
        controls=[
            ft.Text("Whale Movement Alerts", size=24, weight="bold"),
            ft.Divider(),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Text("Real-time on-chain data will be displayed here.", size=14)
                )
            )
        ]
    )