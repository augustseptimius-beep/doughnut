"""
build_master_csv.py - Konsolider alle rådata-CSV'er til én master-fil i long format.

Kører efter alle fetch-scripts. Producerer data/master_indicators.csv som
webapp'en læser fra. Long format gør filen forsker-venlig (tidy data) og
fjerner behovet for 25+ separate CSV-loads i webapp/lib/data.ts.

Output-skema (én række pr. kommune × indikator):
  kommune_kode, kommune_navn, indicator_id, ratio, raw_value,
  unit, data_year, source, category, dimension

Kør:
  cd /sti/til/doughnut
  python3 scripts/build_master_csv.py

Driftsregel:
  1. Kør fetch-script(s) for de indikatorer du vil opdatere
  2. Kør DETTE script - opdaterer data/master_indicators.csv
  3. Commit + push via GitHub Desktop
"""

import csv
import os
import sys
from pathlib import Path

# ─── Stier ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT = DATA_DIR / "master_indicators.csv"

# ─── INDIKATOR-MAPPING (single source of truth for build) ──────────────
# Hver entry beskriver en indikator: hvor data kommer fra, hvilke kolonner
# der skal læses, og metadata til output. Dette er den ENESTE liste der
# skal opdateres når en indikator tilføjes eller fjernes.
#
# Felter:
#   id          - matcher INDICATORS-id i webapp/lib/shared.ts
#   csv         - filnavn i data/
#   ratio_col   - kolonne med ratio (allerede beregnet af fetch-script)
#   raw_col     - kolonne med råværdi (kan være None hvis ikke gemt)
#   unit        - enhed for råværdi (vises i UI)
#   data_year   - årstal for senest data
#   source      - kort kildetekst
#   category    - "social" eller "ecological"
#   dimension   - hvilken kategori/dimension den hører til
#   inverse_ratio - hvis True: ratio i CSV er "inverteret eco" (lav=værre).
#                   Konverteres til direct via 10000/inverse, så høj=overshoot.
#                   Bruges for spildevand (N, P) og affald.

SOCIAL_INDICATORS = [
    # === Sundhed ===
    {"id": "life_expectancy", "csv": "doughnut_scores.csv", "ratio_col": "life_expectancy_ratio", "raw_col": "life_expectancy_raw", "unit": "år", "data_year": "2023", "source": "DST HISBK", "category": "social", "dimension": "sundhed"},
    {"id": "hospital_short", "csv": "sundhed_extra_scores.csv", "ratio_col": "hospital_short_ratio", "raw_col": "hospital_short_pct", "unit": "%", "data_year": "2023", "source": "DST SBR01", "category": "social", "dimension": "sundhed"},
    {"id": "hospital_long", "csv": "sundhed_extra_scores.csv", "ratio_col": "hospital_long_ratio", "raw_col": "hospital_long_pct", "unit": "%", "data_year": "2023", "source": "DST SBR01", "category": "social", "dimension": "sundhed"},
    {"id": "gp_distance", "csv": "sundhed_extra_scores.csv", "ratio_col": "gp_distance_ratio", "raw_col": "gp_distance_km", "unit": "km", "data_year": "2024", "source": "DST SUNDAF01", "category": "social", "dimension": "sundhed"},
    {"id": "medicin", "csv": "medicin_scores.csv", "ratio_col": "medicin_ratio", "raw_col": "medicin_raw", "unit": "recepter/100 borgere", "data_year": "2024", "source": "DST MEDI1", "category": "social", "dimension": "sundhed"},
    {"id": "laegekontakt", "csv": "laegekontakt_scores.csv", "ratio_col": "laegekontakt_ratio", "raw_col": "laegekontakt_raw", "unit": "%", "data_year": "2024", "source": "DST SYGP1", "category": "social", "dimension": "sundhed"},
    {"id": "boerneovervaeght", "csv": "boerneovervaeght_scores.csv", "ratio_col": "boerneovervaeght_ratio", "raw_col": "boerneovervaeght_raw", "unit": "%", "data_year": "2018", "source": "DST LABY26", "category": "social", "dimension": "sundhed"},
    {"id": "hjemsyg", "csv": "hjemsyg_scores.csv", "ratio_col": "hjemsyg_ratio", "raw_col": "hjemsyg_raw", "unit": "pr. 1.000 indb.", "data_year": "2025", "source": "DST HJEMSYG", "category": "social", "dimension": "sundhed"},
    {"id": "wellbeing", "csv": "uvm_scores.csv", "ratio_col": "wellbeing_ratio", "raw_col": "wellbeing_score", "unit": "score (1-5)", "data_year": "2024", "source": "UVM GS/TRIV/TRIVIND", "category": "social", "dimension": "uddannelse"},

    # === Uddannelse ===
    {"id": "education", "csv": "doughnut_scores.csv", "ratio_col": "education_ratio", "raw_col": "education_raw", "unit": "%", "data_year": "2023", "source": "DST HFUDD10", "category": "social", "dimension": "uddannelse"},
    {"id": "low_education", "csv": "uddannelse_extra_scores.csv", "ratio_col": "low_education_ratio", "raw_col": "low_education_pct", "unit": "%", "data_year": "2023", "source": "DST HFUDD11", "category": "social", "dimension": "uddannelse"},
    {"id": "exam_grade", "csv": "uvm_scores.csv", "ratio_col": "exam_grade_ratio", "raw_col": "exam_grade_avg", "unit": "karakter", "data_year": "2024", "source": "UVM GS/KARA/KARAGNS", "category": "social", "dimension": "uddannelse"},
    {"id": "high_absence", "csv": "uvm_scores.csv", "ratio_col": "high_absence_ratio", "raw_col": "high_absence_pct", "unit": "%", "data_year": "2024", "source": "UVM GS/ELEVFRAV/FRAVAAR", "category": "social", "dimension": "uddannelse"},
    {"id": "youth_education", "csv": "uvm_scores.csv", "ratio_col": "youth_education_ratio", "raw_col": "youth_education_pct", "unit": "%", "data_year": "2024", "source": "UVM GS/PROFMOD/PROFMOD", "category": "social", "dimension": "uddannelse"},
    {"id": "apprenticeship", "csv": "uvm_scores.csv", "ratio_col": "apprenticeship_ratio", "raw_col": "apprenticeship_pct", "unit": "%", "data_year": "2024", "source": "UVM EUD/PRAK/SØG", "category": "social", "dimension": "uddannelse"},

    # === Velfærd ===
    {"id": "disposable_income", "csv": "doughnut_scores.csv", "ratio_col": "disposable_income_ratio", "raw_col": "disposable_income_raw", "unit": "kr./indb.", "data_year": "2022", "source": "DST INDKP101", "category": "social", "dimension": "velfaerd"},
    {"id": "employment", "csv": "doughnut_scores.csv", "ratio_col": "employment_ratio", "raw_col": "employment_raw", "unit": "%", "data_year": "2023", "source": "DST RAS200", "category": "social", "dimension": "velfaerd"},
    {"id": "child_poverty", "csv": "doughnut_scores.csv", "ratio_col": "child_poverty_ratio", "raw_col": "child_poverty_raw", "unit": "%", "data_year": "2022", "source": "DST LABY07", "category": "social", "dimension": "velfaerd"},
    {"id": "gini", "csv": "doughnut_scores.csv", "ratio_col": "gini_ratio", "raw_col": "gini_raw", "unit": "point", "data_year": "2022", "source": "DST IFOR41", "category": "social", "dimension": "lighed"},
    {"id": "low_income", "csv": "doughnut_scores.csv", "ratio_col": "low_income_ratio", "raw_col": "low_income_raw", "unit": "%", "data_year": "2022", "source": "DST LABY07", "category": "social", "dimension": "lighed"},
    {"id": "vulnerable_children", "csv": "velfaerd_extra_scores.csv", "ratio_col": "vulnerable_children_ratio", "raw_col": "vulnerable_children_pct", "unit": "%", "data_year": "2022", "source": "DST BU43", "category": "social", "dimension": "velfaerd"},
    {"id": "neet", "csv": "velfaerd_extra_scores.csv", "ratio_col": "neet_ratio", "raw_col": "neet_pct", "unit": "%", "data_year": "2022", "source": "DST NEET1", "category": "social", "dimension": "velfaerd"},
    {"id": "poverty_relative", "csv": "lighed_scores.csv", "ratio_col": "poverty_relative_ratio", "raw_col": "poverty_relative_pct", "unit": "%", "data_year": "2023", "source": "DST IFOR12P", "category": "social", "dimension": "velfaerd"},
    {"id": "child_notifications", "csv": "underretning_scores.csv", "ratio_col": "child_notifications_ratio", "raw_col": "child_notifications_per_1k", "unit": "pr. 1.000 indb. 0-17 år", "data_year": "2023", "source": "DST UND2", "category": "social", "dimension": "velfaerd"},

    # === Bolig ===
    {"id": "vacant_housing", "csv": "doughnut_scores.csv", "ratio_col": "vacant_housing_ratio", "raw_col": "vacant_housing_raw", "unit": "%", "data_year": "2023", "source": "DST BOL101", "category": "social", "dimension": "bolig"},
    {"id": "housing_area", "csv": "bolig_extra_scores.csv", "ratio_col": "housing_area_ratio", "raw_col": "housing_area_m2", "unit": "m²", "data_year": "2023", "source": "DST BOL106", "category": "social", "dimension": "bolig"},
    {"id": "housing_no_wc", "csv": "bolig_wc_scores.csv", "ratio_col": "housing_no_wc_ratio", "raw_col": "housing_no_wc_pct", "unit": "%", "data_year": "2023", "source": "DST BOL102", "category": "social", "dimension": "bolig"},
    {"id": "housing_no_bath", "csv": "bolig_wc_scores.csv", "ratio_col": "housing_no_bath_ratio", "raw_col": "housing_no_bath_pct", "unit": "%", "data_year": "2023", "source": "DST BOL102", "category": "social", "dimension": "bolig"},
    {"id": "bolig_fossil", "csv": "bolig_fossil_scores.csv", "ratio_col": "bolig_fossil_ratio", "raw_col": "bolig_fossil_raw", "unit": "%", "data_year": "2026", "source": "DST BOL202", "category": "social", "dimension": "bolig"},

    # === Demokrati ===
    {"id": "voter_turnout", "csv": "democracy_scores.csv", "ratio_col": "voter_turnout_ratio", "raw_col": "voter_turnout_pct", "unit": "%", "data_year": "2021", "source": "DST KVBPCT", "category": "social", "dimension": "demokrati"},
    {"id": "voter_turnout_national", "csv": "democracy_scores.csv", "ratio_col": "voter_turnout_national_ratio", "raw_col": "voter_turnout_national_pct", "unit": "%", "data_year": "2026", "source": "DST LABY09", "category": "social", "dimension": "demokrati"},
    {"id": "gender_leadership", "csv": "lighed_scores.csv", "ratio_col": "gender_leadership_ratio", "raw_col": "gender_leadership_pct", "unit": "% kvinder", "data_year": "2023", "source": "DST RAS301", "category": "social", "dimension": "ligestilling"},
    {"id": "le_gender_gap", "csv": "ligestilling_scores.csv", "ratio_col": "le_gender_gap_ratio", "raw_col": "le_gender_gap_years", "unit": "år (kønsgab)", "data_year": "2025", "source": "DST HISBK", "category": "social", "dimension": "ligestilling"},
    {"id": "income_gender_gap", "csv": "ligestilling_scores.csv", "ratio_col": "income_gender_gap_ratio", "raw_col": "income_gender_gap_pct", "unit": "% (kvinder/mænd)", "data_year": "2024", "source": "DST INDKP101", "category": "social", "dimension": "ligestilling"},
    {"id": "employment_origin_gap", "csv": "ligestilling_scores.csv", "ratio_col": "employment_origin_gap_ratio", "raw_col": "employment_origin_gap_pct", "unit": "% (ikkevestlig/dansk BFK)", "data_year": "2024", "source": "DST RAS200", "category": "social", "dimension": "lighed"},

    # === Kultur & fritid ===
    {"id": "music_school", "csv": "samskabelse_extra_scores.csv", "ratio_col": "music_school_ratio", "raw_col": "music_school_per_1k", "unit": "pr. 1.000 indb.", "data_year": "2022", "source": "DST SKOLM02B", "category": "social", "dimension": "kultur_fritid"},
    {"id": "library_use", "csv": "lokalsamfund_scores.csv", "ratio_col": "library_ratio", "raw_col": "library_loans_per_cap", "unit": "udlån/indb.", "data_year": "2023", "source": "DST BIB1", "category": "social", "dimension": "kultur_fritid"},
    {"id": "kultur_spending", "csv": "doughnut_scores.csv", "ratio_col": "kultur_spending_ratio", "raw_col": "kultur_spending_raw", "unit": "kr./indb.", "data_year": "2023", "source": "DST REGK31", "category": "social", "dimension": "kultur_fritid"},

    # === Tryghed ===
    {"id": "crime_rate", "csv": "faellesskaber_scores.csv", "ratio_col": "crime_ratio", "raw_col": "crime_per_1k", "unit": "pr. 1.000 indb.", "data_year": "2024", "source": "DST STRAF11", "category": "social", "dimension": "tryghed"},
    {"id": "traffic_accidents", "csv": "faellesskaber_scores.csv", "ratio_col": "traffic_accidents_ratio", "raw_col": "traffic_accidents_per_100k", "unit": "pr. 100.000 indb.", "data_year": "2024", "source": "DST UHELDK1", "category": "social", "dimension": "tryghed"},
    {"id": "sports_membership", "csv": "faellesskaber_scores.csv", "ratio_col": "sports_membership_ratio", "raw_col": "sports_membership_pct", "unit": "%", "data_year": "2022", "source": "DST IDRAKT02", "category": "social", "dimension": "lokalsamfund"},

    # === Lokalsamfund ===
    {"id": "sports_facilities", "csv": "lokalsamfund_scores.csv", "ratio_col": "facilities_ratio", "raw_col": "facilities_per_10k", "unit": "pr. 10.000 indb.", "data_year": "2022", "source": "DST IDRFAC01", "category": "social", "dimension": "lokalsamfund"},
    {"id": "class_size", "csv": "lokalsamfund_extra_scores.csv", "ratio_col": "class_size_ratio", "raw_col": "class_size", "unit": "elever/klasse", "data_year": "2023", "source": "DST KVOTIEN", "category": "social", "dimension": "uddannelse"},
    {"id": "daycare_ratio", "csv": "lokalsamfund_extra_scores.csv", "ratio_col": "daycare_ratio", "raw_col": "daycare_ratio_val", "unit": "børn/voksen", "data_year": "2022", "source": "DST BOERN8", "category": "social", "dimension": "uddannelse"},
    {"id": "sports_spending", "csv": "lokalsamfund_extra_scores.csv", "ratio_col": "sports_spending_ratio", "raw_col": "sports_spending_kr", "unit": "kr./indb.", "data_year": "2022", "source": "DST IDRFIN02", "category": "social", "dimension": "lokalsamfund"},
    {"id": "civil_society", "csv": "doughnut_scores.csv", "ratio_col": "civil_society_ratio", "raw_col": "civil_society_raw", "unit": "kr./indb.", "data_year": "2023", "source": "DST REGK31", "category": "social", "dimension": "lokalsamfund"},
    {"id": "educated_staff", "csv": "lokalsamfund_extra_scores.csv", "ratio_col": "educated_staff_ratio", "raw_col": "educated_staff_pct", "unit": "%", "data_year": "2024", "source": "DST BOERN1", "category": "social", "dimension": "uddannelse"},

    # === Mobilitet ===
    # NB: car_access er bevidst fjernet i 2026 - se shared.ts for begrundelse.
    {"id": "commute_distance", "csv": "mobilitet_scores.csv", "ratio_col": "commute_ratio", "raw_col": "commute_distance_km", "unit": "km", "data_year": "2023", "source": "DST AFSTB4", "category": "social", "dimension": "mobilitet"},
    {"id": "public_transport", "csv": "mobilitet_scores.csv", "ratio_col": "public_transport_ratio", "raw_col": "public_transport_pct", "unit": "%", "data_year": "2025", "source": "DST LABY49", "category": "social", "dimension": "mobilitet"},

    # === Klimatilpasning ===
    # Proxy: vejrrelaterede forsikringsskader pr. 1.000 indb. (F&P, 2023-2025).
    # Invers indikator: lavere skader = bedre score. Navn-nøgle som cba_2023_estimate.csv.
    # Se data/klimatilpasning.md for metodediskussion og fremtidige forbedringer.
    {"id": "vejr_skader", "csv": "klimatilpasning_scores.csv", "ratio_col": "vejr_skader_ratio", "raw_col": "vejr_skader_raw", "unit": "skader pr. 1.000 indb.", "data_year": "2023-2025", "source": "F&P skadesstatistik", "category": "social", "dimension": "klimatilpasning", "navn_key": True},
]

# ─── ØKOLOGISKE INDIKATORER (sub-indikatorer pr. dimension) ────────────
# Multi-indikator dimensioner (luftkvalitet, naeringsstoffer, cirkularitet)
# bruger worst-of-logik (max ratio) - planetary boundary-konvention.
#
# inverse_ratio=True betyder at ratio i CSV er "inverteret eco" hvor lav=værre.
# Vi konverterer: direct = 10000 / inverse, så høj=overshoot.
ECO_SUB_INDICATORS = [
    # === Klimapåvirkning (worst-of: territorial + forbrugsbaseret) ===
    {"id": "klimapaavirkning", "csv": "climate_scores.csv", "ratio_col": "climate_territorial_ratio", "raw_col": "co2e_per_capita", "unit": "ton CO₂e/person", "data_year": "2023", "source": "Klimaregnskabet.dk", "category": "ecological", "dimension": "klimapaavirkning", "inverse_ratio": False, "is_dimension_score": False},

    # === Luftkvalitet (worst-of NO2 + PM2.5) ===
    {"id": "luftkvalitet_no2", "csv": "luftforurening_scores.csv", "ratio_col": "no2_ratio", "raw_col": "no2_ug_m3", "unit": "µg/m³", "data_year": "2023", "source": "DCE/AU UBM via Miljøportal WFS", "category": "ecological", "dimension": "luftkvalitet", "inverse_ratio": False, "is_dimension_score": False},
    {"id": "luftkvalitet_pm25", "csv": "luftforurening_scores.csv", "ratio_col": "pm25_ratio", "raw_col": "pm25_ug_m3", "unit": "µg/m³", "data_year": "2023", "source": "DCE/AU UBM via Miljøportal WFS", "category": "ecological", "dimension": "luftkvalitet", "inverse_ratio": False, "is_dimension_score": False},

    # === Cirkularitet (worst-of genanvendelse + affald) ===
    # Genanvendelse: speciel logik - ratio = (65% EU-mål / faktisk) * 100 (high=undershoot)
    # Affald: inverse_ratio - lav score = mere affald = værre
    {"id": "cirkularitet_recycling", "csv": "consumption_scores.csv", "ratio_col": None, "raw_col": "recycling_pct", "unit": "%", "data_year": "2023", "source": "DST LABY25", "category": "ecological", "dimension": "cirkularitet", "inverse_ratio": False, "is_dimension_score": False, "special": "recycling_eu_target"},
    {"id": "cirkularitet_waste", "csv": "forurening_scores.csv", "ratio_col": "waste_ratio", "raw_col": "waste_kg_per_capita", "unit": "kg/person", "data_year": "2023", "source": "DST + MST", "category": "ecological", "dimension": "cirkularitet", "inverse_ratio": True, "is_dimension_score": False},

    # === Næringsstoffer (worst-of N + P + landbrug) ===
    {"id": "naer_nitrogen", "csv": "naeringsstoffer_scores.csv", "ratio_col": "nitrogen_ratio", "raw_col": "nitrogen_per_1000", "unit": "ton N/1.000 indb.", "data_year": "2024", "source": "DST VANDUD", "category": "ecological", "dimension": "naeringsstoffer", "inverse_ratio": True, "is_dimension_score": False},
    {"id": "naer_phosphorus", "csv": "naeringsstoffer_scores.csv", "ratio_col": "phosphorus_ratio", "raw_col": "phosphorus_per_1000", "unit": "ton P/1.000 indb.", "data_year": "2024", "source": "DST VANDUD", "category": "ecological", "dimension": "naeringsstoffer", "inverse_ratio": True, "is_dimension_score": False},
    {"id": "naer_landbrug", "csv": "n_landbrug_scores.csv", "ratio_col": "n_ratio", "raw_col": "n_ceiling_kg_per_ha", "unit": "kg N/ha", "data_year": "2025", "source": "Vandområdeplan 3", "category": "ecological", "dimension": "naeringsstoffer", "inverse_ratio": False, "is_dimension_score": False},
    # Effektmål: vandområdernes økologiske tilstand (VP3) = den synlige eutrofiering som N/P forårsager.
    # Andel af kommunens vandområder (vandløb+søer+kyst) i god tilstand, scoret mod landsgennemsnit
    # (ratio beregnet i fetch-scriptet, høj = værre). EU's 2027-mål vises som kontekst på metodesiden.
    {"id": "overfladevand", "csv": "vp3_vandkvalitet_scores.csv", "ratio_col": "vandkvalitet_ratio", "raw_col": "pct_god_tilstand", "unit": "%", "data_year": "2025", "source": "Vandområdeplan 3 (VP3 2e2025)", "category": "ecological", "dimension": "naeringsstoffer", "inverse_ratio": False, "is_dimension_score": False, "cap": 300},

    # === Biodiversitet (worst-of: væsentlig + uerstattelig naturværdi, DCE bioscore) ===
    # Kilde: DCE Biodiversitetskort (Bioscore-raster, AU/DCE SR456). Måler habitatkvalitet,
    # ikke rent arealdække. To tærskler matcher CONCITO/EU's biodiversitetsmål:
    #   ≥8  = "væsentlige naturværdier"   → mod 30%-målet (biodiversitet_ratio)
    #   ≥12 = "uerstattelige levesteder"  → mod 10%-målet (uerstattelig_ratio)
    {"id": "bio_vasentlig",    "csv": "biodiversitet_scores.csv", "ratio_col": "biodiversitet_ratio", "raw_col": "pct_vasentlig_natur",    "unit": "%", "data_year": "2021", "source": "DCE Biodiversitetskort (bioscore)", "category": "ecological", "dimension": "biodiversitet", "inverse_ratio": False, "is_dimension_score": False, "cap": 300},
    {"id": "bio_uerstattelig", "csv": "biodiversitet_scores.csv", "ratio_col": "uerstattelig_ratio", "raw_col": "pct_uerstattelig_natur", "unit": "%", "data_year": "2021", "source": "DCE Biodiversitetskort (bioscore)", "category": "ecological", "dimension": "biodiversitet", "inverse_ratio": False, "is_dimension_score": False, "cap": 300},

    # === Forbrugsbaseret CO2 (2. indikator under klimapaavirkning; navn-nøgle, ingen fallback) ===
    {"id": "forbrug_co2", "csv": "cba_2023_estimate.csv", "ratio_col": None, "raw_col": "cba_2023_estimate", "unit": "ton CO₂e/person", "data_year": "2023", "source": "Osei-Owusu et al. 2020 + ENS GA25", "category": "ecological", "dimension": "klimapaavirkning", "inverse_ratio": False, "is_dimension_score": False, "special": "cba_navn_key"},

    # === Forurening / Novel entities (single: pesticider i drikkevand) ===
    {"id": "pesticider", "csv": "pesticider_scores.csv", "ratio_col": "pesticid_ratio", "raw_col": "pesticid_pct_over_graense", "unit": "% boringer over 0.1 µg/l", "data_year": "2023", "source": "DN/GEUS Jupiter 2019-2023", "category": "ecological", "dimension": "forurening", "inverse_ratio": False, "is_dimension_score": True},
    # === Vand (worst-of: nitrat + vandindvinding) ===
    {"id": "nitrat", "csv": "nitrat_scores.csv", "ratio_col": "nitrat_ratio", "raw_col": "nitrat_mg_l", "unit": "mg/L", "data_year": "2025", "source": "Greenpeace/GEUS Jupiter 2025", "category": "ecological", "dimension": "vand", "inverse_ratio": False, "is_dimension_score": False},
    {"id": "vandindvinding", "csv": "vandindvinding_scores.csv", "ratio_col": "vandindvinding_ratio", "raw_col": "vandindvinding_m3_per_person", "unit": "m³/person", "data_year": "2024", "source": "DST VANDIND", "category": "ecological", "dimension": "vand", "inverse_ratio": False, "is_dimension_score": False},

    # === Arealanvendelse (worst-of: natur + intensivt landbrug + bebygget) ===
    # Kilde: DST AREALDK2 2024 (pct af kommunens matrikulerede areal)
    # natur_ratio    = (30% EU-maal / natur_pct) * 100  [lav natur = overshoot]
    # intensiv_ratio = (intensiv_pct / 54.7% nationalt snit) * 100  [meget landbrug = overshoot]
    # bebygget_ratio = (bebygget_pct / 14.2% nationalt snit) * 100  [meget by = overshoot]
    {"id": "areal_intensiv", "csv": "arealanvendelse_scores.csv", "ratio_col": "intensiv_ratio", "raw_col": "intensiv_pct", "unit": "%", "data_year": "2024", "source": "DST AREALDK2", "category": "ecological", "dimension": "arealanvendelse", "inverse_ratio": False, "is_dimension_score": False},
    {"id": "areal_bebygget", "csv": "arealanvendelse_scores.csv", "ratio_col": "bebygget_ratio", "raw_col": "bebygget_pct", "unit": "%", "data_year": "2024", "source": "DST AREALDK2", "category": "ecological", "dimension": "arealanvendelse", "inverse_ratio": False, "is_dimension_score": False},
]

# ─── HJÆLPEFUNKTIONER ──────────────────────────────────────────────────

def load_csv(filename):
    """Læs CSV til dict mapped på kommune_kode (eller første kolonne)."""
    path = DATA_DIR / filename
    if not path.exists():
        print(f"  ⚠ CSV mangler: {filename}", file=sys.stderr)
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_float(s):
    """Returnerer float eller None hvis tom/invalid."""
    if s is None or s == "":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def invert_to_direct_ratio(inverted):
    """Konverter inverse-eco-ratio til direct: 10000 / inverse.
    Lav inverse = høj forurening = værre → høj direct = overshoot."""
    if inverted is None or inverted == 0:
        return None
    return round(10000 / inverted, 2)


def recycling_eu_target_ratio(pct):
    """Speciel logik for genanvendelse: ratio = (65% EU-mål / faktisk) * 100.
    Over 100 = genanvender for lidt."""
    if pct is None or pct == 0:
        return None
    return round((65 / pct) * 100, 2)


def cba_ratio(estimate):
    """Forbrugs-CO2 ratio = (estimat / 3 ton grænse) * 100."""
    if estimate is None:
        return None
    return round((estimate / 3) * 100, 2)


def worst_of(ratios):
    """Worst-of (max) for ikke-None værdier. Planetary boundary-logik."""
    valid = [r for r in ratios if r is not None]
    return round(max(valid), 2) if valid else None


# ─── HOVEDLOGIK ────────────────────────────────────────────────────────

def build_master():
    print(f"Læser fra {DATA_DIR}")
    print()

    # Få liste af alle 98 kommuner fra hoved-CSV
    main_rows = load_csv("doughnut_scores.csv")
    if not main_rows:
        print("FEJL: doughnut_scores.csv mangler eller er tom", file=sys.stderr)
        sys.exit(1)

    kommuner = [(r["kommune_kode"], r.get("kommune_navn", "")) for r in main_rows]
    print(f"Fundet {len(kommuner)} kommuner")
    print()

    # Cache CSV-loads (undgå at læse samme fil 5 gange)
    csv_cache = {}
    def get_csv(filename):
        if filename not in csv_cache:
            csv_cache[filename] = load_csv(filename)
        return csv_cache[filename]

    # Output-rækker
    output_rows = []

    # Tæller for diagnostik
    indicator_coverage = {}

    # ─── Sociale indikatorer ────────────────────────────────────
    print("Sociale indikatorer:")
    for ind in SOCIAL_INDICATORS:
        rows = get_csv(ind["csv"])

        # Specialcase: indikatorer der bruger kommunenavn som nøgle (ikke kode)
        if ind.get("navn_key"):
            by_navn = {r.get("kommune_navn"): r for r in rows if r.get("kommune_navn")}
            n = 0
            for kode, navn in kommuner:
                r = by_navn.get(navn)
                if r is None:
                    continue
                ratio = parse_float(r.get(ind["ratio_col"]))
                raw = parse_float(r.get(ind["raw_col"])) if ind["raw_col"] else None
                if ratio is None and raw is None:
                    continue
                output_rows.append({
                    "kommune_kode": kode,
                    "kommune_navn": navn,
                    "indicator_id": ind["id"],
                    "ratio": ratio if ratio is not None else "",
                    "raw_value": raw if raw is not None else "",
                    "unit": ind["unit"],
                    "data_year": ind["data_year"],
                    "source": ind["source"],
                    "category": ind["category"],
                    "dimension": ind["dimension"],
                })
                n += 1
            indicator_coverage[ind["id"]] = n
            print(f"  {ind['id']:25s}: {n}/98 kommuner (navn-nøgle)")
            continue

        # Standard: kommune_kode-nøgle
        by_kode = {}
        for r in rows:
            kode = r.get("kommune_kode")
            if kode and kode not in by_kode:
                by_kode[kode] = r

        n = 0
        for kode, navn in kommuner:
            r = by_kode.get(kode)
            if r is None:
                continue
            ratio = parse_float(r.get(ind["ratio_col"]))
            # Cap alle sociale ratios ved 150 for at undgå ekstreme inverse-værdier
            if ratio is not None and ratio > 150:
                ratio = 150.0
            raw = parse_float(r.get(ind["raw_col"])) if ind["raw_col"] else None
            if ratio is None and raw is None:
                continue
            output_rows.append({
                "kommune_kode": kode,
                "kommune_navn": navn,
                "indicator_id": ind["id"],
                "ratio": ratio if ratio is not None else "",
                "raw_value": raw if raw is not None else "",
                "unit": ind["unit"],
                "data_year": ind["data_year"],
                "source": ind["source"],
                "category": ind["category"],
                "dimension": ind["dimension"],
            })
            n += 1
        indicator_coverage[ind["id"]] = n
        print(f"  {ind['id']:25s}: {n}/98 kommuner")

    # ─── Økologiske sub-indikatorer ──────────────────────────────
    print()
    print("Økologiske sub-indikatorer:")
    # Saml sub-ratios pr. dimension for at beregne worst-of dimension-scores
    eco_sub_ratios = {}  # {kommune_kode: {dimension: [ratios]}}

    for ind in ECO_SUB_INDICATORS:
        rows = get_csv(ind["csv"])

        # Specialcase: cba bruger navn-nøgle, ikke kommune_kode
        if ind.get("special") == "cba_navn_key":
            by_navn = {r.get("kommune"): r for r in rows if r.get("kommune")}
            n = 0
            for kode, navn in kommuner:
                r = by_navn.get(navn)
                if r is None:
                    continue
                raw = parse_float(r.get(ind["raw_col"]))
                if raw is None:
                    continue
                ratio = cba_ratio(raw)
                output_rows.append({
                    "kommune_kode": kode,
                    "kommune_navn": navn,
                    "indicator_id": ind["id"],
                    "ratio": ratio if ratio is not None else "",
                    "raw_value": raw,
                    "unit": ind["unit"],
                    "data_year": ind["data_year"],
                    "source": ind["source"],
                    "category": ind["category"],
                    "dimension": ind["dimension"],
                })
                eco_sub_ratios.setdefault(kode, {}).setdefault(ind["dimension"], []).append(ratio)
                n += 1
            indicator_coverage[ind["id"]] = n
            print(f"  {ind['id']:25s}: {n}/98 kommuner (navn-nøgle)")
            continue

        # Standard: kommune_kode-nøgle
        by_kode = {}
        for r in rows:
            kode = r.get("kommune_kode")
            if kode and kode not in by_kode:
                by_kode[kode] = r

        n = 0
        for kode, navn in kommuner:
            r = by_kode.get(kode)
            if r is None:
                continue

            raw = parse_float(r.get(ind["raw_col"])) if ind["raw_col"] else None

            # Beregn ratio efter speciallogik
            if ind.get("special") == "recycling_eu_target":
                ratio = recycling_eu_target_ratio(raw)
            else:
                csv_ratio = parse_float(r.get(ind["ratio_col"])) if ind["ratio_col"] else None
                if ind.get("inverse_ratio") and csv_ratio is not None:
                    ratio = invert_to_direct_ratio(csv_ratio)
                else:
                    ratio = csv_ratio

            # Cap ekstreme eco-ratioer (fx bioscore med pct nær 0 giver ratio i tusinder).
            # Baren klipper alligevel ved 200; cap holder det viste tal og validering pæn.
            cap = ind.get("cap")
            if cap is not None and ratio is not None and ratio > cap:
                ratio = float(cap)

            if ratio is None and raw is None:
                continue

            output_rows.append({
                "kommune_kode": kode,
                "kommune_navn": navn,
                "indicator_id": ind["id"],
                "ratio": ratio if ratio is not None else "",
                "raw_value": raw if raw is not None else "",
                "unit": ind["unit"],
                "data_year": ind["data_year"],
                "source": ind["source"],
                "category": ind["category"],
                "dimension": ind["dimension"],
            })
            if ratio is not None:
                eco_sub_ratios.setdefault(kode, {}).setdefault(ind["dimension"], []).append(ratio)
            n += 1
        indicator_coverage[ind["id"]] = n
        print(f"  {ind['id']:25s}: {n}/98 kommuner")

    # ─── Worst-of dimension-aggregater ───────────────────────────
    # Skriv én række pr. (kommune, dimension) med dimension-score = worst-of
    # Bruges af webapp som eco_ratios[dimension].
    # Single-indicator dims (klimapaavirkning, biodiversitet, forbrug_co2) får dimension-score
    # = sub-indikatorens ratio. Multi-indicator dims (luftkvalitet, naeringsstoffer, cirkularitet)
    # får worst-of.
    print()
    print("Dimension-aggregater (worst-of):")
    dim_count = 0
    for kode, navn in kommuner:
        dims_for_kommune = eco_sub_ratios.get(kode, {})
        for dim, ratios in dims_for_kommune.items():
            score = worst_of(ratios)
            if score is None:
                continue
            output_rows.append({
                "kommune_kode": kode,
                "kommune_navn": navn,
                "indicator_id": f"_dim_{dim}",
                "ratio": score,
                "raw_value": "",
                "unit": "",
                "data_year": "",
                "source": "",
                "category": "ecological_dimension",
                "dimension": dim,
            })
            dim_count += 1
    print(f"  {dim_count} dimension-aggregat-rækker")

    # ─── Validering ──────────────────────────────────────────────
    print()
    print("Validering:")
    bad_ratios = [r for r in output_rows if r["ratio"] != "" and (float(r["ratio"]) < 0 or float(r["ratio"]) > 2000)]
    if bad_ratios:
        print(f"  ⚠ {len(bad_ratios)} ratio-værdier uden for forventet interval (0-2000)")
        for r in bad_ratios[:5]:
            print(f"     {r['kommune_navn']} / {r['indicator_id']}: ratio={r['ratio']}")
    else:
        print("  ✓ Alle ratios inden for forventet interval")

    kommuner_med_data = len({r["kommune_kode"] for r in output_rows})
    print(f"  Kommuner med mindst én indikator: {kommuner_med_data}/{len(kommuner)}")

    # ─── Skriv output ────────────────────────────────────────────
    fieldnames = ["kommune_kode", "kommune_navn", "indicator_id", "ratio",
                  "raw_value", "unit", "data_year", "source", "category", "dimension"]
    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(output_rows)

    print()
    print(f"✓ Skrev {len(output_rows)} rækker til {OUTPUT.relative_to(ROOT)}")
    print(f"  Filstørrelse: {OUTPUT.stat().st_size / 1024:.1f} KB")


def auto_build_master():
    """
    Helper-funktion til auto-rebuild fra fetch-scripts.

    Kaldes til sidst i alle fetch_*.py-scripts så master-CSV'en altid
    er opdateret efter en fetch. Isolerer fejl så build-problemer ikke
    crash'er det kaldende fetch-script (rådata er allerede gemt).

    Brug i fetch-scripts:
        from build_master_csv import auto_build_master
        # ... fetch-logik ...
        auto_build_master()
    """
    print()
    print("=" * 55)
    print("AUTO-REBUILD af master_indicators.csv")
    print("=" * 55)
    try:
        build_master()
        print()
        print("✓ Master-CSV opdateret. Klar til commit + push via GitHub Desktop.")
    except Exception as e:
        print()
        print(f"✗ FEJL ved rebuild af master-CSV: {e}")
        print("  Rådata-CSV er gemt OK. Kør manuelt: python3 scripts/build_master_csv.py")
        # Vi raise IKKE - rådata er gemt og det er det vigtigste


if __name__ == "__main__":
    build_master()
