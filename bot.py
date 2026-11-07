# bot.py - il bot della mensa fa due lavori, in due momenti:
#
#   python bot.py menu     -> legge il menu di oggi dal sito e lo salva in docs/menu.json
#   python bot.py avvisa   -> ti manda su Telegram il link alla pagina per prenotare
#   python bot.py settimana -> il lunedì manda su Telegram la tabella del menu della settimana
#
# Usa:
#   - menu.py       -> per leggere il menu dal sito
#   - segreti.env   -> per il token del bot e i numeri delle chat (solo sul tuo PC)

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

import menu
import tabella

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


def manda_messaggio(testo, html=False):
    """Manda il messaggio a tutte le chat Telegram della lista.

    TELEGRAM_CHAT_ID può contenere più numeri separati da virgola,
    es. "111111111,222222222" (tu e un amico). Ognuno deve prima
    aver premuto "Avvia" sul bot, altrimenti Telegram non lo fa scrivere.

    Può contenere anche un canale Telegram: "@nomecanale" se è pubblico,
    oppure il suo numero (inizia con -100) se è privato. Il bot deve essere
    amministratore del canale. Vedi OBIETTIVI.md, "Passare a un canale".
    """
    contenuto = {"text": testo}
    if html:
        contenuto["parse_mode"] = "HTML"   # così Telegram capisce il <b>grassetto</b>
    _manda_a_tutti("sendMessage", contenuto)


def manda_foto(png, didascalia):
    """Manda un'immagine (es. la tabella della settimana) a tutte le chat della lista."""
    _manda_a_tutti("sendPhoto", {"caption": didascalia}, file={"photo": ("menu.png", png, "image/png")})


def _manda_a_tutti(metodo, contenuto, file=None):
    """Chiama Telegram una volta per ogni chat del segreto TELEGRAM_CHAT_ID."""
    segreti = leggi_segreti()
    indirizzo = f"https://api.telegram.org/bot{segreti['TELEGRAM_TOKEN']}/{metodo}"
    chat = [c.strip() for c in segreti["TELEGRAM_CHAT_ID"].split(",") if c.strip()]

    sbagliate = []
    for chat_id in chat:
        # Se una chat non va (es. qualcuno ha bloccato il bot), gli altri lo ricevono lo stesso
        try:
            if file:   # con un'immagine Telegram vuole i dati "a pezzi", non in JSON
                risposta = requests.post(indirizzo, data={"chat_id": chat_id, **contenuto},
                                         files=file, timeout=60)
            else:
                risposta = requests.post(indirizzo, json={"chat_id": chat_id, **contenuto}, timeout=30)
            risposta.raise_for_status()
        except Exception as errore:
            print(f"Non sono riuscito a scrivere alla chat {chat_id}: {errore}")
            sbagliate.append(chat_id)
    if sbagliate:
        raise RuntimeError(f"Messaggio non arrivato a: {', '.join(sbagliate)}")


def testo_completo(dati):
    """Il menu completo della mensa con i piatti d'asporto in evidenza.

    Restituisce None se il sito del menu completo non risponde o non ha il giorno:
    in quel caso il bot manda il messaggio di prima, con il solo asporto.
    """
    giorno = date.fromisoformat(dati["data"])
    try:
        completo = menu.estrai_completo(menu.scarica_completo(), giorno)
    except Exception as errore:
        print(f"Menu completo non disponibile: {errore}")
        return None
    if not completo:
        print("Sul sito del menu completo oggi non c'è niente.")
        return None
    asporto = {p: dati.get(p) or {} for p in ("pranzo", "cena")}
    menu.segna_asporto(completo, asporto)
    testo = menu.scrivi_menu_evidenziato(completo, giorno)
    if dati.get("errore"):
        testo += "\n\n⚠️ Oggi non sono riuscito a leggere il menu d'asporto: nessun piatto è in evidenza."
    return testo + f"\n\n👉 Prenota l'asporto qui:\n{PAGINA}"


def avvisa():
    """Manda su Telegram il menu completo (asporto in evidenza) e il link alla pagina."""
    try:
        dati = json.loads(FILE_MENU.read_text(encoding="utf-8"))
    except Exception:
        dati = {"errore": "file del menu mancante"}

    # Prima prova con il menu completo; se non va, si passa al messaggio di prima
    testo = testo_completo(dati) if dati.get("data") else None
    if testo:
        manda_messaggio(testo, html=True)
        print("Menu completo inviato su Telegram ✅")
        return

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


def tabella_settimana(oggi):
    """La tabella del menu completo della settimana (da lunedì a domenica), come immagine PNG.

    Solo il menu della mensa: l'asporto qui non è segnato.
    Restituisce (immagine, didascalia).
    """
    lunedi = oggi - timedelta(days=oggi.weekday())
    giorni = [lunedi + timedelta(days=n) for n in range(7)]

    html = menu.scarica_completo()
    settimana = [(g, menu.estrai_completo(html, g)) for g in giorni]
    if not any(m for _, m in settimana):
        raise RuntimeError("sul sito non c'è il menu di questa settimana")

    titolo = (f"Menu mensa Chieti - dal {giorno_in_parole(giorni[0])} "
              f"a {giorno_in_parole(giorni[-1])}")
    didascalia = f"🗓️ {titolo}\n(tocca l'immagine per ingrandirla)"
    return tabella.disegna_settimana(settimana, titolo), didascalia


def settimana():
    """Manda su Telegram la tabella con il menu completo di tutta la settimana."""
    try:
        png, didascalia = tabella_settimana(date.today())
    except Exception as errore:
        manda_messaggio(f"⚠️ Oggi non sono riuscito a leggere il menu della settimana.\n"
                        f"Errore: {errore}")
        raise
    manda_foto(png, didascalia)
    print("Tabella della settimana inviata su Telegram ✅")


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else ""
    if comando == "menu":
        salva_menu()
    elif comando == "avvisa":
        avvisa()
    elif comando == "settimana":
        settimana()
    else:
        print("Uso: python bot.py menu   oppure   python bot.py avvisa   oppure   python bot.py settimana")
