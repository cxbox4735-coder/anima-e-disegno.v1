[app]
title = DisegnaAnima
package.name = anima_e_disegno
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,json
version = 1.0
requirements = python3,pygame,pillow,cython,setuptools,wheel
orientation = portrait
fullscreen = 1
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.arch = armeabi-v7a,arm64-v8a
p4a.bootstrap = sdl2
android.entrypoint = org.kivy.android.PythonActivity
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1
