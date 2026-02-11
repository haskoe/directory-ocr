# Project Context: Automated File Processing Pipeline

## Applikationsbeskrivelse
Vi bygger en applikation med to opgaver:
1) Ekstrahere tekst fra alle billed- og pdf-filer i `/incoming` med brug af vision LLM og placere den ekstraherede tekst i folder '/extracted' og efter alle filer i incoming er processeret:
2) Hvis der er en fil kaldet matchwith.csv så matches filer i '/extracted' en for en med matchwith.csv baseret på dato, beskrivelse og beløb kolonner i matchwith.csv. Hvis der er fundet et match flyttes den ekstraherede tekstfil og fundne række til folder '/matches'. Hvis der ikke er fundet et match beholdes ekstraheret tekstfil.

efter 2) må den gerne sleepes i 2 sekunder og så startes der med 1) igen. 2) må kun startes hvis der er behandlet en eller flere filer i 1).

## Folder Struktur & Flow
Systemet opererer med følgende mappestruktur (alle på samme niveau):
- `/incoming`: Folder for nye billed- og pdf-filer (`.jpg`, `.png`, `.pdf`).
- `/extracted`: Folder for tekstfiler genereret fra Trin 1.
- `/processed`: Arkiv for kildefiler, der er behandlet succesfuldt.
- `/match`: Folder for tekstfiler med fundet match.
- `/errors`: Arkiv for kildefiler, der fejlede under behandling.
- `/output`: Destination for genererede `.txt` og `.json` filer.

start-llm.sh indeholder kommandoer til start af 1) OCR på jpg/png og 2) extract af specifik tekst i trin 2.

## Workflow Regler

### Trin 1: Tekstekstraktion
1.  **Trigger:** En eller flere filer i i `/incoming`.
2.  **Inputformater:** - **PDF:** Ekstraher KUN tekst. Ignorer billeder/figurer indlejret i PDF'en. Brug et letvægtsbibliotek (f.eks. `PyPDF2` eller `pdfminer`) til dette for at sikre, at vi kun får tekstlaget.
    - **Billeder (JPG/PNG):** Brug `llama-server` (Vision capabilities) til at transskribere al synlig tekst.
3.  **Output:** Gem teksten som en `.txt` fil i `/output` mappen. Filnavnet skal matche kdefilen (f.eks. `faktura.pdf` -> `faktura.txt`).
4.  **Filhåndtering:**
    - **Succes:** Flyt kdefilen fra `/incoming` til `/processed`.
    - **Fejl:** Flyt kdefilen fra `/incoming` til `/errors`. Log fejlen.

### Trin 2: Data Strukturering (JSON)
1.  **Trigger:** Hvis filen matchwith.csv eksisterer og der er en eller flere filer i extracted.
2.  **Input:** Indhold af den genereret fil fra trin 1 som sammenholdes med en fil hvor hver række indeholder dato, beskrivelse, beløb ogh total og opgaven er at finde den række som er bedste match.
3.  **Processing:** Send teksten til `llama-server` med en *prompt* som instruerer LLM om at finde bedste match (skal kunne konfigureres).
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