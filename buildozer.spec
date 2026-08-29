[app]

# Titolo visibile nell'app drawer
title = Disegna e Anima Pro

# Nome pacchetto (senza spazi)
package.name = disegnaeanima

# Dominio inverso
package.domain = org.disegnaanima

# Versione
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,mp3,wav,ogg,json

# Versione
version = 1.0

# Requisiti: pygame è essenziale
requirements = python3,pygame

# Orientamento (landscape va bene per disegnare)
orientation = landscape

# Icona (opzionale, se ne hai una mettila nella root)
# icon.filename = %(source.dir)s/icona.png

# Permessi Android necessari
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# API Android
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b

# Fullscreen su Android
android.presplash_color = #12121a
android.window_animation = None

[buildozer]

# Log level
log_level = 2

# Directory di build
build_dir = ./.buildozer

# Bin output
bin_dir = ./bin
