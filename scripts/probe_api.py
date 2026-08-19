#!/usr/bin/env python3
"""
Probe-script: finder den korrekte URL og parametre til klimaregnskabet.dk API.
Kør én gang, paste output til Claude.
"""
import json
import sys
from pathlib import Path
import requests
import urllib3
urllib3.disable_warnings()

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_noegler import hent_noegle, kraev_noegle, KLIMA_HJAELP  # noqa: E402

API_KEY = kraev_noegle(
    "KLIMAREGNSKABET_API_KEY", hent_noegle("KLIMAREGNSKABET_API_KEY"), KLIMA_HJAELP
)

HEADERS_VARIANTS = [
    {"x-api-key": API_KEY, "Accept": "application/json"},
    {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"},
    {"Authorization": f"Token {API_KEY}", "Accept": "application/json"},
    {"api-key": API_KEY, "Accept": "application/json"},
]

URL_VARIANTS = [
    "https://www.klimaregnskabet.dk/api",
    "https://www.klimaregnskabet.dk/api/data",
    "https://www.klimaregnskabet.dk/api/v1/data",
    "https://www.klimaregnskabet.dk/api/v1/noegletal",
    "https://www.klimaregnskabet.dk/api/noegletal",
    "https://www.klimaregnskabet.dk/api/keydata",
    "https://www.klimaregnskabet.dk/api/results",
    "https://api.klimaregnskabet.dk",
    "https://api.klimaregnskabet.dk/data",
    "https://api.klimaregnskabet.dk/v1/data",
    "https://api.klimaregnskabet.dk/v1/noegletal",
    "https://api.klimaregnskabet.dk/v1/keydata",
    "https://api.klimaregnskabet.dk/v1/municipality",
    "https://api.klimaregnskabet.dk/v1/kommuner",
]

PARAM_VARIANTS = [
    {"year": 2023, "municipality": 101, "datatype": "Nøgletal"},
    {"year": 2023, "kommune": 101, "datatype": "Nøgletal"},
    {"aar": 2023, "kommune": 101, "datatype": "Nøgletal"},
    {"År": 2023, "Kommune": 101, "Datatyper": "Nøgletal"},
    {"year": 2023, "municipalityCode": 101, "type": "Nøgletal"},
    {"year": "2023", "municipality": "101", "datatype": "Nøgletal"},
]

print("=== Klimaregnskabet API Probe ===\n")
print(f"Tester {len(URL_VARIANTS)} URL'er x {len(HEADERS_VARIANTS)} header-varianter\n")

found = []

for url in URL_VARIANTS:
    for headers in HEADERS_VARIANTS[:2]:  # Test kun de 2 mest sandsynlige headers
        params = PARAM_VARIANTS[0]
        try:
            r = requests.get(url, params=params, headers=headers, timeout=8, verify=True)
            status = r.status_code
            if status != 404:
                content_type = r.headers.get("Content-Type", "")
                print(f"✓ {status} | {url}")
                print(f"  Headers: {dict(list(headers.items())[:1])}")
                print(f"  Content-Type: {content_type}")
                print(f"  Body (500 chars): {r.text[:500]}")
                print()
                if status == 200:
                    found.append((url, headers, params))
            else:
                print(f"  404 | {url}")
        except Exception as e:
            print(f"  ERR | {url} — {str(e)[:80]}")

if not found:
    print("\n--- Ingen 200 OK fundet. Prøver POST-requests ---\n")
    for url in URL_VARIANTS[:6]:
        headers = HEADERS_VARIANTS[0]
        payload = {"year": 2023, "municipality": 101, "datatype": "Nøgletal"}
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=8, verify=True)
            if r.status_code != 404:
                print(f"POST {r.status_code} | {url}")
                print(f"  Body: {r.text[:500]}")
                print()
        except Exception as e:
            print(f"  POST ERR | {url} — {str(e)[:60]}")

print("\n=== Færdig. Paste dette output til Claude ===")
