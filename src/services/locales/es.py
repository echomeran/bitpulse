"""Spanish (neutral, informal "tú")."""

MONTHS = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic")

STRINGS = {
    # main
    "News": "Noticias",
    "AI Assistant": "Asistente IA",
    "Market": "Mercado",
    "Refresh news": "Actualizar noticias",
    "Language": "Idioma",
    # AI tab and chat
    "BitPulse AI Assistant": "Asistente IA de BitPulse",
    "I'm BitPulse, a Bitcoin market assistant. I follow the live price, market sentiment "
    "and today's crypto headlines, and I can explain what's going on.": (
        "Soy BitPulse, un asistente del mercado de Bitcoin. Sigo el precio en vivo, el sentimiento "
        "del mercado y los titulares cripto del día, y puedo explicarte qué está pasando."
    ),
    "For education only, not financial advice. Answers are AI-generated and can be wrong; "
    "check important facts and do your own research before any decision.": (
        "Solo con fines educativos, no es asesoramiento financiero. Las respuestas las genera una IA "
        "y pueden ser incorrectas; comprueba los datos importantes e investiga por tu cuenta antes "
        "de tomar cualquier decisión."
    ),
    "Privacy policy": "Política de privacidad",
    "AI is being prepared for the mobile release. Please try again soon.": (
        "La IA se está preparando para la versión móvil. Vuelve a intentarlo pronto."
    ),
    "Report": "Reportar",
    "Report this answer as wrong, harmful or offensive": "Reportar esta respuesta como incorrecta, dañina u ofensiva",
    "Reported. Thank you.": "Reportado. Gracias.",
    "Could not send report. Try again.": "No se pudo enviar el reporte. Inténtalo de nuevo.",
    "BitPulse is thinking…": "BitPulse está pensando…",
    "Ask BitPulse something…": "Pregúntale algo a BitPulse…",
    "Send message": "Enviar mensaje",
    "Could not reach the AI service. Check your connection and try again.": (
        "No se pudo conectar con el servicio de IA. Revisa tu conexión e inténtalo de nuevo."
    ),
    "The AI service took too long to respond. Please try again.": (
        "El servicio de IA tardó demasiado en responder. Inténtalo de nuevo."
    ),
    "The AI service is busy. Please try again in a minute.": (
        "El servicio de IA está ocupado. Inténtalo de nuevo en un minuto."
    ),
    "The AI service is temporarily unavailable. Please try again.": (
        "El servicio de IA no está disponible por ahora. Inténtalo de nuevo."
    ),
    "The AI service returned an empty response.": "El servicio de IA devolvió una respuesta vacía.",
    "\n\n*(The connection dropped before the answer finished. Please ask again.)*": (
        "\n\n*(La conexión se cortó antes de terminar la respuesta. Vuelve a preguntar.)*"
    ),
    # summaries
    "A summary is not available for this article.": "No hay resumen disponible para esta noticia.",
    "Summaries are not available for this article.": "Los resúmenes no están disponibles para esta noticia.",
    "Could not summarize this article.": "No se pudo resumir esta noticia.",
    "Could not reach the AI service.": "No se pudo conectar con el servicio de IA.",
    # times
    "Latest": "Reciente",
    "{n}m ago": "hace {n} min",
    "{n}h ago": "hace {n} h",
    "{n}d ago": "hace {n} d",
    # news list
    "All News": "Todas",
    "Markets": "Mercados",
    "Trading": "Trading",
    "Policy": "Regulación",
    "ETFs": "ETF",
    "Loading latest news…": "Cargando las últimas noticias…",
    "Retry": "Reintentar",
    "No recent news found in this category.": "No hay noticias recientes en esta categoría.",
    "You've reached the end of the latest news.": "Llegaste al final de las últimas noticias.",
    "Total {count} articles scanned.": "{count} noticias revisadas en total.",
    "Bitcoin Optech weekly newsletter": "Boletín semanal de Bitcoin Optech",
    "New newsletter #{number}": "Nuevo boletín #{number}",
    "Optech newsletter #{number}": "Boletín Optech #{number}",
    "Refreshing news…": "Actualizando noticias…",
    "Updated just now · {count} articles": "Actualizado ahora · {count} noticias",
    "Could not refresh · showing saved news": "No se pudo actualizar · mostrando noticias guardadas",
    "No connection · tap Retry": "Sin conexión · toca Reintentar",
    "Showing saved news · refreshing…": "Mostrando noticias guardadas · actualizando…",
    # article screen
    "No article summary is available.": "No hay resumen de la noticia.",
    "the publisher": "el medio",
    "Loading full article...": "Cargando la noticia completa...",
    "AI summary": "Resumen IA",
    "Written by AI from {publisher}'s article; it can contain mistakes.": (
        "Escrito por IA a partir de la noticia de {publisher}; puede contener errores."
    ),
    "Ask about this article": "Preguntar sobre esta noticia",
    "e.g. why does this matter?": "p. ej., ¿por qué es importante?",
    "Hide questions": "Ocultar preguntas",
    "Summarize with AI": "Resumir con IA",
    "Summarizing…": "Resumiendo…",
    "Writing a short AI summary…": "Escribiendo un breve resumen con IA…",
    "Read the full article on {publisher}": "Leer la noticia completa en {publisher}",
    "Back to news": "Volver a noticias",
    "From {publisher}:": "Según {publisher}:",
    "Source: {source}": "Fuente: {source}",
    "Open original article": "Abrir la noticia original",
    # newsletter
    "© Bitcoin Optech. Republished under the MIT license; the cards rearrange the original text.": (
        "© Bitcoin Optech. Republicado bajo la licencia MIT; las tarjetas reorganizan el texto original."
    ),
    "news": "noticias",
    "news|one": "noticia",
    "app updates": "actualizaciones de apps",
    "app updates|one": "actualización de app",
    "releases": "lanzamientos",
    "releases|one": "lanzamiento",
    "code changes": "cambios de código",
    "code changes|one": "cambio de código",
    "items": "temas",
    "items|one": "tema",
    "{when} · full text ~{minutes} min": "{when} · texto completo ~{minutes} min",
    "Full text ~{minutes} min": "Texto completo ~{minutes} min",
    "BITCOIN OPTECH · WEEKLY": "BITCOIN OPTECH · SEMANAL",
    "Newsletter #{number}": "Boletín #{number}",
    "Writing a plain-language digest…": "Escribiendo un resumen sencillo…",
    "This week in plain words": "Esta semana, en palabras sencillas",
    "Written by AI from the newsletter; it can contain mistakes. Tap a card below for the original.": (
        "Escrito por IA a partir del boletín; puede contener errores. Toca una tarjeta para ver el "
        "original. Las tarjetas están en inglés."
    ),
    "Loading the newsletter…": "Cargando el boletín…",
    "Could not load the newsletter. Check your connection.": "No se pudo cargar el boletín. Revisa tu conexión.",
    "e.g. what does this mean for my wallet?": "p. ej., ¿qué significa esto para mi billetera?",
    "Ask about this issue": "Preguntar sobre este número",
    "Open on bitcoinops.org": "Abrir en bitcoinops.org",
    "License": "Licencia",
    # market
    "Loading...": "Cargando...",
    "Waiting for data...": "Esperando datos...",
    "High: {price}": "Máx.: {price}",
    "Low: {price}": "Mín.: {price}",
    "Live • {time}": "En vivo • {time}",
    "Unavailable": "No disponible",
    "Saved data · updating…": "Datos guardados · actualizando…",
    "Updating...": "Actualizando...",
    "Could not display chart data": "No se pudo mostrar el gráfico",
    "Showing cached data · connection lost": "Mostrando datos guardados · sin conexión",
    "Connection lost · tap Retry": "Sin conexión · toca Reintentar",
    "~{days} Days": "~{days} días",
    "Imminent": "Inminente",
    "Sentiment": "Sentimiento",
    "Next Halving": "Próximo halving",
    "Estimated": "Estimado",
    "Extreme Fear": "Miedo extremo",
    "Fear": "Miedo",
    "Neutral": "Neutral",
    "Greed": "Codicia",
    "Extreme Greed": "Codicia extrema",
    # period buttons: hora, día, semana, mes, año
    "1H": "1H",
    "1D": "1D",
    "1W": "1S",
    "1M": "1M",
    "1Y": "1A",
    "5Y": "5A",
}
