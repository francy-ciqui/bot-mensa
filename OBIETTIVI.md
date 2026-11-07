# Obiettivi del bot mensa

## Come funziona
Le prenotazioni non si fanno sul sito della mensa: si fanno con un messaggio WhatsApp al numero della mensa.

1. Ogni mattina verso le 7:15 il bot (su GitHub Actions) legge il menu del giorno dal sito e lo salva in `docs/menu.json`. Se GitHub parte in ritardo, il bot parte lo stesso fino alle 11, una volta sola al giorno.
   Prima controlla che il menu di oggi sia già sui due siti della mensa. Se manca (di solito il lunedì,
   quando la settimana nuova non è ancora caricata) non manda niente e lascia il lavoro alla partenza dopo.
   All'ultima partenza della mattina manda comunque quello che c'è.
   **A che ora la mensa carica il menu:** GitHub → Actions → Menu mensa → apri la partenza del lunedì →
   «orario» → «È l'ora giusta in Italia?». C'è scritto per esempio «Alle 07:16 il menu di oggi non è ancora
   sul sito» oppure «Alle 08:20 il menu di oggi è sul sito».
2. Subito dopo GitHub pubblica la pagina web (cartella `docs/`) su GitHub Pages.
3. Il bot manda su Telegram il menu e il link alla pagina a tutte le chat del segreto `TELEGRAM_CHAT_ID` (numeri separati da virgola).
   Nel messaggio c'è il menu **completo** della mensa (dal sito cimasristorazione.com) e i piatti
   che si possono prendere **d'asporto** sono in evidenza: 🥡 e grassetto. Se quel sito non risponde,
   il bot manda il messaggio di prima, con il solo menu d'asporto. La pagina web non cambia: mostra solo l'asporto.
   **Il lunedì**, prima del solito messaggio del giorno, il bot manda anche la **tabella** del menu completo
   di tutta la settimana: un'immagine con i giorni nelle colonne e Primi/Secondi/Contorni di pranzo e cena
   nelle righe (vegetariani in verde). Qui l'asporto non è segnato. È un'immagine perché Telegram
   nel testo non sa fare tabelle. La disegna `tabella.py`.
   Per provarlo un altro giorno: GitHub → Actions → Menu mensa → Run workflow → spunta «Manda anche il menu di tutta la settimana».
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

## Passare a un canale Telegram (se un giorno serve)
Oggi il bot scrive alle persone una per una: ognuno deve premere «Avvia» sul bot
e poi il suo numero di chat va aggiunto a mano nel segreto `TELEGRAM_CHAT_ID`.
Con un canale invece chi vuole il menu entra con un link, e chi non lo vuole più esce:
non si tocca più GitHub. **Il codice è già pronto**, va cambiato solo il segreto.

1. Su Telegram: matita ✏️ (nuovo messaggio) → **Nuovo canale**. Dagli un nome, es. «Menu Mensa Chieti».
2. Scegli **Pubblico** (con un nome tipo `menumensachieti`) oppure **Privato** (si entra solo col link d'invito).
3. Nel canale: impostazioni → **Amministratori** → **Aggiungi amministratore** → cerca `@menu_mensa_chieti_francy_bot`.
   Basta il permesso **Pubblica messaggi**.
4. Il valore da mettere nel segreto:
   - canale **pubblico**: `@menumensachieti` (con la @ davanti)
   - canale **privato**: scrivi un messaggio qualsiasi nel canale e chiedi a Claude di trovare
     il numero del canale (inizia con `-100…`).
5. Su GitHub: Settings → Secrets and variables → Actions → matita ✏️ su **TELEGRAM_CHAT_ID**
   e scrivi il valore del punto 4. (GitHub non ti mostra il valore vecchio: è normale.)
6. Se vuoi lo stesso valore anche sul PC, cambialo in `segreti.env`.
7. Prova: GitHub → **Actions** → **Menu mensa** → **Run workflow**. Il messaggio deve comparire nel canale.
8. Condividi il link del canale. Anche tu entri nel canale come tutti gli altri.

Si possono anche tenere insieme canale e persone, separati da virgola: `@menumensachieti,111111111`.
Ma se sei anche nel canale ti arriva due volte.
