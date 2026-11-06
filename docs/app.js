// app.js - legge menu.json, mostra i piatti e compone i messaggi di prenotazione
// (uno per il pranzo e uno per la cena, separati)

const $ = (id) => document.getElementById(id);
let menu = null;

// Entro che ora si prenota ogni pasto. Se cambiano, basta modificare qui.
const SCADENZE = { pranzo: "10:00", cena: "17:00" };

// I 14 allergeni di legge, con i numeri usati dalla mensa nel menu
// (es. "Allergeni: 1-6-10" = glutine, soia, senape)
const ALLERGENI = {
  1: "glutine", 2: "crostacei", 3: "uova", 4: "pesce", 5: "arachidi",
  6: "soia", 7: "latte/lattosio", 8: "frutta a guscio", 9: "sedano", 10: "senape",
  11: "sesamo", 12: "solfiti", 13: "lupini", 14: "molluschi",
};

// --- Nome, numero e "altro": si ricordano l'ultima cosa scritta (salvate nel telefono) ---
for (const campo of ["nome", "allergie", "numero"]) {
  let valore = localStorage.getItem("mensa-" + campo) || "";
  if (campo === "allergie" && valore === "nessuna") valore = ""; // vecchio valore predefinito
  $(campo).value = valore;
  $(campo).addEventListener("input", () => {
    localStorage.setItem("mensa-" + campo, $(campo).value.trim());
    aggiornaTutto();
  });
}

// --- Pulsanti delle intolleranze: si toccano per accenderli o spegnerli ---
let mieiAllergeni = JSON.parse(localStorage.getItem("mensa-allergeni") || "[]");
for (const [numero, nome] of Object.entries(ALLERGENI)) {
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = "chip";
  chip.textContent = nome;
  const n = Number(numero);
  chip.setAttribute("aria-pressed", mieiAllergeni.includes(n));
  chip.addEventListener("click", () => {
    mieiAllergeni = mieiAllergeni.includes(n)
      ? mieiAllergeni.filter((x) => x !== n)
      : [...mieiAllergeni, n].sort((a, b) => a - b);
    chip.setAttribute("aria-pressed", mieiAllergeni.includes(n));
    localStorage.setItem("mensa-allergeni", JSON.stringify(mieiAllergeni));
    aggiornaAvvisi();
    aggiornaTutto();
  });
  $("allergeni").appendChild(chip);
}

// La riga del messaggio: "latte/lattosio, glutine, pomodoro" oppure "nessuna"
function testoAllergie() {
  const voci = mieiAllergeni.map((n) => ALLERGENI[n]);
  const altro = $("allergie").value.trim();
  if (altro) voci.push(altro);
  return voci.length ? voci.join(", ") : "nessuna";
}

// Sotto ogni piatto che contiene uno dei tuoi allergeni compare "⚠️ contiene …"
function aggiornaAvvisi() {
  document.querySelectorAll(".piatto").forEach((riga) => {
    const delPiatto = JSON.parse(riga.dataset.allergeni || "[]");
    const problemi = delPiatto.filter((n) => mieiAllergeni.includes(n)).map((n) => ALLERGENI[n]);
    const avviso = riga.querySelector(".attenzione");
    avviso.textContent = problemi.length ? "⚠️ contiene " + problemi.join(", ") : "";
    avviso.hidden = problemi.length === 0;
  });
}

// "Primi" -> "Primo", "Secondi" -> "Secondo", "Contorni" -> "Contorno"
function etichetta(portata) {
  const p = portata.toLowerCase();
  if (p.startsWith("prim")) return "Primo";
  if (p.startsWith("second")) return "Secondo";
  if (p.startsWith("contorn")) return "Contorno";
  return portata;
}

// Nel messaggio niente 🌱 ❄️ e niente MAIUSCOLO
function pulisci(piatto) {
  let t = piatto.replace("🌱", "").replace("❄️", "").trim();
  if (t === t.toUpperCase()) t = t.toLowerCase();
  return t;
}

// WhatsApp vuole il numero con il prefisso del paese e solo cifre: "333 1234567" -> "393331234567"
// Se il campo è vuoto, WhatsApp ti fa scegliere tu a chi mandarlo.
function numeroWhatsApp() {
  let n = $("numero").value.replace(/\D/g, "");
  if (n.startsWith("00")) n = n.slice(2);
  if (n.length === 10 && n.startsWith("3")) n = "39" + n; // cellulare italiano senza +39
  return n;
}

function oggiISO() {
  const d = new Date();
  const due = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${due(d.getMonth() + 1)}-${due(d.getDate())}`;
}

// --- Disegna le caselle di un pasto (pranzo o cena) ---
function mostraPasto(pasto) {
  const portate = menu[pasto] || {};
  const sezione = $(pasto);
  const contenitore = sezione.querySelector(".portate");
  contenitore.innerHTML = "";
  if (Object.keys(portate).length === 0) return;

  for (const [portata, piatti] of Object.entries(portate)) {
    const gruppo = document.createElement("fieldset");
    const titolo = document.createElement("legend");
    titolo.textContent = portata;
    gruppo.appendChild(titolo);
    const eContorno = etichetta(portata) === "Contorno";

    for (const voce of piatti) {
      // (accetta anche il vecchio menu.json, dove il piatto era solo testo)
      const piatto = typeof voce === "string" ? voce : voce.nome;
      const riga = document.createElement("div");
      riga.className = "piatto";
      riga.dataset.allergeni = JSON.stringify(voce.allergeni || []);

      const scelta = document.createElement("label");
      const casella = document.createElement("input");
      casella.type = "checkbox";
      casella.dataset.portata = portata;
      casella.value = piatto;
      const testo = document.createElement("span");
      testo.textContent = piatto;
      const attenzione = document.createElement("small");
      attenzione.className = "attenzione";
      attenzione.hidden = true;
      testo.appendChild(attenzione);
      scelta.append(casella, testo);
      riga.appendChild(scelta);

      // La doppia porzione si può chiedere solo per i contorni
      if (eContorno) {
        const doppia = document.createElement("label");
        doppia.className = "doppia";
        doppia.hidden = true;
        const x2 = document.createElement("input");
        x2.type = "checkbox";
        x2.className = "x2";
        doppia.append(x2, " x2");
        riga.appendChild(doppia);
        x2.addEventListener("change", () => {
          // Doppia porzione per un solo contorno: spuntandone una, si tolgono le altre
          if (x2.checked) {
            sezione.querySelectorAll(".x2").forEach((altra) => {
              if (altra !== x2) altra.checked = false;
            });
          }
          aggiornaPasto(pasto);
        });
      }
      casella.addEventListener("change", () => aggiornaPasto(pasto));
      gruppo.appendChild(riga);
    }
    contenitore.appendChild(gruppo);
  }
  sezione.hidden = false;
}

// --- Compone il messaggio di un pasto ---
function componi(pasto) {
  const sezione = $(pasto);
  const scelti = {};
  sezione.querySelectorAll(".piatto").forEach((riga) => {
    const casella = riga.querySelector("label:first-child input");
    if (!casella.checked) return;
    const x2 = riga.querySelector(".x2");
    let nome = pulisci(casella.value);
    if (x2 && x2.checked) nome += " (doppia porzione)";
    const tipo = etichetta(casella.dataset.portata);
    (scelti[tipo] = scelti[tipo] || []).push(nome);
  });
  if (Object.keys(scelti).length === 0) return null;

  const righe = [
    `Prenotazione mensa – ${menu.giorno}`,
    `Nome: ${$("nome").value.trim()}`,
    `Pasto: ${pasto}`,
  ];
  for (const tipo of ["Primo", "Secondo", "Contorno"]) {
    righe.push(`${tipo}: ${scelti[tipo] ? scelti[tipo].join(", ") : "nessuno"}`);
    delete scelti[tipo];
  }
  for (const [tipo, piatti] of Object.entries(scelti)) righe.push(`${tipo}: ${piatti.join(", ")}`);
  righe.push(`Intolleranze/allergie: ${testoAllergie()}`);
  return righe.join("\n");
}

// --- Orario limite: "Prenota entro le 10:00" oppure "Tempo scaduto" ---
function aggiornaScadenza(pasto) {
  const p = $(pasto).querySelector(".scadenza");
  const [ore, minuti] = SCADENZE[pasto].split(":").map(Number);
  const limite = new Date();
  limite.setHours(ore, minuti, 0, 0);
  const mancano = Math.round((limite - new Date()) / 60000); // minuti

  if (menu.data !== oggiISO()) {
    p.textContent = `⏰ Si prenota entro le ${SCADENZE[pasto]}`;
    p.className = "scadenza";
  } else if (mancano <= 0) {
    p.textContent = `⛔ Tempo scaduto: si prenotava entro le ${SCADENZE[pasto]}`;
    p.className = "scadenza scaduta";
  } else {
    const h = Math.floor(mancano / 60), m = mancano % 60;
    const resto = h > 0 ? `${h} h ${m} min` : `${m} min`;
    p.textContent = `⏰ Prenota entro le ${SCADENZE[pasto]} (mancano ${resto})`;
    p.className = mancano <= 30 ? "scadenza vicina" : "scadenza";
  }
}

// La casella "x2" compare solo se il contorno è spuntato e NON hai preso un primo
function aggiornaDoppie(sezione) {
  const primoPreso = [...sezione.querySelectorAll("label:first-child input:checked")]
    .some((c) => etichetta(c.dataset.portata) === "Primo");
  sezione.querySelectorAll(".doppia").forEach((doppia) => {
    const contorno = doppia.parentElement.querySelector("label:first-child input");
    const permessa = contorno.checked && !primoPreso;
    doppia.hidden = !permessa;
    if (!permessa) doppia.querySelector(".x2").checked = false;
  });
}

function aggiornaPasto(pasto) {
  const sezione = $(pasto);
  aggiornaDoppie(sezione);
  const testo = componi(pasto);
  const wa = sezione.querySelector(".whatsapp");
  sezione.querySelector(".anteprima").textContent = testo || "Spunta almeno un piatto.";
  sezione.querySelector(".copia").disabled = !testo;
  wa.classList.toggle("disattivo", !testo);
  wa.href = testo ? `https://wa.me/${numeroWhatsApp()}?text=` + encodeURIComponent(testo) : "#";
  aggiornaScadenza(pasto);
}

function aggiornaTutto() {
  if (!menu) return;
  aggiornaPasto("pranzo");
  aggiornaPasto("cena");
}

// --- Pulsanti Copia e WhatsApp di ogni pasto ---
for (const pasto of ["pranzo", "cena"]) {
  const sezione = $(pasto);
  const bottone = sezione.querySelector(".copia");
  bottone.addEventListener("click", async () => {
    const testo = componi(pasto);
    if (!testo) return;
    try {
      await navigator.clipboard.writeText(testo);
    } catch {
      // Piano B per i browser che non permettono la copia diretta
      const area = document.createElement("textarea");
      area.value = testo;
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }
    bottone.textContent = "✅ Copiato";
    setTimeout(() => (bottone.textContent = "📋 Copia"), 2000);
  });
  const wa = sezione.querySelector(".whatsapp");
  wa.addEventListener("click", (e) => {
    if (wa.classList.contains("disattivo")) e.preventDefault();
  });
}

function mostraAvviso(testo) {
  $("avviso").textContent = testo;
  $("avviso").hidden = false;
}

// --- Avvio: scarica menu.json (sempre la versione più nuova) ---
async function avvia() {
  try {
    const risposta = await fetch("menu.json?t=" + Date.now(), { cache: "no-store" });
    menu = await risposta.json();
  } catch {
    $("giorno").textContent = "";
    mostraAvviso("Non riesco a caricare il menu. Controlla la connessione e riapri la pagina.");
    return;
  }

  $("giorno").textContent = menu.giorno ? `Menu di ${menu.giorno}` : "";
  if (menu.data && menu.data !== oggiISO()) {
    mostraAvviso(`Attenzione: questo è il menu di ${menu.giorno}, non quello di oggi.`);
  }
  if (menu.errore) {
    mostraAvviso("Stamattina il bot non è riuscito a leggere il menu dal sito.");
  } else if (Object.keys(menu.pranzo || {}).length + Object.keys(menu.cena || {}).length === 0) {
    mostraAvviso("Per oggi sul sito non c'è nessun menu.");
  }
  mostraPasto("pranzo");
  mostraPasto("cena");
  aggiornaAvvisi();
  aggiornaTutto();
  setInterval(aggiornaTutto, 60000); // ogni minuto aggiorna il "mancano …"
}

avvia();

// Permette di aggiungere la pagina alla schermata Home e di aprirla anche offline
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");
