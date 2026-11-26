"""Portuguese (Brazil, informal "você")."""

MONTHS = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")

STRINGS = {
    # main
    "News": "Notícias",
    "AI Assistant": "Assistente IA",
    "Market": "Mercado",
    "Refresh news": "Atualizar notícias",
    "Language": "Idioma",
    # AI tab and chat
    "BitPulse AI Assistant": "Assistente IA do BitPulse",
    "I'm BitPulse, a Bitcoin market assistant. I follow the live price, market sentiment "
    "and today's crypto headlines, and I can explain what's going on.": (
        "Sou o BitPulse, um assistente do mercado de Bitcoin. Acompanho o preço ao vivo, o "
        "sentimento do mercado e as manchetes cripto do dia, e posso explicar o que está acontecendo."
    ),
    "For education only, not financial advice. Answers are AI-generated and can be wrong; "
    "check important facts and do your own research before any decision.": (
        "Apenas para fins educacionais, não é recomendação financeira. As respostas são geradas por "
        "IA e podem estar erradas; confira os fatos importantes e faça sua própria pesquisa antes de "
        "qualquer decisão."
    ),
    "Privacy policy": "Política de privacidade",
    "AI is being prepared for the mobile release. Please try again soon.": (
        "A IA está sendo preparada para a versão móvel. Tente novamente em breve."
    ),
    "Report": "Denunciar",
    "Report this answer as wrong, harmful or offensive": "Denunciar esta resposta como errada, nociva ou ofensiva",
    "Reported. Thank you.": "Denunciado. Obrigado.",
    "Could not send report. Try again.": "Não foi possível enviar a denúncia. Tente novamente.",
    "BitPulse is thinking…": "O BitPulse está pensando…",
    "Ask BitPulse something…": "Pergunte algo ao BitPulse…",
    "Send message": "Enviar mensagem",
    "Could not reach the AI service. Check your connection and try again.": (
        "Não foi possível acessar o serviço de IA. Verifique sua conexão e tente novamente."
    ),
    "The AI service took too long to respond. Please try again.": (
        "O serviço de IA demorou demais para responder. Tente novamente."
    ),
    "The AI service is busy. Please try again in a minute.": (
        "O serviço de IA está ocupado. Tente novamente em um minuto."
    ),
    "The AI service is temporarily unavailable. Please try again.": (
        "O serviço de IA está indisponível no momento. Tente novamente."
    ),
    "The AI service returned an empty response.": "O serviço de IA retornou uma resposta vazia.",
    "\n\n*(The connection dropped before the answer finished. Please ask again.)*": (
        "\n\n*(A conexão caiu antes de a resposta terminar. Pergunte novamente.)*"
    ),
    # summaries
    "A summary is not available for this article.": "Não há resumo disponível para esta notícia.",
    "Summaries are not available for this article.": "Os resumos não estão disponíveis para esta notícia.",
    "Could not summarize this article.": "Não foi possível resumir esta notícia.",
    "Could not reach the AI service.": "Não foi possível acessar o serviço de IA.",
    # times
    "Latest": "Recente",
    "{n}m ago": "há {n} min",
    "{n}h ago": "há {n} h",
    "{n}d ago": "há {n} d",
    # news list
    "All News": "Todas",
    "Markets": "Mercados",
    "Trading": "Trading",
    "Policy": "Regulação",
    "ETFs": "ETFs",
    "Loading latest news…": "Carregando as últimas notícias…",
    "Retry": "Tentar de novo",
    "No recent news found in this category.": "Nenhuma notícia recente nesta categoria.",
    "You've reached the end of the latest news.": "Você chegou ao fim das últimas notícias.",
    "Total {count} articles scanned.": "{count} notícias verificadas no total.",
    "Bitcoin Optech weekly newsletter": "Boletim semanal do Bitcoin Optech",
    "New newsletter #{number}": "Novo boletim #{number}",
    "Optech newsletter #{number}": "Boletim Optech #{number}",
    "Refreshing news…": "Atualizando notícias…",
    "Updated just now · {count} articles": "Atualizado agora · {count} notícias",
    "Could not refresh · showing saved news": "Não foi possível atualizar · mostrando notícias salvas",
    "No connection · tap Retry": "Sem conexão · toque em Tentar de novo",
    "Showing saved news · refreshing…": "Mostrando notícias salvas · atualizando…",
    # article screen
    "No article summary is available.": "Não há resumo da notícia.",
    "the publisher": "o veículo",
    "Loading full article...": "Carregando a notícia completa...",
    "AI summary": "Resumo IA",
    "Written by AI from {publisher}'s article; it can contain mistakes.": (
        "Escrito por IA a partir da notícia de {publisher}; pode conter erros."
    ),
    "Ask about this article": "Perguntar sobre esta notícia",
    "e.g. why does this matter?": "ex.: por que isso importa?",
    "Hide questions": "Ocultar perguntas",
    "Summarize with AI": "Resumir com IA",
    "Summarizing…": "Resumindo…",
    "Writing a short AI summary…": "Escrevendo um breve resumo com IA…",
    "Read the full article on {publisher}": "Ler a notícia completa em {publisher}",
    "Back to news": "Voltar às notícias",
    "From {publisher}:": "Segundo {publisher}:",
    "Source: {source}": "Fonte: {source}",
    "Open original article": "Abrir a notícia original",
    # newsletter
    "© Bitcoin Optech. Republished under the MIT license; the cards rearrange the original text.": (
        "© Bitcoin Optech. Republicado sob a licença MIT; os cartões reorganizam o texto original."
    ),
    "news": "notícias",
    "news|one": "notícia",
    "app updates": "atualizações de apps",
    "app updates|one": "atualização de app",
    "releases": "lançamentos",
    "releases|one": "lançamento",
    "code changes": "mudanças de código",
    "code changes|one": "mudança de código",
    "items": "temas",
    "items|one": "tema",
    "{when} · full text ~{minutes} min": "{when} · texto completo ~{minutes} min",
    "Full text ~{minutes} min": "Texto completo ~{minutes} min",
    "BITCOIN OPTECH · WEEKLY": "BITCOIN OPTECH · SEMANAL",
    "Newsletter #{number}": "Boletim #{number}",
    "Writing a plain-language digest…": "Escrevendo um resumo simples…",
    "This week in plain words": "Esta semana, em palavras simples",
    "Written by AI from the newsletter; it can contain mistakes. Tap a card below for the original.": (
        "Escrito por IA a partir do boletim; pode conter erros. Toque em um cartão abaixo para ver o "
        "original. Os cartões estão em inglês."
    ),
    "Loading the newsletter…": "Carregando o boletim…",
    "Could not load the newsletter. Check your connection.": "Não foi possível carregar o boletim. Verifique sua conexão.",
    "e.g. what does this mean for my wallet?": "ex.: o que isso significa para a minha carteira?",
    "Ask about this issue": "Perguntar sobre esta edição",
    "Open on bitcoinops.org": "Abrir em bitcoinops.org",
    "License": "Licença",
    # market
    "Loading...": "Carregando...",
    "Waiting for data...": "Aguardando dados...",
    "High: {price}": "Máx.: {price}",
    "Low: {price}": "Mín.: {price}",
    "Live • {time}": "Ao vivo • {time}",
    "Unavailable": "Indisponível",
    "Saved data · updating…": "Dados salvos · atualizando…",
    "Updating...": "Atualizando...",
    "Could not display chart data": "Não foi possível exibir o gráfico",
    "Showing cached data · connection lost": "Mostrando dados salvos · sem conexão",
    "Connection lost · tap Retry": "Sem conexão · toque em Tentar de novo",
    "~{days} Days": "~{days} dias",
    "Imminent": "Iminente",
    "Sentiment": "Sentimento",
    "Next Halving": "Próximo halving",
    "Estimated": "Estimado",
    "Extreme Fear": "Medo extremo",
    "Fear": "Medo",
    "Neutral": "Neutro",
    "Greed": "Ganância",
    "Extreme Greed": "Ganância extrema",
    # period buttons: hora, dia, semana, mês, ano
    "1H": "1H",
    "1D": "1D",
    "1W": "1S",
    "1M": "1M",
    "1Y": "1A",
    "5Y": "5A",
}
