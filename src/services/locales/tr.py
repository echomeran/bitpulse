"""Turkish."""

MONTHS = ("Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara")

STRINGS = {
    # main
    "News": "Haberler",
    "AI Assistant": "AI Asistan",
    "Market": "Piyasa",
    "Refresh news": "Haberleri yenile",
    "Language": "Dil",
    # AI tab and chat
    "BitPulse AI Assistant": "BitPulse AI Asistan",
    "I'm BitPulse, a Bitcoin market assistant. I follow the live price, market sentiment "
    "and today's crypto headlines, and I can explain what's going on.": (
        "Ben BitPulse, bir Bitcoin piyasa asistanıyım. Canlı fiyatı, piyasa duyarlılığını ve "
        "günün kripto başlıklarını takip ediyor, neler olduğunu anlatabiliyorum."
    ),
    "For education only, not financial advice. Answers are AI-generated and can be wrong; "
    "check important facts and do your own research before any decision.": (
        "Yalnızca eğitim amaçlıdır, yatırım tavsiyesi değildir. Cevapları yapay zeka yazar ve "
        "yanlış olabilir; önemli bilgileri doğrula ve bir karar vermeden önce kendi araştırmanı yap."
    ),
    "Privacy policy": "Gizlilik politikası",
    "AI is being prepared for the mobile release. Please try again soon.": (
        "Yapay zeka mobil sürüm için hazırlanıyor. Lütfen birazdan tekrar dene."
    ),
    "Report": "Bildir",
    "Report this answer as wrong, harmful or offensive": "Bu cevabı yanlış, zararlı veya rahatsız edici olarak bildir",
    "Reported. Thank you.": "Bildirildi. Teşekkürler.",
    "Could not send report. Try again.": "Bildirim gönderilemedi. Tekrar dene.",
    "Report this answer": "Bu cevabı bildir",
    "What is wrong with it?": "Sorun ne?",
    "Wrong or misleading": "Yanlış veya yanıltıcı",
    "Harmful or dangerous": "Zararlı veya tehlikeli",
    "Offensive": "Rahatsız edici",
    "Something else": "Başka bir şey",
    "Cancel": "Vazgeç",
    "Send": "Gönder",
    "BitPulse is thinking…": "BitPulse düşünüyor…",
    "Ask BitPulse something…": "BitPulse'a bir şey sor…",
    "Send message": "Mesajı gönder",
    "Could not reach the AI service. Check your connection and try again.": (
        "Yapay zeka servisine ulaşılamadı. Bağlantını kontrol edip tekrar dene."
    ),
    "The AI service took too long to respond. Please try again.": (
        "Yapay zeka servisi çok geç cevap verdi. Lütfen tekrar dene."
    ),
    "The AI service is busy. Please try again in a minute.": (
        "Yapay zeka servisi şu an yoğun. Lütfen bir dakika sonra tekrar dene."
    ),
    "The AI service is temporarily unavailable. Please try again.": (
        "Yapay zeka servisi geçici olarak kullanılamıyor. Lütfen tekrar dene."
    ),
    "The AI service returned an empty response.": "Yapay zeka servisi boş bir cevap döndürdü.",
    "\n\n*(The connection dropped before the answer finished. Please ask again.)*": (
        "\n\n*(Cevap bitmeden bağlantı koptu. Lütfen tekrar sor.)*"
    ),
    # summaries
    "A summary is not available for this article.": "Bu haber için özet yok.",
    "Summaries are not available for this article.": "Bu haber için özet kullanılamıyor.",
    "Could not summarize this article.": "Bu haber özetlenemedi.",
    "Could not reach the AI service.": "Yapay zeka servisine ulaşılamadı.",
    # times
    "Latest": "Yeni",
    "{n}m ago": "{n} dk önce",
    "{n}h ago": "{n} sa önce",
    "{n}d ago": "{n} gün önce",
    # news list
    "All News": "Tüm Haberler",
    "Markets": "Piyasalar",
    "Trading": "Alım Satım",
    "Policy": "Düzenleme",
    "ETFs": "ETF'ler",
    "Loading latest news…": "Son haberler yükleniyor…",
    "Retry": "Tekrar dene",
    "No recent news found in this category.": "Bu kategoride yeni haber yok.",
    "You've reached the end of the latest news.": "Son haberlerin sonuna geldin.",
    "Total {count} articles scanned.": "Toplam {count} haber tarandı.",
    "Bitcoin Optech weekly newsletter": "Bitcoin Optech haftalık bülteni",
    "New newsletter #{number}": "Yeni bülten #{number}",
    "Optech newsletter #{number}": "Optech bülteni #{number}",
    "Refreshing news…": "Haberler yenileniyor…",
    "Updated just now · {count} articles": "Az önce güncellendi · {count} haber",
    "Could not refresh · showing saved news": "Yenilenemedi · kayıtlı haberler gösteriliyor",
    "No connection · tap Retry": "Bağlantı yok · Tekrar dene'ye dokun",
    "Showing saved news · refreshing…": "Kayıtlı haberler gösteriliyor · yenileniyor…",
    # article screen
    "No article summary is available.": "Haber özeti yok.",
    "the publisher": "yayıncı",
    "Loading full article...": "Haberin tamamı yükleniyor...",
    "AI summary": "AI özeti",
    "Written by AI from {publisher}'s article; it can contain mistakes.": (
        "Yapay zeka bu özeti {publisher} haberinden yazdı; hata içerebilir."
    ),
    "Ask about this article": "Bu haberi sor",
    "e.g. why does this matter?": "ör. bu neden önemli?",
    "Hide questions": "Soruları gizle",
    "Summarize with AI": "AI ile özetle",
    "Summarizing…": "Özetleniyor…",
    "Writing a short AI summary…": "Kısa bir AI özeti yazılıyor…",
    "Read the full article on {publisher}": "Haberin tamamını oku: {publisher}",
    "Back to news": "Haberlere dön",
    "From {publisher}:": "Yayıncının özeti ({publisher}):",
    "Source: {source}": "Kaynak: {source}",
    "Open original article": "Orijinal haberi aç",
    # newsletter
    "© Bitcoin Optech. Republished under the MIT license; the cards rearrange the original text.": (
        "© Bitcoin Optech. MIT lisansıyla yayımlanmıştır; kartlar orijinal metni yeniden düzenler."
    ),
    "news": "haber",
    "app updates": "uygulama güncellemesi",
    "releases": "sürüm",
    "code changes": "kod değişikliği",
    "items": "konu",
    "{when} · full text ~{minutes} min": "{when} · tam metin ~{minutes} dk",
    "Full text ~{minutes} min": "Tam metin ~{minutes} dk",
    "BITCOIN OPTECH · WEEKLY": "BITCOIN OPTECH · HAFTALIK",
    "Newsletter #{number}": "Bülten #{number}",
    "Writing a plain-language digest…": "Sade bir özet yazılıyor…",
    "This week in plain words": "Bu hafta, sade bir dille",
    "Written by AI from the newsletter; it can contain mistakes. Tap a card below for the original.": (
        "Yapay zeka bültenden yazdı; hata içerebilir. Orijinal metin için aşağıdaki kartlara dokun. "
        "Kartlar İngilizce."
    ),
    "Loading the newsletter…": "Bülten yükleniyor…",
    "Could not load the newsletter. Check your connection.": "Bülten yüklenemedi. Bağlantını kontrol et.",
    "e.g. what does this mean for my wallet?": "ör. bu cüzdanım için ne anlama geliyor?",
    "Ask about this issue": "Bu sayıyı sor",
    "Open on bitcoinops.org": "bitcoinops.org'da aç",
    "License": "Lisans",
    # market
    "Loading...": "Yükleniyor...",
    "Waiting for data...": "Veri bekleniyor...",
    "High: {price}": "En yüksek: {price}",
    "Low: {price}": "En düşük: {price}",
    "Live • {time}": "Canlı • {time}",
    "Unavailable": "Yok",
    "Saved data · updating…": "Kayıtlı veri · güncelleniyor…",
    "Updating...": "Güncelleniyor...",
    "Could not display chart data": "Grafik gösterilemedi",
    "Showing cached data · connection lost": "Kayıtlı veri gösteriliyor · bağlantı koptu",
    "Connection lost · tap Retry": "Bağlantı koptu · Tekrar dene'ye dokun",
    "~{days} Days": "~{days} gün",
    "Imminent": "Çok yakın",
    "Sentiment": "Duyarlılık",
    "Next Halving": "Sonraki Halving",
    "Estimated": "Tahmini",
    "Extreme Fear": "Aşırı Korku",
    "Fear": "Korku",
    "Neutral": "Nötr",
    "Greed": "Açgözlülük",
    "Extreme Greed": "Aşırı Açgözlülük",
    # period buttons: saat, gün, hafta, ay, yıl
    "1H": "1S",
    "1D": "1G",
    "1W": "1H",
    "1M": "1A",
    "1Y": "1Y",
    "5Y": "5Y",
}
