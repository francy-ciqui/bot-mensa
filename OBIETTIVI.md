# Obiettivi del bot mensa

## Come funziona
Le prenotazioni non si fanno sul sito della mensa: si fanno con un messaggio WhatsApp al numero della mensa.

1. Ogni mattina alle 7:15 il bot (su GitHub Actions) legge il menu del giorno dal sito e lo salva in `docs/menu.json`.
2. Subito dopo GitHub pubblica la pagina web (cartella `docs/`) su GitHub Pages.
3. Il bot ti manda su Telegram il link alla pagina.
4. Nella pagina spunti i piatti di pranzo e/o cena. La pagina scrive il messaggio di prenotazione.
5. Pranzo e cena hanno ciascuno il suo messaggio, con l'orario limite (pranzo entro le 10:00, cena entro le 17:00, da confermare).
6. Premi **Invia su WhatsApp**: si apre direttamente la chat della mensa e invii tu. In alternativa premi **Copia**.
7. I contorni hanno la casella **x2** per la doppia porzione.

## Regole
- Il bot non manda mai niente su WhatsApp da solo: l'invio lo fai sempre tu.
- Il sito della mensa viene visitato una sola volta al giorno.
- Token e segreti stanno solo in `segreti.env` e nei Secrets di GitHub.
- Nome, intolleranze e numero della mensa restano salvati solo nel tuo telefono, non nel repository.

## Formato del messaggio
```
Prenotazione mensa – giovedì 5 novembre
Nome: Francesco Ciquera
Pasto: pranzo
Primo: pasta al pomodoro
Secondo: pollo arrosto
Contorno: insalata
Intolleranze/allergie: nessuna
```
