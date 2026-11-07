# tabella.py - disegna il menu della settimana come una tabella (immagine PNG)
#
# Telegram non sa mostrare tabelle nel testo, quindi il bot manda una foto:
#   - colonne = i giorni (da lunedì a domenica)
#   - righe   = Primi, Secondi e Contorni, prima del pranzo e poi della cena
# I piatti vegetariani sono scritti in verde (le emoji come 🌱 nelle immagini non si vedono).

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

GIORNI_BREVI = ["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]

# Misure in pixel
LARGHEZZA_ETICHETTA = 150   # la prima colonna, con "Primi", "Secondi", ...
LARGHEZZA_GIORNO = 270      # ogni colonna di un giorno
MARGINE = 12                # spazio dentro ogni casella
DIMENSIONE = 21             # grandezza delle lettere

# Colori
SFONDO = "#ffffff"
LINEE = "#c9ccd1"
TESTO = "#1d1f23"
VERDE = "#1f7a3a"
GRIGIO = "#6b7078"
TESTATA = "#2b4c7e"         # la riga con i giorni
PRANZO = "#f6b73c"          # la fascia "PRANZO"
CENA = "#5b5fc7"            # la fascia "CENA"
RIGHE_ALTERNATE = ["#ffffff", "#f4f6f9"]

# Dove cercare un carattere che abbia le lettere accentate (è, à, ...)
CARATTERI = {
    "normale": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"],
    "grassetto": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"],
}


def carattere(tipo, dimensione=DIMENSIONE):
    for percorso in CARATTERI[tipo]:
        if Path(percorso).exists():
            return ImageFont.truetype(percorso, dimensione)
    return ImageFont.load_default(dimensione)


def _a_capo(testo, font, larghezza, disegno):
    """Spezza il testo in più righe perché stia nella larghezza della casella."""
    righe, riga = [], ""
    for parola in testo.split():
        prova = f"{riga} {parola}".strip()
        if disegno.textlength(prova, font=font) <= larghezza:
            riga = prova
        else:
            if riga:
                righe.append(riga)
            riga = parola
    if riga:
        righe.append(riga)
    return righe


def _piatto(nome):
    """Toglie le emoji dal nome e dice se il piatto è vegetariano."""
    vegetariano = "🌱" in nome
    surgelato = "❄️" in nome
    nome = nome.replace("🌱", "").replace("❄️", "").strip()
    if surgelato:
        nome += " *"
    return nome, vegetariano


def disegna_settimana(settimana, titolo):
    """settimana = lista di (giorno, menu) da lunedì a domenica.

    menu è come quello di menu.estrai_completo: {"pranzo": {"Primi": [...]}, "cena": {...}}.
    Restituisce l'immagine PNG come bytes, pronta da mandare a Telegram.
    """
    font = carattere("normale")
    font_b = carattere("grassetto")
    font_titolo = carattere("grassetto", 30)
    prova = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    alto_riga = DIMENSIONE + 7
    larghezza_testo = LARGHEZZA_GIORNO - 2 * MARGINE

    # Le portate nell'ordine in cui compaiono (di solito Primi, Secondi, Contorni)
    portate = {"pranzo": [], "cena": []}
    for _, menu in settimana:
        for servizio in portate:
            for portata in menu.get(servizio, {}):
                if portata not in portate[servizio]:
                    portate[servizio].append(portata)

    # 1) Prepara il contenuto di ogni riga e quanto è alta
    righe = []   # ("fascia", servizio) oppure ("piatti", portata, [caselle], altezza)
    for servizio in ["pranzo", "cena"]:
        if not portate[servizio]:
            continue
        righe.append(("fascia", servizio))
        for portata in portate[servizio]:
            caselle, altezza = [], 0
            for _, menu in settimana:
                casella = []   # lista di (riga di testo, vegetariano)
                for p in menu.get(servizio, {}).get(portata, []):
                    nome, veg = _piatto(p["nome"])
                    pezzi = _a_capo("• " + nome, font, larghezza_testo, prova)
                    casella += [(pezzo if i == 0 else "   " + pezzo, veg) for i, pezzo in enumerate(pezzi)]
                caselle.append(casella)
                altezza = max(altezza, len(casella) * alto_riga)
            righe.append(("piatti", portata, caselle, altezza + 2 * MARGINE))

    # 2) Misure dell'immagine
    alto_titolo, alto_testata, alto_fascia, alto_legenda = 64, 56, 40, 46
    larghezza = LARGHEZZA_ETICHETTA + LARGHEZZA_GIORNO * len(settimana)
    altezza = alto_titolo + alto_testata + alto_legenda + sum(
        alto_fascia if r[0] == "fascia" else r[3] for r in righe)
    immagine = Image.new("RGB", (larghezza, altezza), SFONDO)
    d = ImageDraw.Draw(immagine)

    # 3) Titolo
    d.text((MARGINE + 4, 16), titolo, font=font_titolo, fill=TESTO)
    y = alto_titolo

    # 4) Riga con i giorni
    d.rectangle([0, y, larghezza, y + alto_testata], fill=TESTATA)
    for n, (giorno, _) in enumerate(settimana):
        x = LARGHEZZA_ETICHETTA + n * LARGHEZZA_GIORNO
        scritta = f"{GIORNI_BREVI[giorno.weekday()]} {giorno.day}/{giorno.month}"
        w = d.textlength(scritta, font=font_b)
        d.text((x + (LARGHEZZA_GIORNO - w) / 2, y + 15), scritta, font=font_b, fill="#ffffff")
    y += alto_testata

    # 5) Le righe del menu
    alternata = 0
    for riga in righe:
        if riga[0] == "fascia":
            colore = PRANZO if riga[1] == "pranzo" else CENA
            d.rectangle([0, y, larghezza, y + alto_fascia], fill=colore)
            d.text((MARGINE, y + 8), riga[1].upper(), font=font_b,
                   fill="#1d1f23" if riga[1] == "pranzo" else "#ffffff")
            y += alto_fascia
            continue
        _, portata, caselle, alto = riga
        d.rectangle([0, y, larghezza, y + alto], fill=RIGHE_ALTERNATE[alternata % 2])
        alternata += 1
        d.text((MARGINE, y + MARGINE), portata, font=font_b, fill=TESTO)
        for n, casella in enumerate(caselle):
            x = LARGHEZZA_ETICHETTA + n * LARGHEZZA_GIORNO + MARGINE
            for i, (testo, veg) in enumerate(casella):
                d.text((x, y + MARGINE + i * alto_riga), testo, font=font, fill=VERDE if veg else TESTO)
        d.line([0, y + alto, larghezza, y + alto], fill=LINEE, width=1)
        y += alto

    # 6) Linee verticali tra i giorni (non sulle fasce colorate, per pulizia basta così)
    for n in range(len(settimana) + 1):
        x = LARGHEZZA_ETICHETTA + n * LARGHEZZA_GIORNO
        d.line([x - 1, alto_titolo, x - 1, y], fill=LINEE, width=1)

    # 7) Legenda
    d.text((MARGINE, y + 12), "In verde: piatto vegetariano.   * = può contenere prodotti surgelati",
           font=font, fill=GRIGIO)

    uscita = io.BytesIO()
    immagine.save(uscita, format="PNG", optimize=True)
    return uscita.getvalue()
