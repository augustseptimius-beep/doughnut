## Beregning

Worst-of af to indikatorer: (1) NO2-koncentration (kvælstofdioxid, µg/m³ årsgennemsnit) og (2) PM2.5-koncentration (fine partikler, µg/m³ årsgennemsnit). Begge sammenholdes med WHO's retningslinjer fra 2021. Ratio = (kommunens koncentration / WHO-grænse) × 100. Ratio over 100 = over WHO-grænsen. Dimensionens samlede score er den højeste (værste) af de to sub-indikatorer - planetary boundary-logik: hvis bare én grænse er overskredet, er dimensionen overskredet. Beregnet som befolkningsvægtet gennemsnit af 1×1 km modelceller inden for kommunegrænsen via spatial join.

## Grænseværdi

WHO 2021 Air Quality Guidelines (årsgennemsnit): NO2 = 10 µg/m³, PM2.5 = 5 µg/m³. WHO-grænsen er valgt frem for EU's grænseværdier (NO2: 40 µg/m³, PM2.5: 25 µg/m³) fordi WHO-grænsen er videnskabeligt baseret på sundhedseffekter, mens EU-grænsen er et politisk kompromis.

## Begrænsninger

Modelberegnet baggrundskoncentration (UBM, 1×1 km grid) - ikke målte værdier. Fanger ikke lokale hotspots ved travle gadestrækninger (OSPM-model dækker dette, men kun i store byer). Kommunegennemsnittet inkluderer landlige arealer med lav forurening, hvilket trækker byernes reelle eksponering ned. PM2.5 i Danmark er i høj grad påvirket af langtransport fra kontinentet og hav - ikke kun lokale kilder.

## Datafil

`luftforurening_scores.csv`
