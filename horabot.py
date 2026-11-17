import os
import sys
import time
import unicodedata
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError("Token do Telegram não encontrado no arquivo .env")

URL = f"https://api.telegram.org/bot{TOKEN}/"

FUSOS = {
    "sao paulo": "America/Sao_Paulo",
    "brasilia": "America/Sao_Paulo",
    "rio de janeiro": "America/Sao_Paulo",
    "londres": "Europe/London",
    "paris": "Europe/Paris",
    "lisboa": "Europe/Lisbon",
    "toquio": "Asia/Tokyo",
    "pequim": "Asia/Shanghai",
    "nova york": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "dubai": "Asia/Dubai",
    "sydney": "Australia/Sydney"
}

NOMES_EXIBICAO = {
    "sao paulo": "São Paulo",
    "brasilia": "Brasília",
    "rio de janeiro": "Rio de Janeiro",
    "londres": "Londres",
    "paris": "Paris",
    "lisboa": "Lisboa",
    "toquio": "Tóquio",
    "pequim": "Pequim",
    "nova york": "Nova York",
    "los angeles": "Los Angeles",
    "dubai": "Dubai",
    "sydney": "Sydney"
}


def normalizar_texto(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(
        caractere for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )


def obter_horario(cidade):
    cidade_normalizada = normalizar_texto(cidade)
    fuso = FUSOS.get(cidade_normalizada)

    if not fuso:
        return None

    url = f"https://worldtime.timezone.io/api/timezone/{fuso}"

    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        dados = resposta.json()
        horario = datetime.fromisoformat(dados["datetime"])

        return {
            "cidade": cidade.strip().title(),
            "fuso": fuso,
            "horario": horario
        }

    except (
        requests.exceptions.RequestException,
        ValueError,
        KeyError
    ):
        return None


def consultar_horario(cidade):
    dados = obter_horario(cidade)

    if dados is None:
        return (
            "Não foi possível consultar essa cidade.\n"
            "Verifique o nome ou tente novamente."
        )

    horario = dados["horario"]

    return (
        f"🕒 Horário em {dados['cidade']}\n"
        f"📅 Data: {horario.strftime('%d/%m/%Y')}\n"
        f"⏰ Hora: {horario.strftime('%H:%M:%S')}\n"
        f"🌎 Fuso: {dados['fuso']}"
    )


def comparar_horarios(cidade_a, cidade_b):
    dados_a = obter_horario(cidade_a)
    dados_b = obter_horario(cidade_b)

    if dados_a is None or dados_b is None:
        return (
            "Não consegui consultar uma das cidades.\n"
            "Verifique os nomes e tente novamente."
        )

    horario_a = dados_a["horario"]
    horario_b = dados_b["horario"]

    diferenca = horario_b.utcoffset() - horario_a.utcoffset()
    minutos = int(diferenca.total_seconds() // 60)

    if minutos == 0:
        mensagem = "As duas cidades possuem o mesmo horário."

    else:
        horas = abs(minutos) // 60
        minutos_restantes = abs(minutos) % 60

        if minutos > 0:
            cidade_frente = dados_b["cidade"]
            outra_cidade = dados_a["cidade"]
        else:
            cidade_frente = dados_a["cidade"]
            outra_cidade = dados_b["cidade"]

        if horas > 0:
            unidade = "hora" if horas == 1 else "horas"
            tempo = f"{horas} {unidade}"

            if minutos_restantes > 0:
                tempo += f" e {minutos_restantes} minutos"
        else:
            unidade = "minuto" if minutos_restantes == 1 else "minutos"
            tempo = f"{minutos_restantes} {unidade}"

        mensagem = (
            f"{cidade_frente} está {tempo} à frente de "
            f"{outra_cidade}."
        )

    return (
        "🌎 COMPARAÇÃO DE FUSOS\n\n"
        f"📍 {dados_a['cidade']}: {horario_a.strftime('%H:%M:%S')}\n"
        f"📍 {dados_b['cidade']}: {horario_b.strftime('%H:%M:%S')}\n\n"
        f"⏰ Diferença: {mensagem}"
    )


def testar_conexao():
    try:
        resposta = requests.get(URL + "getMe", timeout=15)
        dados = resposta.json()

        if dados["ok"]:
            bot = dados["result"]

            print("Conexão realizada com sucesso!")
            print("-------------------------------")
            print("Nome do bot:", bot["first_name"])
            print("Usuário:", bot["username"])
            print("ID:", bot["id"])
        else:
            print("Erro na conexão:", dados)

    except requests.exceptions.RequestException as erro:
        print("Erro ao conectar com o Telegram:", erro)


def enviar_mensagem(chat_id, texto):
    try:
        resposta = requests.post(
            URL + "sendMessage",
            data={"chat_id": chat_id, "text": texto},
            timeout=15
        )
        resposta.raise_for_status()
        dados = resposta.json()

        if not dados.get("ok"):
            print("Erro ao enviar mensagem:", dados)

    except requests.exceptions.RequestException as erro:
        print("Erro ao enviar mensagem:", erro)


def processar_mensagem(texto):
    texto = texto.strip()

    if texto == "/start":
        return (
            "🕒 Olá! Bem-vindo ao HoraBot!\n\n"
            "Seu assistente de horários mundiais.\n\n"
            "Digite /ajuda para conhecer os comandos."
        )

    elif texto == "/ajuda":
        return (
            "🕒 COMANDOS DO HORABOT\n\n"
            "/start - Iniciar o bot\n"
            "/hora - Consultar horários\n"
            "/comparar - Comparar fusos\n"
            "/cidades - Ver cidades disponíveis\n"
            "/ajuda - Ver instruções\n\n"
            "Exemplo de consulta:\n"
            "/hora São Paulo\n\n"
            "Exemplo de comparação:\n"
            "/comparar São Paulo Londres"
        )

    elif texto == "/cidades":
        lista = sorted(
            set(NOMES_EXIBICAO.get(cidade, cidade.title()) for cidade in FUSOS)
        )

        return (
            "🌎 CIDADES DISPONÍVEIS NO HORABOT\n\n"
            + "\n".join(f"📍 {cidade}" for cidade in lista)
            + "\n\nPara consultar, digite:\n"
            "/hora nome da cidade\n\n"
            "Exemplo: /hora Paris"
        )

    elif texto == "/hora" or texto.startswith("/hora "):
        partes = texto.split(maxsplit=1)

        if len(partes) < 2:
            return (
                "🌎 Informe uma cidade para consultar o horário.\n\n"
                "Exemplo: /hora São Paulo\n"
                "Digite /cidades para ver as opções."
            )

        cidade = partes[1]
        return consultar_horario(cidade)

    elif texto == "/comparar" or texto.startswith("/comparar "):
        partes = texto.split(maxsplit=1)

        if len(partes) < 2:
            return (
                "🌎 Informe duas cidades para comparar.\n\n"
                "Exemplo:\n"
                "/comparar São Paulo Londres"
            )

        cidades = partes[1].split()

        for i in range(1, len(cidades)):
            cidade_a = " ".join(cidades[:i])
            cidade_b = " ".join(cidades[i:])

            if (
                normalizar_texto(cidade_a) in FUSOS
                and normalizar_texto(cidade_b) in FUSOS
            ):
                return comparar_horarios(cidade_a, cidade_b)

        return (
            "Não consegui identificar as duas cidades.\n\n"
            "Digite /cidades para consultar as opções disponíveis.\n"
            "Exemplo: /comparar São Paulo Londres"
        )

    else:
        return (
            "Não reconheci esse comando. "
            "Digite /ajuda para conhecer as opções."
        )


def iniciar_bot():
    offset = None

    print("🕒 HoraBot está funcionando!")
    print("Aguardando mensagens do Telegram...")

    while True:
        parametros = {
            "timeout": 30,
            "allowed_updates": ["message"]
        }

        if offset is not None:
            parametros["offset"] = offset

        try:
            resposta = requests.get(
                URL + "getUpdates",
                params=parametros,
                timeout=35
            )

            resposta.raise_for_status()
            dados = resposta.json()

            if not dados.get("ok"):
                print("Erro retornado pelo Telegram:", dados)
                time.sleep(3)
                continue

            for atualizacao in dados["result"]:
                offset = atualizacao["update_id"] + 1
                mensagem = atualizacao.get("message")

                if not mensagem:
                    continue

                texto = mensagem.get("text", "")
                chat_id = mensagem["chat"]["id"]

                if not texto:
                    continue

                print("Mensagem recebida:", texto)
                resposta_bot = processar_mensagem(texto)
                enviar_mensagem(chat_id, resposta_bot)

        except requests.exceptions.RequestException as erro:
            print("Erro de conexão:", erro)
            time.sleep(3)


if __name__ == "__main__":
    if "--testar" in sys.argv:
        testar_conexao()
    else:
        iniciar_bot()