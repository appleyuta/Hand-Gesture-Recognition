from kivy.uix.screenmanager import Screen
from yolo import yolo_obj
#from yolo_tflite import yolo_obj
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from customclass.msgpopup import MessagePopup
from serial_device import ir_serial
import threading

flgPlay = False
#flgFace = False
#flgMosaic = False
import cv2

class ExecuteScreen(Screen):
    def __init__(self,**kwargs):
        super(ExecuteScreen,self).__init__(**kwargs)
        image_texture = Texture.create(size=(600, 400), colorfmt='bgr')
        self.ids['camera'].texture = image_texture
    def build(self):
        pass
    
    def play(self):
        global flgPlay
        flgPlay = not flgPlay
        if flgPlay == True:
            if ir_serial == None:
                MessagePopup("警告","irMagicianが接続されていないか、認識されていません。\nデバイスを再接続してからアプリを再起動してください。",size_hint=(0.7,0.7)).popup_open()
            self.ids.btn.text = 'Stop'
            self.image_capture = cv2.VideoCapture(0)
            ret, frame = self.image_capture.read()
            yolo_obj.network_setting(ret,frame)
            Clock.schedule_interval(self.update, 1.0 / 60.0)
        else:
            self.ids.btn.text = 'Play'
            Clock.unschedule(self.update)
            self.image_capture.release()
    
    def update(self, dt):
        ret, frame = self.image_capture.read()
        cap_w = self.image_capture.get(3)
        cap_h = self.image_capture.get(4)
        if hasattr(yolo_obj,"exec_net"):
            if ret and yolo_obj.exec_net.requests[0].wait(-1) == 0:
                frame = yolo_obj.exec_predict(ret,frame,cap_h,cap_w)
                # カメラ映像を上下反転
                buf = cv2.flip(frame, 0)
                image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                image_texture.blit_buffer(buf.tobytes(), colorfmt='bgr', bufferfmt='ubyte')
                camera = self.ids['camera']
                camera.texture = image_texture
        else:
            if ret:
                frame = yolo_obj.exec_predict(ret,frame,cap_h,cap_w)
                # カメラ映像を上下反転
                buf = cv2.flip(frame, 0)
                image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                image_texture.blit_buffer(buf.tobytes(), colorfmt='bgr', bufferfmt='ubyte')
                camera = self.ids['camera']
                camera.texture = image_texture