# Hand Gesture Recognition
Hand Gestureを用いた家電操作アプリです。

## 使用したネットワーク
このアプリケーションで使用したネットワークについて解説する。  
YOLOv3をベースにCPUやモバイルハードウェアなどで高速で実行できるようにアーキテクチャを改善した。  
YOLOv3は物体検出に有用となる特徴量を抽出するBackboneと、Backboneで得られた特徴量を基に物体を検出するHeadに分けられる。

YOLOv3の公式実装は以下のようになる。  
Backbone : Darknet53  
Head : Standard Convolution

これらを以下のように変更したネットワークを提案する。  
Backbone : **MobileNetV3-Small**  
Head : **Depthwise Separable Convolution**

提案したネットワークを**M**obile**N**etV3-**S**mall **Y**OLOv3を省略し**MNSY**と呼称する。

## MNSYの有効性
MNSYと代表的なネットワークの比較を以下に示す。  
mAPに関してはCOCO mAPを使用し、学習データはCreative Senz3d Dataset及び自前で集めた画像、合計33,000枚を用いた。速度計測にはCPUにCore i9-8950HK、OpenVINOのIRモデルを使用した。

|Model|Params|Model Size|mAP|Inference Speed|
|:---|:---|:---|:---|:---|
|Tiny-YOLOv3|8.7M|33.2MB|81.26|41.84fps|
|MobileNetV3+SSDLite|**1.5M**|**6.0MB**|75.04|**193.94fps**|
|MNSY|2.4M|9.2MB|**84.75**|107.06fps|

MNSYはパラーメータ数、モデルサイズ、精度、速度のすべてでTiny-YOLOv3を上回っている。  
SSDLiteはMNSYと比べて高速で実行可能であるが、精度が著しく下がっている。  
以上のことから、MNSYは速度と精度の両立を実現したネットワークであり、様々な用途での応用が期待できる。


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