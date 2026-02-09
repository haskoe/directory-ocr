# Project Context: Automated File Processing Pipeline

## Applikationsbeskrivelse
Vi bygger en applikation, der overvåger en mappe for indgående filer, behandler dem i to trin ved hjælp af en lokal LLM (`llama-server`), og sorterer filerne baseret på succes eller fejl.

## Folder Struktur & Flow
Systemet opererer med følgende mappestruktur (alle på samme niveau):
- `/incoming`: Watch-folder for nye filer (`.jpg`, `.png`, `.pdf`).
- `/processed`: Arkiv for kildefiler, der er behandlet succesfuldt.
- `/errors`: Arkiv for kildefiler, der fejlede under behandling.
- `/output`: Destination for genererede `.txt` og `.json` filer.

start-llm.sh indeholder kommandoer til start af 1) OCR på jpg/png og 2) extract af specifik tekst i trin 2.

## Workflow Regler

### Trin 1: Tekstekstraktion
1.  **Trigger:** Når en fil lander i `/incoming`.
2.  **Inputformater:** - **PDF:** Ekstraher KUN tekst. Ignorer billeder/figurer indlejret i PDF'en. Brug et letvægtsbibliotek (f.eks. `PyPDF2` eller `pdfminer`) til dette for at sikre, at vi kun får tekstlaget.
    - **Billeder (JPG/PNG):** Brug `llama-server` (Vision capabilities) til at transskribere al synlig tekst.
3.  **Output:** Gem teksten som en `.txt` fil i `/output` mappen. Filnavnet skal matche kdefilen (f.eks. `faktura.pdf` -> `faktura.txt`).
4.  **Filhåndtering:**
    - **Succes:** Flyt kdefilen fra `/incoming` til `/processed`.
    - **Fejl:** Flyt kdefilen fra `/incoming` til `/errors`. Log fejlen.

### Trin 2: Data Strukturering (JSON)
1.  **Trigger:** Når en `.txt` fil er færdiggjort i Trin 1 (eller kør det som en sekventiel proces).
2.  **Input:** Læs indholdet af den genererede `.txt` fil.
3.  **Processing:** Send teksten til `llama-server` med en *brugerdefineret prompt* (skal kunne konfigureres).
    - Målet er at ekstrahere specifikke nøgleværdier.
4.  **Output:** Gem resultatet som en `.json` fil i `/output` mappen (f.eks. `faktura.json`).

## Teknisk Stack & Krav
- **OS:** Linux (alle varianter.
- **Sprog:** Python med anvendelse af UV til pakkehåndtering.
- **LLM Integration:** - Brug `llama-server` API (typisk OpenAI-compatible endpoint).
    - Vær opmærksom på context window limits.
- **Biblioteker:** - Brug `shutil` til at flytte filer.
    - Brug `pathlib` til stihåndtering.
    - Brug `watchdog` (Python).
- **Fejlhåndtering:** Robust `try/except` blokke omkring fil-I/O og API-kald. Applikationen må ikke crashe, hvis en enkelt fil er korrupt.

## Kodestil
- Skriv modulær kode: Adskil fil-overvågning, tekst-ekstraktion og LLM-kald i separate funktioner/klasser.
- Tilføj logging til konsollen, så man kan følge med i, hvilken fil der behandles, og hvor den flyttes hen.