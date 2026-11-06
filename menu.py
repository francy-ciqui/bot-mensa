# menu.py - legge il menu di oggi dalla pagina pubblica della mensa di Chieti
#
# Cosa fa, in parole semplici:
#   1. scarica la pagina https://cimas-meal.it/chieti (una sola volta)
#   2. cerca il giorno di oggi
#   3. tira fuori i piatti di pranzo e cena e li scrive sullo schermo

import re
from datetime import date

import requests
from bs4 import BeautifulSoup

INDIRIZZO_MENU = "https://cimas-meal.it/chieti"

# Ci presentiamo in modo onesto: un programma personale, una richiesta al giorno
INTESTAZIONI = {"User-Agent": "BotMensaPersonale/1.0 (uso personale, 1 richiesta al giorno)"}

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def scarica_pagina():
    """Scarica la pagina del menu, come farebbe il browser."""
    risposta = requests.get(INDIRIZZO_MENU, headers=INTESTAZIONI, timeout=30)
    risposta.raise_for_status()  # se il sito risponde con un errore, ci fermiamo
    return risposta.text


def pulisci_piatto(testo):
    """Separa il nome del piatto dai numeri degli allergeni e segna i piatti vegetariani.

    Esempio: 'Pasta al pomodoro Allergeni: 1-6-10 | Vegetariano'
          -> {"nome": "Pasta al pomodoro 🌱", "allergeni": [1, 6, 10]}
    """
    testo = " ".join(testo.split())                      # spazi doppi -> uno solo
    vegetariano = "Vegetariano" in testo
    testo = testo.replace("Vegetariano", "").replace("Allergeni:", "").replace("|", "")
    allergeni = []
    for codici in re.findall(r"\s(\d+(?:-\d+)*)\b", testo):  # es. "1-6-10"
        allergeni += [int(n) for n in codici.split("-")]
    testo = re.sub(r"\s\d+(-\d+)*\b", "", testo)         # via i numeri dal nome
    testo = " ".join(testo.split())
    if vegetariano:
        testo = re.sub(r"\sV$", "", testo)               # a volte c'è una "V" in più
        testo += " 🌱"
    return {"nome": testo, "allergeni": sorted(set(allergeni))}


def estrai_menu(html, giorno):
    """Restituisce il menu del giorno scelto, diviso per pranzo e cena.

    Esempio di risultato:
      {"pranzo": {"Primi": [...], "Secondi": [...], "Contorni": [...]}, "cena": {...}}
    """
    pagina = BeautifulSoup(html, "html.parser")
    data_cercata = f"{giorno.day} {MESI[giorno.month - 1]} {giorno.year}"  # es. "4 novembre 2026"
    risultato = {}

    # Sulla pagina ogni giorno ha un titolo (es. "MERCOLEDÌ 4 Novembre 2026")
    for titolo in pagina.select("div.title-menu"):
        data_titolo = " ".join(titolo.get_text(" ").split()).lower()
        if data_cercata not in data_titolo:
            continue

        # Subito dopo il titolo ci sono i piatti e il pulsante PRENOTA
        contenuto = titolo.find_next_sibling("div", class_="content-menu")
        pulsante = titolo.find_next("a", class_="button-menu")
        if contenuto is None:
            continue

        # Il link del pulsante ci dice se è pranzo o cena (es. ".../menu-lunedi-pranzo")
        link = pulsante.get("href", "") if pulsante else ""
        servizio = "cena" if "cena" in link else "pranzo"

        portate = {}
        for intestazione in contenuto.find_all("h5"):     # "Primi", "Secondi", "Contorni"
            lista = intestazione.find_next_sibling("ul")
            if lista:
                piatti = [pulisci_piatto(voce.get_text(" ")) for voce in lista.find_all("li")]
                portate[intestazione.get_text(strip=True)] = [p for p in piatti if p["nome"]]
        risultato[servizio] = portate

    return risultato


def scrivi_menu(menu, giorno):
    """Trasforma il menu in un testo leggibile."""
    if not menu:
        return f"Nessun menu trovato per il {giorno.strftime('%d/%m/%Y')} 🤷"

    righe = [f"🍽️ Menu mensa Chieti - {giorno.strftime('%d/%m/%Y')}"]
    for servizio in ["pranzo", "cena"]:
        if servizio not in menu:
            continue
        righe.append("")
        righe.append("☀️ PRANZO" if servizio == "pranzo" else "🌙 CENA")
        for portata, piatti in menu[servizio].items():
            righe.append(f"{portata}:")
            for piatto in piatti:
                # (accetta anche il vecchio formato, dove il piatto era solo testo)
                nome = piatto["nome"] if isinstance(piatto, dict) else piatto
                righe.append(f"  • {nome}")
    return "\n".join(righe)


if __name__ == "__main__":
    oggi = date.today()
    html = scarica_pagina()
    print(scrivi_menu(estrai_menu(html, oggi), oggi))
