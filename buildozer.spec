[app]
title = PdfLoader
package.name = attestation
package.domain = io.jihashtag
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,pdf
version = 0.8
requirements = python3,Cython,android,geopy,kivy,plyer,pypdf2,pillow,jnius,qrcode[pil]
icon.filename = logo_jiha.png
orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.arch = armeabi-v7a
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = masterios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.7.0[buildozer]
log_level = 2
warn_on_root = 1
