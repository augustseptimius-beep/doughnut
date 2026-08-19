#!/usr/bin/env python3
"""Læser API-nøgler fra miljøvariabler i stedet for fra kildekoden.

Baggrund: nøglerne til Klimaregnskabet.dk og Uddannelsesstatistik stod
hårdkodet i scripts/ indtil august 2026. Repoet er offentligt, så en nøgle er
kompromitteret i samme sekund den bliver pushet, uanset om nogen opdager det.
Rul den gamle nøgle hos udbyderen, sæt den nye som miljøvariabel, og skriv
aldrig en nøgle ind i en fil der ligger i git.

Brug i et fetch-script:

    from api_noegler import hent_noegle, kraev_noegle

    API_KEY = hent_noegle("KLIMAREGNSKABET_API_KEY")

    def main():
        kraev_noegle("KLIMAREGNSKABET_API_KEY", API_KEY, KLIMA_HJAELP)
        ...

`hent_noegle()` fejler bevidst ALDRIG ved import, heller ikke når variablen
mangler. Et script der ikke kan importeres fejler tavst i andre sammenhænge, og
det er præcis den fejlklasse `tjek_robusthed.py` findes for at fange (se
CLAUDE.md, punkt 19). Fejlen skal komme når scriptet køres, ikke når det læses.
"""

from __future__ import annotations

import os
import sys

# Hjælpetekster pr. kilde. Holdes her, så fejlbeskeden er ens uanset hvilket
# script brugeren tilfældigvis kørte først.
KLIMA_HJAELP = (
    "Nøglen fås ved at oprette en konto på https://klimaregnskabet.dk og bede "
    "om API-adgang. Brug en fælles funktionspostkasse, ikke en personlig konto."
)

UVM_HJAELP = (
    "Token'et hentes fra https://uddannelsesstatistik.dk under API-adgang. "
    "Det er et JWT bundet til den bruger der oprettede det, og det har typisk "
    "flere års levetid - behandl det som en adgangskode."
)


def hent_noegle(navn: str) -> str:
    """Returnerer miljøvariablen, eller tom streng hvis den ikke er sat.

    Fejler aldrig. Brug kraev_noegle() i main() til at afvise en manglende
    nøgle på et tidspunkt hvor brugeren kan se beskeden.
    """
    return os.environ.get(navn, "").strip()


def kraev_noegle(navn: str, vaerdi: str, hjaelp: str = "") -> str:
    """Afbryder med en brugbar besked hvis nøglen mangler."""
    if vaerdi:
        return vaerdi

    print(f"FEJL: miljøvariablen {navn} er ikke sat.", file=sys.stderr)
    print(file=sys.stderr)
    print("Sæt den for denne ene kørsel:", file=sys.stderr)
    print(f'    {navn}="din-noegle" python3 scripts/<script>.py', file=sys.stderr)
    print(file=sys.stderr)
    print("Eller permanent i din shell-profil (~/.zshrc på macOS):", file=sys.stderr)
    print(f'    export {navn}="din-noegle"', file=sys.stderr)
    if hjaelp:
        print(file=sys.stderr)
        print(hjaelp, file=sys.stderr)
    sys.exit(1)
