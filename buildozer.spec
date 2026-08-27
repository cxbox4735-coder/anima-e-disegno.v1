[app]
title = DisegnaAnima
package.name = anima_e_disegno
package.domain = org.example
source.dir = .
source.include_exts = py, png, jpg, json
version = 1.0
requirements = python3, pygame, pillow
orientation = portrait
android.arch = armeabi-v7a, arm64-v8a
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
