[app]

# (str) Title of your application
title = DisegnaAnima

# (str) Package name
package.name = anima_e_disegno

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,json,kv,atlas

# (str) Application versioning
version = 1.0

# (list) Application requirements - QUESTO È IMPORTANTE!
# Non mettere spazi dopo le virgole, includi SDL2
requirements = python3,pygame,pillow,cython,setuptools,wheel,jnius,sdl2,sdl2_image,sdl2_mixer,sdl2_ttf,png,jpeg

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# Android specific

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 31

# (str) Android NDK version to use
android.ndk = 21b

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = arm64-v8a

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (str) Android logcat filters
android.logcat_filters = *:S python:D

# (str) python-for-android branch to use, defaults to master
p4a.branch = master

#
# iOS specific
#

ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.7.0

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
