[app]
title = DisegnaAnima
package.name = anima_e_disegno
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,json,kv,atlas
version = 1.0
requirements = python3,pygame,pillow,cython,setuptools,wheel,jnius,sdl2,sdl2_image,sdl2_mixer,sdl2_ttf,png,jpeg
orientation = portrait
fullscreen = 1
android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 21b
android.arch = arm64-v8a
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.logcat_filters = *:S python:D
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
