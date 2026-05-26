[app]
title = Smart Khata
package.name = smartkhata
package.domain = org.diary
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3, kivy, sqlite3, reportlab

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1

p4a.local_recipes = 
p4a.hook = 
p4a.bootstrap = sdl2
