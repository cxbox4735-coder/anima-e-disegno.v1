[app]
title = DisegnaAnima
package.name = anima_e_disegno
package.domain = org.example
source.dir = .
source.include_exts = py, png, jpg, json
version = 1.0

# requirements: aggiunti cython/setuptools/wheel che spesso servono in build
requirements = python3, pygame, pillow, cython, setuptools, wheel

# bootstrap & Android settings (adatta se necessario)
p4a.bootstrap = sdl2
android.api = 33
android.ndk = 25b
android.ndk_api = 21
android.arch = armeabi-v7a, arm64-v8a
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1
