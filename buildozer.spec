[app]
title = POS Sistema
package.name = possistema
package.domain = org.possistema
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db,json
version = 1.0
requirements = python3,kivy==2.3.0,sqlite3,pillow
orientation = landscape
fullscreen = 0
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
