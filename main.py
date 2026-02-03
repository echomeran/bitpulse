import flet as ft
from views.news_view import news_view_component
from views.news_detail_view import news_detail_view_component
from views.whale_view import whale_view_component
from views.ai_view import ai_view_component

def main(page: ft.Page):
    # --- PENCERE VE SAYFA AYARLARI ---
    page.title = "BitPulse"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 400
    page.window.height = 750
    page.window.resizable = False
    page.padding = 0
    page.bgcolor = "#121212" # Modern koyu arka plan

    # --- NAVİGASYON VE İÇERİK YÖNETİMİ ---
    main_container = ft.Container(expand=True)

    def go_back_to_list(e):
        main_container.content = news_layout
        page.update()

    def open_news_detail(item):
        # Habere tıklandığında detay görünümüne geçiş
        main_container.content = news_detail_view_component(item, go_back_to_list)
        page.update()

    # --- VIEW BİLEŞENLERİNİ BAŞLATMA ---
    # news_view_component'e detay açma fonksiyonunu parametre olarak gönderiyoruz
    news_layout, update_news = news_view_component(page, open_news_detail)
    whale_layout = whale_view_component()
    ai_layout = ai_view_component()

    # --- MİLİMETRİK SİMETRİK VE İNCE HEADER ---
    header = ft.Container(
        height=50, # Şerit kalınlığı 50 birime sabitlendi
        bgcolor="#121212",
        padding=ft.padding.symmetric(horizontal=10),
        content=ft.Stack([
            # Sol: Yenileme Butonu (Dikeyde tam merkez)
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.REFRESH_ROUNDED,
                    on_click=lambda _: update_news(),
                    icon_color=ft.Colors.ORANGE_ACCENT,
                    icon_size=22,
                    padding=0, # Dikey kaymayı engellemek için iç boşluk sıfırlandı
                ),
                alignment=ft.alignment.center_left,
            ),
            # Orta: Tam Daire Logo (Milimetrik dikey ve yatay merkez)
            ft.Container(
                alignment=ft.alignment.center,
                content=ft.Container(
                    width=36,  # 50px şerit içinde en dengeli duran logo boyutu
                    height=36, 
                    border_radius=18, # Tam daire (Genişliğin tam yarısı)
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Image(
                        src="icon_clean.png", # Yeni daire logon
                        fit=ft.ImageFit.COVER,
                    )
                ),
            ),
        ])
    )

    # --- ALT NAVİGASYON BARI ---
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

    # Başlangıç ekranı ayarı
    main_container.content = news_layout
    
    # Ekrana ekleme (Boşluk bırakan Divider yerine 1px Container kullanıldı)
    page.add(
        header,
        ft.Container(height=1, bgcolor="#222222"), # Görünmez paddingleri olmayan ince çizgi
        main_container
    )
    
    # İlk verileri yükle
    update_news()

if __name__ == "__main__":
    # Windows Desktop uygulaması olarak başlatır
    ft.app(target=main, assets_dir="assets")