# bot.py - prende il menu di oggi e te lo manda su Telegram
#
# Usa:
#   - menu.py       -> per leggere il menu dal sito
#   - segreti.env   -> per il token del bot e il numero della tua chat

import os
from datetime import date
from pathlib import Path

import requests

import menu

CARTELLA = Path(__file__).parent


def leggi_segreti():
    """Trova token e numero della chat.

    - Su GitHub li prende dalla "cassaforte" (i Secrets, passati come variabili d'ambiente).
    - Sul tuo PC li legge da segreti.env.
    """
    if os.environ.get("TELEGRAM_TOKEN"):
        return {
            "TELEGRAM_TOKEN": os.environ["TELEGRAM_TOKEN"],
            "TELEGRAM_CHAT_ID": os.environ["TELEGRAM_CHAT_ID"],
        }

    segreti = {}
    for riga in (CARTELLA / "segreti.env").read_text(encoding="utf-8-sig").splitlines():
        if "=" in riga and not riga.strip().startswith("#"):
            nome, valore = riga.split("=", 1)
            segreti[nome.strip()] = valore.strip()
    return segreti


def manda_messaggio(testo):
    """Manda un messaggio alla tua chat Telegram tramite il bot."""
    segreti = leggi_segreti()
    indirizzo = f"https://api.telegram.org/bot{segreti['TELEGRAM_TOKEN']}/sendMessage"
    risposta = requests.post(
        indirizzo,
        json={"chat_id": segreti["TELEGRAM_CHAT_ID"], "text": testo},
        timeout=30,
    )
    risposta.raise_for_status()


if __name__ == "__main__":
    oggi = date.today()
    try:
        html = menu.scarica_pagina()
        testo = menu.scrivi_menu(menu.estrai_menu(html, oggi), oggi)
    except Exception as errore:
        # Se il sito non risponde, te lo diciamo invece di restare in silenzio
        testo = f"⚠️ Non sono riuscito a leggere il menu di oggi.\nErrore: {errore}"
    manda_messaggio(testo)
    print("Messaggio inviato su Telegram ✅")
