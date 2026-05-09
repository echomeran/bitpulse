import flet as ft
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


def create_chat_bubble(text, is_user):
    bubble = ft.Container(
        content=ft.Text(text, color=ft.Colors.WHITE, size=14, selectable=True),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#2563EB", "#1D4ED8"] if is_user else ["#0F172A", "#1E293B"]
        ),
        padding=ft.padding.all(14),
        border_radius=ft.border_radius.only(
            top_left=18,
            top_right=18,
            bottom_left=18 if is_user else 4,
            bottom_right=4 if is_user else 18,
        ),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK)),
        width=290,
    )

    bubble.constraints = ft.BoxConstraints(max_width=280)

    return ft.Row(
        controls=[bubble],
        alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
    )


def build_knowledge_base(user_query, news_list, btc_price):
    context = f"CURRENT BTC PRICE: {btc_price}\n\nLATEST NEWS:\n"
    if isinstance(news_list, list):
        for item in news_list[:15]:
            if isinstance(item, dict):
                context += f"- {item.get('title', '')} (Source: {item.get('publisher', 'Unknown')})\n"

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
                        ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.BLUE_400),
                        ft.Text(
                            "BitPulse is thinking...",
                            size=13,
                            italic=True,
                            color=ft.Colors.BLUE_300,
                        ),
                    ],
                    spacing=12,
                ),
                padding=ft.padding.all(12),
                bgcolor="#0F172A",
                border_radius=20,
                width=180,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK))
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
                    model="gemini-2.5-flash", contents=smart_prompt
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
        hint_text="Ask BitPulse something...",
        hint_style=ft.TextStyle(color=ft.Colors.GREY_600),
        expand=True,
        on_submit=send_message_click,
        border_radius=25,
        bgcolor="#0F172A",
        border_color="#1E293B",
        focused_border_color=ft.Colors.BLUE_500,
        content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
    )

    send_button = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            on_click=send_message_click,
            icon_color=ft.Colors.WHITE,
            icon_size=20,
        ),
        bgcolor=ft.Colors.BLUE_600,
        shape=ft.BoxShape.CIRCLE,
        margin=ft.padding.only(left=8),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE_500))
    )

    return ft.Column(
        [
            ft.Container(
                content=ft.Text("BitPulse AI Advisor", size=24, weight="bold"),
                padding=ft.padding.only(left=10, top=10),
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
