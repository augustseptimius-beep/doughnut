#!/bin/bash
cd "$(dirname "$0")/webapp"
echo "Starter udviklingsserver..."
echo "(Browseren åbner automatisk om ca. 20 sekunder)"
(sleep 20 && open http://localhost:3000) &
npm run dev
