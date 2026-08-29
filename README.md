# Disegna & Anima Pro

App di disegno e animazione con stickman, ottimizzata per Android.

## Build automatica su GitHub

1. Carica tutti i file su un repository GitHub
2. Vai su **Actions** → **Build Android APK**
3. Clicca **Run workflow**
4. Attendi ~20-40 minuti (la prima build scarica NDK/SDK)
5. Scarica l'APK dagli **Artifacts**

## Build locale (opzionale)

```bash
pip install buildozer cython
buildozer android debug
