[app]

title = Disegna e Anima Pro
package.name = disegnaanima
package.domain = org.tuo.nome
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt

version = 1.0

# PYTHON 3.11.9 + CYTHON 0.29.37 = COMBINAZIONE STABILE TESTATA
requirements = hostpython3==3.11.9,python3==3.11.9,cython==0.29.37,pygame-ce

orientation = landscape
fullscreen = 1

android.api = 34
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

p4a.local_recipes = ./p4a-recipes

[buildozer]
log_level = 2
warn_on_root = 0
