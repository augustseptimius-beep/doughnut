#!/usr/bin/env python3
"""Checker hvilke lag der indeholder 'mark' i LFST WFS"""
import urllib.request
import xml.etree.ElementTree as ET

url = "https://geodata.fvm.dk/geoserver/ows?service=WFS&version=2.0.0&request=GetCapabilities"
req = urllib.request.Request(url, headers={"User-Agent": "DoughnutDK/1.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    raw = resp.read().decode("utf-8", errors="replace")

root = ET.fromstring(raw)
ns = {"wfs": "http://www.opengis.net/wfs/2.0"}
names = [ft.text for ft in root.findall(".//wfs:FeatureType/wfs:Name", ns) if ft.text]

print("=== Alle lag i LFST WFS ===")
for n in sorted(names):
    print(n)

print("\n=== Lag med 'mark' i navn ===")
for n in names:
    if "mark" in n.lower():
        print(n)
