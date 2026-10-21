## Generelt om scoring

Platformen bruger to forskellige scoringskonventioner:

**Socialt fundament:** Score 100 = landsgennemsnit. Over 100 er bedre end gennemsnit (grønt), under 100 er dårligere (rødt). Røde segmenter i den indre ring viser "shortfall" - kommunen lever ikke op til det sociale minimum.

**Økologisk loft:** Score 100 = grænseværdi. Under 100 er godt (inden for grænsen), over 100 er "overshoot" (rødt). Røde segmenter i den ydre ring viser overskridelse af den planetære grænse.

**Vægtning:** Hver kategori (f.eks. Sundhed, Velfærd, Bolig) beregnes som et simpelt gennemsnit af sine indikatorer. Det samlede sociale gennemsnit er et gennemsnit af kategorierne - ikke af de individuelle indikatorer. Det betyder at kategorier med få indikatorer (f.eks. Bolig med 3) vægter lige så tungt som kategorier med mange (f.eks. Velfærd med 6). Dette er et bevidst valg: hver dimension i doughnut-modellen anses for lige vigtig, uanset hvor mange indikatorer der måler den.

**Inverterede indikatorer:** For indikatorer hvor lavere er bedre (f.eks. kriminalitet, affald, børnefattigdom) beregnes ratioen inverteret: (landsgennemsnit / kommune) × 100, så højere ratio fortsat betyder bedre performance. Kommuner med en værdi på 0 (typisk manglende data eller ingen registreret aktivitet) sættes til ratio 0, ikke perfekt score - dette er for at undgå at databrist fejlagtigt fremstår som topscore. For multi-indikator økologiske dimensioner (luftkvalitet, næringsstoffer, forurening) bruges en specialregel: ratio 150 anvendes som loft for sub-indikatorer hvor data mangler eller hvor ingen aktivitet registreres (f.eks. kommuner uden markblokke i N-loft-beregningen).
