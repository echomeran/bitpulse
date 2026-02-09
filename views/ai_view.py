import flet as ft
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


def create_chat_bubble(text, is_user):
    bubble = ft.Container(
        content=ft.Text(text, color=ft.Colors.WHITE, size=13, selectable=True),
        bgcolor="#0078FF" if is_user else "#262626",
        padding=ft.Padding(12, 12, 12, 12),
        border_radius=ft.BorderRadius.only(
            top_left=15,
            top_right=15,
            bottom_left=15 if is_user else 5,
            bottom_right=5 if is_user else 15,
        ),
        width=280,
    )

    bubble.constraints = ft.BoxConstraints(max_width=280)

    return ft.Row(
        controls=[bubble],
        alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
    )


def build_knowledge_base(user_query, news_list, btc_price):
    context = f"CURRENT BTC PRICE: {btc_price}\n\nLATEST NEWS:\n"
    for item in news_list[:15]:
        context += f"- {item['title']}: {item['body']}\n"

    return f"""
    You are the BitPulse AI Expert. 
    Use the provided KNOWLEDGE BASE below to answer the user's question.
    If the answer is not in the news, use your general knowledge but mention it's not in the recent news.
    Be professional but friendly and cheerful. Do not write long paragraphs. 
    Context is:
    
    {context}
    
    USER QUESTION: {user_query}
    """


def ai_view_component(page: ft.Page):
    chat_list = ft.ListView(expand=True, spacing=15, auto_scroll=True, padding=10)

    async def send_message_click(e):
        user_text = chat_input.value.strip()
        if user_text != "":
            chat_list.controls.append(create_chat_bubble(user_text, is_user=True))
            chat_input.value = ""
            page.update()

            typing_indicator = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            "Thinking...",
                            size=12,
                            italic=True,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.ProgressRing(width=12, height=12, stroke_width=2),
                    ],
                    spacing=10,
                ),
                padding=10,
            )
            chat_list.controls.append(typing_indicator)
            page.update()

            from views.news_view import all_news_cache
            from views.market_view import live_price_ref

            smart_prompt = build_knowledge_base(
                user_text, all_news_cache, live_price_ref
            )

            try:
                response = await client.aio.models.generate_content(
                    model="gemini-3-flash-preview", contents=smart_prompt
                )

                chat_list.controls.remove(typing_indicator)

                chat_list.controls.append(
                    create_chat_bubble(response.text, is_user=False)
                )
            except Exception as ex:
                if typing_indicator in chat_list.controls:
                    chat_list.controls.remove(typing_indicator)
                chat_list.controls.append(
                    ft.Text(f"Error: {ex}", color=ft.Colors.RED_ACCENT)
                )

            page.update()

    chat_input = ft.TextField(
        hint_text="Ask something about crypto...",
        expand=True,
        on_submit=send_message_click,
        border_radius=15,
        bgcolor="#1E1E1E",
        border_color="#333333",
    )

    send_button = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        on_click=send_message_click,
        icon_color=ft.Colors.ORANGE_ACCENT,
    )

    return ft.Column(
        [
            ft.Container(
                content=ft.Text("BitPulse AI Advisor", size=24, weight="bold"),
                padding=ft.Padding.only(left=10, top=10),
            ),
            ft.Divider(height=1, color="#333333"),
            chat_list,
            ft.Container(
                padding=10,
                content=ft.Row([chat_input, send_button]),
            ),
        ],
        expand=True,
    )
