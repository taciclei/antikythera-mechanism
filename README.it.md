# Meccanismo di Antikythera: una ricostruzione 3D funzionante e verificata

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · [Deutsch](README.de.md) · **Italiano** · [Português](README.pt.md) · [Ελληνικά](README.el.md) · [中文](README.zh.md) · [日本語](README.ja.md)

![Il meccanismo ricostruito, vista frontale di tre quarti](docs/images/front34.jpg)

https://github.com/user-attachments/assets/c810d3ee-ecfa-46e3-b11d-f919c3ae2cd9

https://github.com/user-attachments/assets/40b1f61b-5fb0-4b54-bd1c-1ba1f423a424


Il Meccanismo di Antikythera è un calcolatore astronomico in bronzo azionato a manovella, costruito in Grecia nel II o nel I secolo a.C. e recuperato da un relitto nel 1901. È la più antica macchina a ingranaggi complessa che si conosca. Questo repository ne contiene una ricostruzione 3D completa in **Blender 5.2**:

- tutte le **69 ruote dentate** hanno il loro numero reale di denti;
- i denti sono coniugati a evolvente, quindi ogni coppia ingrana e funziona davvero;
- ogni treno di ingranaggi è stato **verificato in frazioni esatte** rispetto al ciclo astronomico che riproduce;
- l'**assenza di collisioni** tra le parti è stata verificata sull'intera escursione del movimento.

L'intero modello è stato realizzato in un solo passaggio da Claude Opus 5.5 a partire da un unico prompt principale autosufficiente ([`PROMPT_OPUS.md`](PROMPT_OPUS.md)), e poi verificato in modo indipendente.

## Punti salienti

- **69 ruote dentate**, classificate in base al loro grado di certezza:
  - 30 **conservate**, fisicamente presenti nei frammenti (scansioni TC);
  - 7 **ricostruite**, sulla base di indizi solidi;
  - 32 **ipotetiche**, secondo il modello di Freeth et al. 2021.

  Ogni stato ha una propria collezione Blender, così ciascun gruppo può essere nascosto o mostrato.
- **Matematica esatta.** 1 giro della ruota principale b1 corrisponde a 1 anno. Il meccanismo ha esattamente **un grado di libertà** (la manovella), e tutti i 22 rapporti obiettivo coincidono esattamente in forma di frazione (esempi qui sotto).

  | Uscita | Velocità esatta (giri/anno) | Ciclo |
  |---|---|---|
  | Luna (media) | 254/19 | 254 mesi siderali in 19 anni |
  | Quadrante metonico | −5/19 | 5 giri = 19 anni = 235 mesi lunari |
  | Quadrante del Saros | −940/4237 | 4 giri = 223 mesi lunari |
  | Nodi lunari (Lancetta del Drago) | −5/93 | 18.6 anni, in senso inverso |
  | Venere | 289/462 rispetto a b1 | 289 periodi sinodici in 462 anni |
- **Funziona meccanicamente.**
  - Gli interassi sono esatti a 10⁻⁶ mm e ogni rapporto di condotta è ≥ 1.2.
  - Si registrano **0 compenetrazioni** su migliaia di campionamenti 3D (BVH): ogni ingranamento lungo un passo del dente, ogni ciclo perno-asola e 168 coppie di parti in 240 posizioni della manovella.
- **La Luna accelera e rallenta con ruote circolari**, non ovali. Un meccanismo a perno e asola sulla piattaforma rotante e3 riproduce l'anomalia lunare di Ipparco (±6.58°).
- **I pianeti tornano indietro al momento giusto.** Marte, Giove e Saturno diventano retrogradi all'opposizione (180° ± 0.03°), e Mercurio e Venere restano entro le loro elongazioni massime.
- **Una sola manovella muove tutto.** Tutto il movimento deriva da `AM_Controller["crank"]`, espresso in anni, tramite driver a espressione semplice: il file si anima quindi senza dover abilitare gli script Python.
- **Visualizzazione leggibile.** Ciascuno dei sette "pianeti" antichi ha un proprio colore e un'etichetta che lo segue (Sole, Luna, Mercurio, Venere, Marte, Giove, Saturno), oltre a una legenda.
- **Illuminazione museale.** La scena ha un fondale scuro a ciclorama e softbox dalla luce calda, con resa del colore AgX. Questo allestimento è stato scelto fra tre soluzioni renderizzate e confrontate fianco a fianco.
- **Vista esplosa.** Portando `AM_Controller["explode"]` da 0 a 1, ogni parte scorre lungo l'asse di impilamento.
- **Stampa 3D.** Un file STL per ogni parte più un 3MF completo, in tre profili: resina ×1, resina ×1.5 e FDM ×2.

| Quadrante anteriore | Quadranti posteriori |
|---|---|
| ![Quadrante anteriore con i pianeti colorati ed etichettati](docs/images/front.jpg) | ![Spirali metonica e del Saros](docs/images/back.jpg) |

| Vista esplosa | L'interno, a meccanismo aperto |
|---|---|
| ![Immagine fissa della vista esplosa](docs/images/exploded.jpg) | ![Fotogramma del video della vista esplosa](docs/images/exploded_video_frame.jpg) |

## Video

- [`antikythera.mp4`](build/out/renders/antikythera.mp4): 20 s. La manovella avanza di 4 anni e pianeti, Luna e quadranti posteriori si muovono tutti insieme.
- [`antikythera_eclate.mp4`](build/out/renders/antikythera_eclate.mp4): 15 s in vista esplosa. Il meccanismo si apre strato dopo strato mentre gli ingranaggi continuano a girare, poi si richiude.

I pianeti che nei video a volte si muovono **all'indietro** non sono un errore. È il **moto retrogrado** osservato dalla Terra, e il meccanismo è stato costruito proprio per mostrarlo. La Lancetta del Drago (i nodi lunari) gira sempre in senso inverso.

## Avvio rapido

1. Installare **Blender 5.2** o una versione successiva.
2. Aprire [`build/out/am.blend`](build/out/am.blend) e premere **Spazio** per riprodurre l'animazione.
3. Selezionare `AM_Controller` e modificarne le proprietà personalizzate:
   - `crank`: anni; 1 corrisponde a un giro di b1;
   - `explode`: da 0 a 1;
   - `patina`: 0 è bronzo nuovo, 1 è la patina da museo.
4. Usare l'Outliner per nascondere le collezioni:
   - `AM_CASE` e `AM_DIALS` per vedere gli ingranaggi;
   - `AM_HYPOTHETICAL` per conservare solo ciò che è attestato;
   - `AM_LABELS` per rimuovere le etichette;
   - `AM_STAGE` per rimuovere il set di illuminazione.
5. Fare clic su una parte qualsiasi per leggerne le proprietà personalizzate: `status`, `role`, `teeth`, `module` e `sources`.

### Rieseguire la verifica

Usare il Python incluso in Blender. I percorsi indicati qui sotto valgono per macOS; vanno adattati sugli altri sistemi.

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
BL=/Applications/Blender.app/Contents/MacOS/Blender

$PY tools/validate_spec.py          # exact linear solve (1 DOF, 22 targets), centre distances, collision screening
$PY tools/check_kinematics.py       # pin-and-slot laws, followers, elongations, retrogrades, solar apogee
cd build && $PY -m unittest discover -s tests && $PY -m am.verify --stage all && cd ..
$BL -b build/out/am.blend --python-exit-code 1 -P tools/crosscheck_blend.py   # Blender rotations vs an independent solver
```

[`build/README.md`](build/README.md) elenca ogni fase di costruzione, verifica, esportazione e rendering, con un comando per ciascuna fase.

### Ricostruire tutto dal prompt principale

In una cartella **vuota**, con [Claude Code](https://claude.com/claude-code):

```sh
claude -p --model 'claude-opus-5-5[1m]' --effort xhigh --permission-mode acceptEdits \
  --allowedTools Bash Read Write Edit Glob Grep < PROMPT_OPUS.md
```

- [`prompts/PROMPT_OPUS_v1_validated.md`](prompts/PROMPT_OPUS_v1_validated.md) è la versione esatta che ha prodotto questa build in un solo passaggio (89 min).
- [`PROMPT_OPUS.md`](PROMPT_OPUS.md) è la v1.2. Aggiunge i colori e le etichette dei pianeti, l'allestimento museale, il cursore della vista esplosa e il video della vista esplosa. Tutti questi elementi sono stati aggiunti a questa build in un secondo momento con gli script in `tools/`, e la v1.2 non è ancora stata rieseguita da zero.

## Come è stato realizzato

1. **Ricerca.** Agenti in parallelo hanno letto le fonti primarie: Freeth et al. 2006, 2008 e 2021 (con le Supplementary Information), Price 1974, Budiselic et al. 2020, Woan & Bayley 2024, Anastasiou et al. 2014 e altre. I risultati sono stati riconciliati in un unico insieme di dati, poi controllati da un agente scettico.
2. **Specifica.** [`spec/antikythera.json`](spec/antikythera.json) è l'unica fonte di verità. Riporta denti, modulo, posizione dell'asse, intervallo in z e foro di ogni ruota dentata, oltre a ogni albero, perno fisso, mozzo, spina, quadrante e materiale. È generata da `tools/make_spec.py`, che corregge 22 impossibilità geometriche presenti nei dati pubblicati (per esempio, b2 non può ingranare sia con c1 sia con l1 alle distanze pubblicate). Ogni interasse è risolto in modo esatto.
3. **Verifiche indipendenti.** `tools/validate_spec.py` e `tools/check_kinematics.py` non condividono codice con il generatore, e i test di mutazione confermano che rilevano gli errori introdotti di proposito.
4. **Denti a corona per inviluppo.** `tools/crown_envelope.py` calcola i denti frontali (a corona) di a1 e q1 come la regione che i denti della ruota coniugata non spazzano mai. `tools/test_crowns_blender.py` li verifica poi con BVH in Blender.
5. **Revisioni avversariali.** Due tornate di revisori indipendenti hanno esaminato i dati, l'API di Blender testata dal vivo, l'eseguibilità e la geometria, individuando 5 problemi bloccanti e circa 60 altri problemi. Sono stati tutti risolti.
6. **Build in un solo passaggio** da parte di una nuova sessione di Opus 5.5, partendo dal solo prompt: 131 turni, circa 5000 righe di codice e tutti i criteri di accettazione superati.
7. **Verifica indipendente** del risultato: test, verifiche esatte, il controllo BVH completo e un confronto incrociato di ogni corpo in `am.blend` con il risolutore indipendente (7·10⁻⁷ rad).

## Struttura del repository

```
PROMPT_OPUS.md            master prompt (v1.2), self-contained; embeds the full JSON spec + SHA-256
prompts/                  the prompt version validated by the one-pass build (v1)
spec/antikythera.json     single source of truth (gears, axes, shafts, trains, dials, staging, video)
research/                 raw multi-agent research results with source URLs
tools/                    spec generator, validators, crown envelopes, annotation/staging/explode/render scripts
build/                    the project generated by the one-pass build (am/, blender_scripts/, tests/, README)
build/out/                am.blend, verification report (report.md/html), checks, print files, renders, videos
docs/                     dossier (HTML) and images
```

## Limiti dichiarati

- I treni planetari, i nodi lunari e il Sole vero seguono il modello **ipotetico** di Freeth et al. 2021. Un'animazione funzionante non dimostra come fosse costruito l'originale.
- Alcune grandezze non sono pubblicate. Per queste la specifica usa valori predefiniti documentati, elencati in `spec/antikythera.json` → `unresolved_defaults`:
  - angoli degli assi sulla piastra posteriore;
  - raggi degli anelli del cosmo;
  - fasi iniziali (l'epoca non è calibrata).
- I denti sono evolventi coniugate (con una cremagliera a 30°, che corrisponde all'antico dente a triangolo equilatero), non i triangoli limati a mano dell'originale.
- I colori dei pianeti servono solo alla leggibilità; non hanno valore storico.

## Fonti principali

- T. Freeth et al., "A Model of the Cosmos in the ancient Greek Antikythera Mechanism", *Scientific Reports* 11, 5821 (2021), con le relative Supplementary Information.
- T. Freeth et al., "Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism", *Nature* 444, 587 (2006).
- T. Freeth, A. Jones, J. Steele, Y. Bitsakis, "Calendars with Olympiad display and eclipse prediction on the Antikythera Mechanism", *Nature* 454, 614 (2008).
- T. Freeth & A. Jones, "The Cosmos in the Antikythera Mechanism", ISAW Papers 4 (2012).
- D. de Solla Price, *Gears from the Greeks* (1974).
- C. Budiselic et al. (2020); G. Woan & J. Bayley (2024): numero di fori dell'anello del calendario.
- M. Anastasiou et al. (2014): le spirali dei quadranti posteriori.

L'elenco completo con gli URL si trova in `spec/antikythera.json` → `sources`.

## Licenza

- **Codice**: MIT ([`LICENSE`](LICENSE)).
- **Render, video, modello 3D, file di stampa e testi**: CC BY 4.0 ([`LICENSE-MEDIA.md`](LICENSE-MEDIA.md)).
- **Dati scientifici**: si prega di citare le opere indicate sopra.

---

Realizzato con [Claude Code](https://claude.com/claude-code) (Claude Opus 5 / 5.5) per taciclei.
