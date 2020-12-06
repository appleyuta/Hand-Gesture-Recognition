# Hand Gesture Recognition
Hand Gestureを用いた家電操作アプリです。

## デモ
guiapp.pyの実行デモ

![result](https://github.com/appleyuta/Hand-Gesture-Recognition/blob/main/demo.gif)

## 使用方法
アプリケーションは2種類用意されています。
1. guiapp.py
   - tkinterで開発されたアプリ
2. Kivy_guiapp.py
   - Kivyで開発されたアプリ

python guiapp.pyのように実行できます。

## 必要なライブラリ
Windowsで実行する場合はrequirements_windows.txtに書かれたライブラリが必要です。  
それ以外のOSでの実行にはrequirements.txtに書かれたライブラリが必要です。  
requirements.txtに書かれたライブラリの他にOpenVINOの実行環境が必要です。

## Windowsにおけるdecodeエラー対処
WindowsでKivyを実行する際に下記のエラーが出る場合があります。

UnicodeDecodeError: 'cp932' codec can't decode byte 0x83 in position 1478: illegal multibyte sequence

### 対処法
site-packages/kivy/lang/builder.pyの288行目を以下のように書き換え

修正前
`with open(filename, 'r') as fd:  
    kwargs['filename'] = filename  
    data = fd.read()`

修正後
`with open(filename, 'r', encoding='utf8') as fd:  
    kwargs['filename'] = filename  
    data = fd.read()`