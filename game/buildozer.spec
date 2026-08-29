[app]

title = Disegna e Anima Pro
package.name = disegnaanima
package.domain = org.tuo.nome
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
source.main = main.py

version = 1.1

requirements = hostpython3==3.11.9,python3==3.11.9,cython==0.29.37,pygame-ce,sdl2,android

orientation = landscape
fullscreen = 1

android.api = 34
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

# Solo INTERNET (se vuoi aggiungere storage per esportare in Galleria, decommenta sotto)
android.permissions = INTERNET

# android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.presplash_color = #12121A
source.exclude_dirs = bin,build,__pycache__,.git,export_*

[buildozer]
log_level = 2
warn_on_root = 0
