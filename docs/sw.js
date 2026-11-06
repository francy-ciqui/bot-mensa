// sw.js - fa funzionare la pagina come un'app sul telefono.
// Prova sempre prima la rete (così il menu è quello nuovo);
// se manca la connessione, mostra l'ultima versione salvata.

const CASSETTO = "mensa-v2";

self.addEventListener("install", () => self.skipWaiting());
// All'avvio butta le copie delle versioni precedenti
self.addEventListener("activate", (e) =>
  e.waitUntil(
    caches.keys()
      .then((nomi) => Promise.all(nomi.filter((n) => n !== CASSETTO).map((n) => caches.delete(n))))
      .then(() => self.clients.claim())
  )
);

self.addEventListener("fetch", (evento) => {
  const richiesta = evento.request;
  if (richiesta.method !== "GET" || !richiesta.url.startsWith(self.location.origin)) return;

  // Per menu.json usiamo un indirizzo fisso, senza il "?t=..." che cambia ogni volta
  const chiave = new URL(richiesta.url);
  chiave.search = "";

  evento.respondWith(
    // "no-cache": chiede sempre a GitHub se c'è una versione nuova
    // (senza, il telefono può tenere la copia vecchia fino a 10 minuti)
    fetch(richiesta, { cache: "no-cache" })
      .then((risposta) => {
        if (risposta.ok) {
          const copia = risposta.clone();
          caches.open(CASSETTO).then((c) => c.put(chiave.href, copia));
        }
        return risposta;
      })
      .catch(() => caches.match(chiave.href))
  );
});
