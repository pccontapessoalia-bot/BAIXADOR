[app]

title = Baixador de Links
package.name = baixador
package.domain = org.baixador
source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,svg,ttf
version = 1.0
version.name = 1.0
version.code = 2
requirements = python3,kivy,yt-dlp,plyer,requests,certifi
orientation = portrait
osx.package_name = Baixador de Links
presplash.color = #7C5CFC
presplash = presplash.png
icon = app_icon.png

[buildozer]

log_level = 2
warn_on_root = 1

[android]

android.api = 33
android.minapi = 21
android.ndk = 25c
android.sdk = 33
android.build_tools = 33.0.2
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO
android.arch = arm64-v8a
android.ffmpeg = True
android.enable_androidx = True
android.storage = auto
android.accept_sdk_license = True
android.gradle_dependencies = androidx.core:core:1.9.0

