# bot.py - il bot della mensa fa due lavori, in due momenti:
#
#   python bot.py menu     -> legge il menu di oggi dal sito e lo salva in docs/menu.json
#   python bot.py avvisa   -> ti manda su Telegram il link alla pagina per prenotare
#
# Usa:
#   - menu.py       -> per leggere il menu dal sito
#   - segreti.env   -> per il token del bot e il numero della tua chat (solo sul tuo PC)

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

import requests

import menu

CARTELLA = Path(__file__).parent
FILE_MENU = CARTELLA / "docs" / "menu.json"

# L'indirizzo della pagina su GitHub Pages
PAGINA = os.environ.get("PAGINA_URL", "https://francy-ciqui.github.io/bot-mensa/")

GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]


def giorno_in_parole(giorno):
    """Es. date(2026, 11, 5) -> 'giovedì 5 novembre'."""
    return f"{GIORNI[giorno.weekday()]} {giorno.day} {menu.MESI[giorno.month - 1]}"


def salva_menu():
    """Scarica il menu di oggi e lo scrive in docs/menu.json per la pagina web."""
    oggi = date.today()
    dati = {
        "data": oggi.isoformat(),                 # es. "2026-11-05"
        "giorno": giorno_in_parole(oggi),         # es. "giovedì 5 novembre"
        "aggiornato": datetime.now().strftime("%H:%M"),
        "errore": None,
        "pranzo": {},
        "cena": {},
    }
    try:
        trovato = menu.estrai_menu(menu.scarica_pagina(), oggi)
        dati["pranzo"] = trovato.get("pranzo", {})
        dati["cena"] = trovato.get("cena", {})
    except Exception as errore:
        # Se il sito non risponde, la pagina lo dirà invece di restare vuota
        dati["errore"] = str(errore)

    FILE_MENU.parent.mkdir(exist_ok=True)
    FILE_MENU.write_text(json.dumps(dati, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Menu salvato in {FILE_MENU} ✅")


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


def avvisa():
    """Manda su Telegram il promemoria con il link alla pagina."""
    try:
        dati = json.loads(FILE_MENU.read_text(encoding="utf-8"))
    except Exception:
        dati = {"errore": "file del menu mancante"}

    if dati.get("errore"):
        testo = (f"⚠️ Oggi non sono riuscito a leggere il menu.\n"
                 f"Errore: {dati['errore']}\n\nLa pagina: {PAGINA}")
    elif not dati.get("pranzo") and not dati.get("cena"):
        testo = f"🤷 Oggi ({dati['giorno']}) sul sito non c'è nessun menu.\n\nLa pagina: {PAGINA}"
    else:
        # Prima il menu completo, poi il link alla pagina per prenotare
        giorno = date.fromisoformat(dati["data"])
        pasti = {p: dati[p] for p in ("pranzo", "cena") if dati.get(p)}
        testo = (menu.scrivi_menu(pasti, giorno)
                 + f"\n\n👉 Prenota qui:\n{PAGINA}")
    manda_messaggio(testo)
    print("Promemoria inviato su Telegram ✅")


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else ""
    if comando == "menu":
        salva_menu()
    elif comando == "avvisa":
        avvisa()
    else:
        print("Uso: python bot.py menu   oppure   python bot.py avvisa")
