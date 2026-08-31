# Kobo Comic Optimizer

Ottimizzatore di fumetti e manga per Kobo, progettato principalmente per macOS e Apple Silicon.

Il programma può elaborare PDF, CBZ, CBR, ZIP, RAR e cartelle contenenti immagini, creando file CBZ o PDF ottimizzati.

## Caratteristiche

- Supporto per PDF
- Supporto per CBZ e ZIP
- Supporto per CBR e RAR
- Supporto per cartelle contenenti immagini
- Supporto per più file contemporaneamente
- Ordinamento naturale di file e pagine
- Creazione di un unico file oppure di file separati
- Elaborazione parallela delle pagine nella modalità file unico
- Elaborazione parallela tra file nella modalità file separati
- Ridimensionamento automatico delle immagini
- Conversione in JPEG ottimizzato
- Compressione JPEG configurabile tramite preset
- Timer e indicatori di avanzamento
- Verifica finale dell'output
- Gestione automatica di `__MACOSX`, `.DS_Store` e file `._`
- Ambiente Python isolato automatico tramite `.venv`
- Installazione automatica delle dipendenze Python necessarie

---

# Requisiti

## Sistema

Il programma è progettato principalmente per:

- macOS
- Apple Silicon

## Python

È necessario avere Python 3 installato.

Il programma utilizza automaticamente un ambiente virtuale Python isolato chiamato:

```text
.venv
```

La cartella viene creata automaticamente accanto allo script alla prima esecuzione.

## Dipendenze Python

Lo script installa automaticamente, quando necessario:

- PyMuPDF
- Pillow

Non è necessario installarle manualmente con `pip`.

L'utilizzo di un ambiente virtuale evita i problemi di macOS/Homebrew relativi all'errore:

```text
externally-managed-environment
```

---

# Dipendenze opzionali per CBR e RAR

Per elaborare file:

- CBR
- RAR

è necessario avere almeno un estrattore compatibile disponibile nel sistema.

Lo script cerca automaticamente, in questo ordine:

```text
7zz
7z
unar
unrar
```

Su macOS può essere installato, ad esempio, `p7zip` tramite Homebrew:

```bash
brew install p7zip
```

In alternativa:

```bash
brew install unar
```

Queste dipendenze sono necessarie solo per l'elaborazione di archivi RAR e CBR.

---

# Avvio

Posiziona nella stessa cartella:

```text
KoboComicOptimizer.py
README.md
```

Poi rendi lo script eseguibile:

```bash
chmod +x KoboComicOptimizer.py
```

Avvialo con:

```bash
./KoboComicOptimizer.py
```

Oppure:

```bash
python3 KoboComicOptimizer.py
```

Alla prima esecuzione il programma:

1. crea automaticamente `.venv`
2. controlla le dipendenze
3. installa PyMuPDF e Pillow se mancanti
4. riavvia automaticamente lo script nell'ambiente isolato

Alle esecuzioni successive non reinstalla le dipendenze.

---

# Formati supportati

## Input

### Documenti e archivi

- PDF
- CBZ
- CBR
- ZIP
- RAR

### Immagini

- JPG
- JPEG
- PNG
- WEBP
- BMP
- GIF
- TIFF
- AVIF

### Cartelle

Sono supportate cartelle contenenti immagini.

---

# Formati di output

Il programma può creare:

- CBZ
- PDF

## CBZ

È generalmente il formato consigliato per fumetti e manga.

Le immagini vengono archiviate senza ulteriore compressione ZIP, perché i JPEG sono già compressi.

## PDF

Il programma crea un PDF utilizzando le immagini ottimizzate.

---

# Utilizzo

All'avvio puoi fornire:

- un singolo file
- più file contemporaneamente
- una cartella
- più cartelle

Puoi anche trascinare file e cartelle direttamente nel Terminale.

Il programma rileva automaticamente i contenuti supportati e mostra l'ordine di elaborazione.

---

# Avvio rapido

Nel menu principale è disponibile:

```text
1) AVVIO RAPIDO — premi INVIO
```

Le impostazioni predefinite sono:

```text
Preset: Kobo Small
Lato massimo: 1000 px
JPEG qualità: 50
Output: CBZ
Modalità: File unico
```

Per utilizzare queste impostazioni è sufficiente premere `INVIO`.

---

# Personalizzazione

È possibile scegliere:

## Preset

### Kobo Small

```text
Lato massimo: 1000 px
JPEG qualità: 50
```

### Kobo Standard

```text
Lato massimo: 1400 px
JPEG qualità: 60
```

### Alta qualità

```text
Lato massimo: 1800 px
JPEG qualità: 75
```

### Massima qualità

```text
Lato massimo: 2400 px
JPEG qualità: 85
```

---

# Modalità di output

## File unico

Tutti i file selezionati vengono raccolti rispettando l'ordine naturale e uniti in un unico CBZ o PDF.

Le sorgenti vengono elaborate sequenzialmente per garantire il corretto ordine delle pagine e dei volumi.

Successivamente, le immagini vengono ottimizzate in parallelo.

Questo significa che il parallelismo viene applicato alle pagine, non ai diversi volumi durante la raccolta.

---

## File separati

Ogni sorgente genera un proprio file di output.

In questa modalità il programma può elaborare più file contemporaneamente.

Ogni singolo file utilizza un solo processo interno per evitare un parallelismo eccessivo.

Il parallelismo avviene quindi tra i diversi fumetti.

---

# PDF

I PDF vengono convertiti tramite PyMuPDF.

Ogni pagina viene renderizzata e trasformata in immagine.

Il rendering utilizza una matrice di scala:

```text
2x
```

Le immagini risultanti vengono poi ridimensionate in base al preset selezionato.

---

# Ottimizzazione delle immagini

Durante l'elaborazione il programma:

1. corregge automaticamente l'orientamento EXIF
2. converte le immagini nel formato RGB
3. gestisce la trasparenza applicando uno sfondo bianco
4. ridimensiona le immagini quando superano il lato massimo del preset
5. salva il risultato come JPEG

Le immagini JPEG utilizzano:

```text
Subsampling: 4:2:0
Optimize: attivo
Progressive: attivo
```

---

# Indicatori di avanzamento

Durante l'elaborazione vengono mostrati:

- numero di pagine elaborate
- percentuale di completamento
- tempo trascorso

Esempio:

```text
Elaborate: 80/132 (60.6%) - 00:24
```

Durante la creazione del CBZ viene mostrato anche il numero di pagine archiviate.

---

# Verifica finale

Al termine dell'elaborazione il programma verifica il file creato.

## CBZ

Viene controllato che l'archivio contenga immagini valide.

## PDF

Viene controllato che il PDF possa essere aperto e contenga almeno una pagina.

Se la verifica fallisce, il file di output viene eliminato e viene segnalato un errore.

---

# Output

Il file viene normalmente creato nella stessa cartella della sorgente.

Il nome utilizza il suffisso:

```text
_kobo
```

Esempio:

```text
Manga.cbz
```

diventa:

```text
Manga_kobo.cbz
```

Se il nome esiste già:

```text
Manga_kobo_2.cbz
Manga_kobo_3.cbz
```

e così via.

---

# Dimensioni del file

La dimensione finale dipende principalmente da:

- dimensione originale delle immagini
- formato dell'input
- preset selezionato
- qualità JPEG selezionata
- livello di compressione già presente nell'originale

Un file ottimizzato può, in alcuni casi, risultare più grande dell'originale.

Questo accade soprattutto quando il file originale utilizza già una compressione molto efficiente oppure quando la conversione ricodifica immagini già ottimizzate.

Il programma mostra comunque il confronto finale:

```text
Originale: XX.XX MB
Finale:    XX.XX MB
Riduzione: XX.X%
```

Una riduzione negativa indica che il file finale è più grande dell'originale.

---

# Interruzione

Durante l'elaborazione puoi interrompere il programma con:

```text
CTRL + C
```

Il programma segnalerà l'annullamento dell'operazione.

---

# Struttura della cartella

Dopo la prima esecuzione, la struttura sarà simile a:

```text
Kobo Comic Optimizer/
│
├── KoboComicOptimizer.py
├── README.md
└── .venv/
```

La cartella `.venv` viene creata automaticamente e contiene l'ambiente Python isolato utilizzato dal programma.

Non è necessario modificarla manualmente.

---

# Note

I file temporanei utilizzati durante l'elaborazione vengono creati automaticamente e rimossi al termine dell'operazione.

I file e le cartelle macOS non necessari, come:

```text
__MACOSX
.DS_Store
._
```

vengono ignorati durante l'elaborazione.

---

# Compatibilità

Progettato principalmente per:

- macOS
- Apple Silicon
- Kobo
- KOReader

Per l'elaborazione di CBR e RAR è necessario installare un estrattore compatibile.