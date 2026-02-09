import flet as ft


def news_detail_view_component(item, on_back_click):
    # Image URL handling logic
    raw_img = item.get("imageurl", "")
    img_url = (
        raw_img
        if raw_img.startswith("http")
        else f"https://www.cryptocompare.com{raw_img}"
    )

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
                            f"Source: {item['source_info']['name']}",
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Divider(height=30),
                        ft.Text(
                            item["body"],
                            size=16,
                            selectable=True,
                            style=ft.TextStyle(height=1.5),
                        ),
                    ]
                ),
            ),
        ],
    )
