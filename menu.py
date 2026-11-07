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
    # Legenda della mensa: "V" = piatto vegano, "*" = può contenere prodotti surgelati
    if re.search(r"\sV$", testo):
        vegetariano = True
        testo = re.sub(r"\sV$", "", testo)
    surgelato = "*" in testo
    testo = testo.replace("*", "").strip()
    if vegetariano:
        testo += " 🌱"
    if surgelato:
        testo += " ❄️"
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


# Il menu COMPLETO della mensa (in sala), su un altro sito. Serve solo al messaggio Telegram:
# la pagina web continua a usare il menu d'asporto qui sopra.
INDIRIZZO_COMPLETO = "https://www.cimasristorazione.com/menu-mense/universita-chieti/"


def scarica_completo():
    """Scarica la pagina con il menu completo della settimana."""
    risposta = requests.get(INDIRIZZO_COMPLETO, headers=INTESTAZIONI, timeout=30)
    risposta.raise_for_status()
    return risposta.text


def estrai_completo(html, giorno):
    """Come estrai_menu, ma dal sito del menu completo.

    Sulla pagina ogni giorno è un riquadro con la data (es. "07 Novembre 2026")
    e due linguette, "pranzo-N" e "cena-N", con Primi, Secondi e Contorni.
    """
    pagina = BeautifulSoup(html, "html.parser")
    data_cercata = f"{giorno.day:02d} {MESI[giorno.month - 1]} {giorno.year}"  # es. "07 novembre 2026"
    risultato = {}
    for riquadro in pagina.select("div.day-menu"):
        data = riquadro.select_one("span.date")
        if not data or " ".join(data.get_text().split()).lower() != data_cercata:
            continue
        for linguetta in riquadro.select("div.tab-pane"):
            servizio = "cena" if linguetta.get("id", "").startswith("cena") else "pranzo"
            portate = {}
            for intestazione in linguetta.find_all("h5"):
                lista = intestazione.find_next_sibling("ul")
                if not lista:
                    continue
                piatti = []
                for voce in lista.find_all("li"):
                    # Una "R" da sola accanto al piatto è una sigla del sito: la togliamo
                    testo = re.sub(r"\sR(?=\s|$)", " ", " " + voce.get_text(" ")).strip()
                    piatto = pulisci_piatto(testo)
                    if piatto["nome"]:
                        piatti.append(piatto)
                portate[intestazione.get_text(strip=True)] = piatti
            risultato[servizio] = portate
    return risultato


def _parole(nome):
    """Le parole di un piatto, per confrontare due siti che lo scrivono in modo un po' diverso.

    Es. "Pasta / Pasta integrale in bianco o al pomodoro" e
        "Pasta integrale/ Pasta in bianco o al pomodoro" danno le stesse parole.
    Lettere da sole ("e", "o", la sigla "R") non contano, e di ogni parola si guarda
    solo l'inizio: così "Sovracosce di pollo" e "Sovracoscia di pollo" sono lo stesso piatto.
    """
    parole = re.findall(r"[a-zàèéìòù]+", nome.lower())
    return frozenset(p[:5] for p in parole if len(p) > 1)


def segna_asporto(completo, asporto):
    """Segna con "asporto": True i piatti del menu completo che ci sono anche d'asporto.

    Se un piatto d'asporto non si trova nel menu completo, lo aggiunge in fondo
    alla sua portata, così nel messaggio non si perde niente.
    """
    for servizio, portate in asporto.items():
        completo.setdefault(servizio, {})
        for portata, piatti in portate.items():
            lista = completo[servizio].setdefault(portata, [])
            for piatto in piatti:
                uguale = next((p for p in lista if _parole(p["nome"]) == _parole(piatto["nome"])), None)
                if uguale:
                    uguale["asporto"] = True
                else:
                    nome = re.sub(r"\sR(?=\s|$)", "", piatto["nome"])   # via la sigla "R"
                    lista.append({**piatto, "nome": nome, "asporto": True})
    return completo


LEGENDA = "<b>in grassetto</b> 🥡 = anche d'asporto"


def scrivi_menu_evidenziato(menu, giorno):
    """Il menu completo per Telegram (formato HTML), con i piatti d'asporto in evidenza."""
    righe = [f"🍽️ <b>Menu mensa Chieti - {giorno.strftime('%d/%m/%Y')}</b>", LEGENDA]
    return "\n".join(righe) + "\n" + scrivi_pasti(menu)


def scrivi_pasti(menu):
    """Pranzo e cena di un giorno, piatto per piatto (formato HTML per Telegram)."""
    from html import escape

    righe = []
    for servizio in ["pranzo", "cena"]:
        if not menu.get(servizio):
            continue
        righe.append("")
        righe.append("☀️ <b>PRANZO</b>" if servizio == "pranzo" else "🌙 <b>CENA</b>")
        for portata, piatti in menu[servizio].items():
            # quote=False: Telegram non capisce &#x27; e mostrerebbe il codice al posto dell'apostrofo
            righe.append(f"{escape(portata, quote=False)}:")
            for piatto in piatti:
                nome = escape(piatto["nome"], quote=False)
                # 🥡 a destra del nome, accanto a 🌱 e ❄️ se ci sono
                righe.append(f"  • <b>{nome} 🥡</b>" if piatto.get("asporto") else f"  • {nome}")
    return "\n".join(righe)


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
