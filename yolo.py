from postprocess_np import yolo3_postprocess_np #YOLOv3出力の整形
import cv2
from openvino.inference_engine import IENetwork, IEPlugin
import numpy as np
import time
import tkinter as tk
from PIL import Image,ImageTk
import sqlite3
import threading

from serial_device import ir_serial #irMagicianとの通信用


#IoU計算関数
def intersection_over_union(box_1, box_2):
    width_of_overlap_area = min(box_1[2], box_2[2]) - max(box_1[0], box_2[0])
    height_of_overlap_area = min(box_1[3], box_2[3]) - max(box_1[1], box_2[1])
    if width_of_overlap_area < 0 or height_of_overlap_area < 0:
        area_of_overlap = 0
    else:
        area_of_overlap = width_of_overlap_area * height_of_overlap_area
    box_1_area = (box_1[3] - box_1[1]) * (box_1[2] - box_1[0])
    box_2_area = (box_2[3] - box_2[1]) * (box_2[2] - box_2[0])
    area_of_union = box_1_area + box_2_area - area_of_overlap
    if area_of_union == 0:
        return 0
    return area_of_overlap / area_of_union

#class_idをラベルに変換する辞書
idx2label = {0:"zero",1:"one",2:"two",3:"three",4:"four",5:"five",6:"three_v2",7:"fit",8:"fox",9:"ok",10:"go",11:"little_finger"}
anchors = [151,288, 171,191, 209,296, 105,90, 120,136, 126,181, 68,101, 86,129, 98,162]#mnsy
#anchors = [72,79, 93,159, 96,106, 56,68, 56,47, 70,105, 37,55, 45,75, 56,90]#mnsy224
anchors = np.array(anchors).reshape(-1, 2)

#YOLOv3でジェスチャを認識するクラス
class YOLO:
    def __init__(self,use_device):
        self.plugin_dir = None
        self.plugin = IEPlugin(use_device,plugin_dirs=self.plugin_dir)
        self.model_xml = "./weights/mnsy.xml"
        self.model_bin = "./weights/mnsy.bin"
        self.net = IENetwork(model=self.model_xml,weights=self.model_bin)
        self.exec_net = self.plugin.load(network=self.net)
        self.cnt = 0 #stopジェスチャのカウント

        self.stop = False #動作停止flag
        self.checker = None #画面更新flag
        
        self.before_data = None #1つ前のデータを保持
        self.start_point_x = None #ジェスチャの開始座標
        self.start_point_y = None #ジェスチャの開始座標
        self.detected_data = [] #過去のデータを保持するリスト
        self.detect_class = np.empty(0) #median値を計算するための配列
        self.exec_f = None #実行フレームへのアクセス変数

        self.count = 0 #ジェスチャ時間閾値
        self.y_start2end_count = None #ジェスチャ開始からのフレーム待機時間
        self.x_start2end_count = None #ジェスチャ開始からのフレーム待機時間

        self.end_point_x = None #ジェスチャの終了座標
        self.end_point_y = None #ジェスチャの終了座標
        
        self.preview = None
        self.preview_frame = None
        self.image_texture = None
        self.detect_gesture_name = ""
        self.frame_counter = 0

    def set_exec_f(self,exec_f):
        self.exec_f = exec_f #ExecuteFrame
    
    def setCameraPreview(self,preview):
        self.preview = preview


    #モデルを実行してジェスチャ検出(tkinter用)
    def exec_model(self):
        input_blob = next(iter(self.net.inputs))  #input_blob = 'data'
        out_blob   = next(iter(self.net.outputs)) #out_blob   = 'detection_out'
        model_n, model_c, model_h, model_w = self.net.inputs[input_blob].shape

        color = (0,255,0)
        #time_stamp = time.time()
        cap = cv2.VideoCapture(0)
        cap_w = cap.get(3)
        cap_h = cap.get(4)
        time_stamp = 0
        start_flag_x = 0
        start_flag_y = 0
        end_flag_y = 0
        speed_count = 0#仮
        speed_sum = 0#仮
        while cap.isOpened():
            ret, frame = cap.read()
            #左右反転(鏡)
            frame = cv2.flip(frame,1)
            if not ret:
                break

            #STEP-6
            in_frame = cv2.resize(frame, (model_w, model_h))
            in_frame = cv2.cvtColor(in_frame,cv2.COLOR_BGR2RGB)
            in_frame = cv2.normalize(in_frame,None,alpha=0,beta=1,norm_type=cv2.NORM_MINMAX,dtype=cv2.CV_32F)
            in_frame = in_frame.transpose((2, 0, 1))  # Change data layout from HWC to CHW
            in_frame = in_frame.reshape((model_n, model_c, model_h, model_w))

            #STEP-7
            self.exec_net.start_async(request_id=0, inputs={input_blob: in_frame})

            t = 0
            start_time = time.time()
            if self.exec_net.requests[0].wait(-1) == 0:
                result = self.exec_net.requests[0].outputs
                #time.sleep(0.07)

                current_time = time.time()
                #tは実行にかかった時間(速度計算に使用)
                t = current_time - start_time
                speed_count += 1
                speed_sum += t
                out_list = []
                for out_blob in result.values():
                    out_blob = out_blob.transpose(0,2,3,1)
                    #print(out_blob.shape)
                    out_list.append(out_blob)
                    
                objects = yolo3_postprocess_np(out_list,(cap_h,cap_w),anchors,12,(model_h,model_w),confidence=0.1)
                iou_threshold = 0.1
                for i in range(len(objects[0])):
                    if objects[3][i] == 0:
                        continue
                    for j in range(i + 1, len(objects[0])):
                        if intersection_over_union(objects[1][i], objects[1][j]) > iou_threshold:
                            objects[3][j] = 0
                velocity_x = 0
                velocity_y = 0
                for i in range(len(objects[0])):
                    if objects[3][i] > 0.3:
                        #print(objects)
                        x_center = objects[0][i][0]
                        y_center = objects[0][i][1]
                        class_id = objects[2][i]
                        if self.detect_class.__len__() == 9:
                            #class_idのmedianを計算して検出クラスを安定させる
                            median_class_id = np.median(self.detect_class)
                            frame = cv2.rectangle(frame,(objects[1][i][0],objects[1][i][1]),(objects[1][i][2],objects[1][i][3]),(0,255,0),3)
                            frame = cv2.putText(frame,idx2label[median_class_id],(objects[1][i][0]-3,objects[1][i][1]-3), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255),3)
                            frame = cv2.line(frame,(x_center,y_center),(x_center+1,y_center+1),(0,255,0),3)
                            time_stamp = time.time()
                            
                            if self.before_data != None and t != 0:
                                #速度を計算
                                velocity_x = (self.before_data[0]-x_center)/t
                                velocity_y = (self.before_data[1]-y_center)/t
                                #print(velocity_y)

                            if self.start_point_x == None and self.cnt > 5:
                                start_flag_x = 1
                            
                            if self.start_point_y == None and self.cnt > 5:
                                start_flag_y = 1
                            
                            if start_flag_x >= 1:
                                start_flag_x += 1
                            
                            #カウント6以上でリセット
                            if start_flag_x > 5:
                                start_flag_x = 0
                                self.start_point_x = None
                                #print("reset x")
                            
                            if start_flag_y >= 1:
                                start_flag_y += 1
                            
                            #カウント6以上でリセット
                            if start_flag_y > 5:
                                start_flag_y = 0
                                self.start_point_y = None
                                #print("reset y")
                            
                            if start_flag_x >= 1 and abs(velocity_x) > 900:
                                self.start_point_x = (x_center,velocity_x,median_class_id)
                                self.x_start2end_count = 0
                                start_flag_x = 0
                                self.cnt = 0
                            #ジェスチャ開始後、数フレームの間待機する
                            if self.x_start2end_count != None:
                                self.x_start2end_count += 1
                            
                            if self.start_point_x != None and self.end_point_x == None and self.x_start2end_count > 10 and abs(velocity_x) < 90:
                                self.end_point_x = (x_center,median_class_id)
                                self.x_start2end_count = None #初期化
                            
                            if self.end_point_x != None and self.cnt > 3:
                                diff = self.start_point_x[0] - self.end_point_x[0]
                                if self.start_point_x[2] == median_class_id:
                                    if diff > 0:
                                        if self.start_point_x[1] > 0 and abs(diff) > 100:
                                            print(idx2label[median_class_id],"left")
                                            self.detect_gesture_name = idx2label[median_class_id] + " left"
                                            self.cnt = 0
                                            threading.Thread(target=self.Infrared_signal_control,args=(median_class_id,4)).start()
                                    else:
                                        if self.start_point_x[1] < 0 and abs(diff) > 100:
                                            print(idx2label[median_class_id],"right")
                                            self.detect_gesture_name = idx2label[median_class_id] + " right"
                                            self.cnt = 0
                                            threading.Thread(target=self.Infrared_signal_control,args=(median_class_id,3)).start()
                            
                                start_flag_x = 0
                                self.start_point_x = None
                                self.end_point_x = None
                            
                            #y
                            #if start_flag_y >= 1 and abs(velocity_y) > 300 and self.y_start2end_count == None:
                            if start_flag_y >= 1 and abs(velocity_y) > 900:
                                self.start_point_y = (y_center,velocity_y,median_class_id)
                                self.y_start2end_count = 0
                                start_flag_y = 0
                                print(self.start_point_y)
                            #ジェスチャ開始後、数フレームの間待機する
                            if self.y_start2end_count != None:
                                self.y_start2end_count += 1

                            
                            #if self.start_point_y != None and self.end_point_y == None and abs(velocity_y) < 90:
                            if self.start_point_y != None and self.end_point_y == None and self.y_start2end_count > 10 and abs(velocity_y) < 90:
                                self.end_point_y = (y_center,median_class_id)
                                self.y_start2end_count = None #初期化
                                print(self.end_point_y)
                            
                            if self.end_point_y != None and self.cnt > 3:
                                diff = self.start_point_y[0] - self.end_point_y[0]
                                if self.start_point_y[2] == median_class_id:
                                    if diff > 0:
                                        if self.start_point_y[1] > 0 and abs(diff) > 100:
                                            print(idx2label[median_class_id],"up")
                                            self.detect_gesture_name = idx2label[median_class_id] + " up"
                                            self.cnt = 0
                                            threading.Thread(target=self.Infrared_signal_control,args=(median_class_id,1)).start()
                                    else:
                                        if self.start_point_y[1] < 0 and abs(diff) > 100:
                                            print(idx2label[median_class_id],"down")
                                            self.detect_gesture_name = idx2label[median_class_id] + " down"
                                            self.cnt = 0
                                            threading.Thread(target=self.Infrared_signal_control,args=(median_class_id,2)).start()
                            
                                start_flag_y = 0
                                end_flag_y = 0
                                self.start_point_y = None
                                self.end_point_y = None


                            if self.before_data != None:
                                if abs(self.before_data[0] - x_center) < 30 and abs(self.before_data[1] - y_center) < 30 and self.before_data[2] == median_class_id:
                                    self.cnt += 1
                                else:
                                    self.cnt = 0
                                    
                            if self.cnt > 30:
                                print(idx2label[median_class_id],"stop")
                                self.detect_gesture_name = idx2label[median_class_id] + " stop"
                                threading.Thread(target=self.Infrared_signal_control,args=(median_class_id,0)).start()
                                self.cnt = 0
                            
                            #現在のデータを過去のデータとして保持
                            self.before_data = (x_center,y_center,median_class_id)
                        #median_filterで計算するための配列を更新
                        if self.detect_class.__len__() < 9:
                            self.detected_data.append([x_center,y_center,0,0,class_id])
                            #最初のみすべてのデータを現在のclass_idでfillする
                            self.detect_class = np.array([class_id for _ in range(9)])
                        else:
                            self.detected_data.pop(0)
                            self.detected_data.append([x_center,y_center,velocity_x,velocity_y,median_class_id])
                            self.detect_class = np.append(self.detect_class[1:],class_id)
                        
                        #print(np.average(self.detected_data,axis=0)[3])


                        #print("速度x:",velocity_x)
                        #print("カウント:",self.cnt)
                        #print("フラッグx:",start_flag_x)
                        #print("フラッグy:",start_flag_y)
                    
                if time.time() - time_stamp > 1:
                    #print("reset")
                    self.start_point_x = None
                    self.start_point_y = None
                    self.x_start2end_count = None
                    self.y_start2end_count = None
                    self.before_data = None
                    self.end_point_x = None
                    self.end_point_y = None
                    self.cnt = 0
                
            self.frame_counter += 1
            if self.frame_counter > 60:
                self.detect_gesture_name = ""
                self.frame_counter = 0

            #frame = cv2.putText(frame,str(round(1/t,1))+"fps",(30,40),cv2.FONT_HERSHEY_PLAIN,3,(0,0,255),3)
            frame = cv2.putText(frame,self.detect_gesture_name,(30,80),cv2.FONT_HERSHEY_PLAIN,7,(0,0,255),3)            

            #表示サイズにリサイズ
            frame = cv2.resize(frame,(600,400))
            self.preview_frame = frame
            img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            #以前の描画更新結果と異なる場合は映像を描画
            if self.checker != img:
                self.exec_f.canvas.create_image((0,0),image=img,anchor=tk.NW,tag="img")
                self.checker = img
            #停止信号が渡された場合にキャンバスを初期化しloopを抜ける
            if self.stop:
                self.exec_f.canvas.delete("all")
                print("実行速度:",speed_sum/speed_count*1000,"ms")
                break
        cap.release()


    def network_setting(self,ret,frame):
        self.input_blob = next(iter(self.net.inputs))  #input_blob = 'data'
        self.out_blob   = next(iter(self.net.outputs)) #out_blob   = 'detection_out'
        self.model_n, self.model_c, self.model_h, self.model_w = self.net.inputs[self.input_blob].shape

        #左右反転(鏡)
        frame = cv2.flip(frame,1)

        #STEP-6
        in_frame = cv2.resize(frame, (self.model_w, self.model_h))
        in_frame = cv2.cvtColor(in_frame,cv2.COLOR_BGR2RGB)
        in_frame = cv2.normalize(in_frame,None,alpha=0,beta=1,norm_type=cv2.NORM_MINMAX,dtype=cv2.CV_32F)
        in_frame = in_frame.transpose((2, 0, 1))  # Change data layout from HWC to CHW
        in_frame = in_frame.reshape((self.model_n, self.model_c, self.model_h, self.model_w))
        #STEP-7
        self.exec_net.start_async(request_id=0, inputs={self.input_blob: in_frame})


    def exec_predict(self,ret,frame,cap_h,cap_w):
        frame = cv2.flip(frame,1)
        
        #STEP-6
        in_frame = cv2.resize(frame, (self.model_w, self.model_h))
        in_frame = cv2.cvtColor(in_frame,cv2.COLOR_BGR2RGB)
        in_frame = cv2.normalize(in_frame,None,alpha=0,beta=1,norm_type=cv2.NORM_MINMAX,dtype=cv2.CV_32F)
        in_frame = in_frame.transpose((2, 0, 1))  # Change data layout from HWC to CHW
        in_frame = in_frame.reshape((self.model_n, self.model_c, self.model_h, self.model_w))
        self.exec_net.start_async(request_id=0, inputs={self.input_blob: in_frame})

        time_stamp = 0
        self.start_flag_x = 0
        self.start_flag_y = 0
        #end_flag_y = 0
        speed_count = 0#仮
        speed_sum = 0#仮
        t = 0
        start_time = time.time()
        if self.exec_net.requests[0].wait(-1) == 0:
            result = self.exec_net.requests[0].outputs
            #time.sleep(0.07)

            current_time = time.time()
            #tは実行にかかった時間(速度計算に使用)
            t = current_time - start_time
            speed_count += 1
            speed_sum += t
            out_list = []
            for out_blob in result.values():
                out_blob = out_blob.transpose(0,2,3,1)
                #print(out_blob.shape)
                out_list.append(out_blob)
                
            objects = yolo3_postprocess_np(out_list,(cap_h,cap_w),anchors,12,(self.model_h,self.model_w),confidence=0.1)
            iou_threshold = 0.1
            for i in range(len(objects[0])):
                #print(i,"access")
                if objects[3][i] == 0:
                    continue
                for j in range(i + 1, len(objects[0])):
                    if intersection_over_union(objects[1][i], objects[1][j]) > iou_threshold:
                        objects[3][j] = 0
            velocity_x = 0
            velocity_y = 0
            for i in range(len(objects[0])):
                if objects[3][i] > 0.3:
                    #print(objects)
                    x_center = objects[0][i][0]
                    y_center = objects[0][i][1]
                    class_id = objects[2][i]
                    if self.detect_class.__len__() == 9:
                        #class_idのmedianを計算して検出クラスを安定させる
                        median_class_id = np.median(self.detect_class)
                        #print(self.detect_class)
                        frame = cv2.rectangle(frame,(objects[1][i][0],objects[1][i][1]),(objects[1][i][2],objects[1][i][3]),(0,255,0),3)
                        frame = cv2.putText(frame,idx2label[median_class_id],(objects[1][i][0]-3,objects[1][i][1]-3), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255),3)
                        frame = cv2.line(frame,(x_center,y_center),(x_center+1,y_center+1),(0,255,0),3)
                        time_stamp = time.time()
                        #print(time_stamp)

                        if self.before_data != None and t != 0:
                            #速度を計算
                            velocity_x = (self.before_data[0]-x_center)/t
                            velocity_y = (self.before_data[1]-y_center)/t
                            #print(velocity_y)

                        if self.start_point_x == None and self.cnt > 5:
                            self.start_flag_x = 1
                        
                        if self.start_point_y == None and self.cnt > 5:
                            self.start_flag_y = 1
                        
                        if self.start_flag_x >= 1:
                            self.start_flag_x += 1
                        
                        #カウント6以上でリセット
                        if self.start_flag_x > 5:
                            self.start_flag_x = 0
                            self.start_point_x = None
                            #print("reset x")
                        
                        if self.start_flag_y >= 1:
                            self.start_flag_y += 1
                        
                        #カウント6以上でリセット
                        if self.start_flag_y > 5:
                            self.start_flag_y = 0
                            self.start_point_y = None
                            #print("reset y")
                        
                        if self.start_flag_x >= 1 and abs(velocity_x) > 900:
                            self.start_point_x = (x_center,velocity_x,median_class_id)
                            self.x_start2end_count = 0
                            self.start_flag_x = 0
                            self.cnt = 0
                        #ジェスチャ開始後、数フレームの間待機する
                        if self.x_start2end_count != None:
                            self.x_start2end_count += 1
                        
                        if self.start_point_x != None and self.end_point_x == None and self.x_start2end_count > 10 and abs(velocity_x) < 90:
                            self.end_point_x = (x_center,median_class_id)
                            self.x_start2end_count = None #初期化
                        
                        if self.end_point_x != None and self.cnt > 3:
                            diff = self.start_point_x[0] - self.end_point_x[0]
                            if self.start_point_x[2] == median_class_id:
                                if diff > 0:
                                    if self.start_point_x[1] > 0 and abs(diff) > 100:
                                        print(idx2label[median_class_id],"left")
                                        self.detect_gesture_name = idx2label[median_class_id] + " left"
                                        self.cnt = 0
                                        threading.Thread(target=self.Infrared_signal_control,args=(median_class_id,4)).start()
                                else:
                                    if self.start_point_x[1] < 0 and abs(diff) > 100:
                                        print(idx2label[median_class_id],"right")
                                        self.detect_gesture_name = idx2label[median_class_id] + " right"
                                        self.cnt = 0
                                        threading.Thread(target=self.Infrared_signal_control,args=(median_class_id,3)).start()
                        
                            self.start_flag_x = 0
                            self.start_point_x = None
                            self.end_point_x = None
                        
                        #y
                        #if start_flag_y >= 1 and abs(velocity_y) > 300 and self.y_start2end_count == None:
                        if self.start_flag_y >= 1 and abs(velocity_y) > 900:
                            self.start_point_y = (y_center,velocity_y,median_class_id)
                            self.y_start2end_count = 0
                            self.start_flag_y = 0
                            print(self.start_point_y)
                        #ジェスチャ開始後、数フレームの間待機する
                        if self.y_start2end_count != None:
                            self.y_start2end_count += 1

                        
                        #if self.start_point_y != None and self.end_point_y == None and abs(velocity_y) < 90:
                        if self.start_point_y != None and self.end_point_y == None and self.y_start2end_count > 10 and abs(velocity_y) < 90:
                            self.end_point_y = (y_center,median_class_id)
                            self.y_start2end_count = None #初期化
                            print(self.end_point_y)
                        
                        if self.end_point_y != None and self.cnt > 3:
                            diff = self.start_point_y[0] - self.end_point_y[0]
                            if self.start_point_y[2] == median_class_id:
                                if diff > 0:
                                    if self.start_point_y[1] > 0 and abs(diff) > 100:
                                        print(idx2label[median_class_id],"up")
                                        self.detect_gesture_name = idx2label[median_class_id] + " up"
                                        self.cnt = 0
                                        threading.Thread(target=self.Infrared_signal_control,args=(median_class_id,1)).start()
                                else:
                                    if self.start_point_y[1] < 0 and abs(diff) > 100:
                                        print(idx2label[median_class_id],"down")
                                        self.detect_gesture_name = idx2label[median_class_id] + " down"
                                        self.cnt = 0
                                        threading.Thread(target=self.Infrared_signal_control,args=(median_class_id,2)).start()
                        
                            self.start_flag_y = 0
                            end_flag_y = 0
                            self.start_point_y = None
                            self.end_point_y = None


                        if self.before_data != None:
                            if abs(self.before_data[0] - x_center) < 30 and abs(self.before_data[1] - y_center) < 30 and self.before_data[2] == median_class_id:
                                self.cnt += 1
                            else:
                                self.cnt = 0
                                
                        if self.cnt > 30:
                            print(idx2label[median_class_id],"stop")
                            self.detect_gesture_name = idx2label[median_class_id] + " stop"
                            threading.Thread(target=self.Infrared_signal_control,args=(median_class_id,0)).start()
                            self.cnt = 0
                        
                        #現在のデータを過去のデータとして保持
                        self.before_data = (x_center,y_center,median_class_id)
                    #median_filterで計算するための配列を更新
                    if self.detect_class.__len__() < 9:
                        self.detected_data.append([x_center,y_center,0,0,class_id])
                        #最初のみすべてのデータを現在のclass_idでfillする
                        self.detect_class = np.array([class_id for _ in range(9)])
                    else:
                        self.detected_data.pop(0)
                        self.detected_data.append([x_center,y_center,velocity_x,velocity_y,median_class_id])
                        self.detect_class = np.append(self.detect_class[1:],class_id)
                    
                    #print(np.average(self.detected_data,axis=0)[3])


                    #print("速度x:",velocity_x)
                    #print("カウント:",self.cnt)
                    #print("フラッグx:",start_flag_x)
                    #print("フラッグy:",start_flag_y)
                
            if time.time() - time_stamp > 1:
                #print("reset")
                self.start_point_x = None
                self.start_point_y = None
                self.x_start2end_count = None
                self.y_start2end_count = None
                self.before_data = None
                self.end_point_x = None
                self.end_point_y = None
                self.cnt = 0
                
            self.frame_counter += 1
            if self.frame_counter > 60:
                self.detect_gesture_name = ""
                self.frame_counter = 0

            #frame = cv2.putText(frame,str(round(1/t,1))+"fps",(30,40),cv2.FONT_HERSHEY_PLAIN,3,(0,0,255),3)
            frame = cv2.putText(frame,self.detect_gesture_name,(30,80),cv2.FONT_HERSHEY_PLAIN,7,(0,0,255),3)            
            #表示サイズにリサイズ
            #frame = cv2.resize(frame,(600,400))
        return frame

    #ジェスチャに対応した赤外線信号を発信する
    def Infrared_signal_control(self,class_id,move_id):
        target_id = 5*class_id + move_id
        dbpath = "gesture_db.sqlite"
        connection = sqlite3.connect(dbpath)
        cursor = connection.cursor()
        print("target_id",target_id)
        cursor.execute("SELECT * FROM sample WHERE target_id = "+str(target_id))
        res = cursor.fetchall()
        print(res)
        if len(res) != 0:
            self.playIR(res[0])
    
    #引数で与えられた赤外線信号を発信する
    def playIR(self,data):
        print("Playing IR")
        rawdata = data[4].split(",")
        rawdata = [int(d) for d in rawdata]
        recNumber = len(rawdata)
        rawX = rawdata

        ir_serial.write(("n,%d\r\n" % recNumber).encode())
        ir_serial.readline()

        postScale = data[2]
        ir_serial.write(("k,%d\r\n" % postScale).encode())
        #time.sleep(1.0)
        msg = ir_serial.readline()
    
        for n in range(recNumber):
            bank = n / 64
            pos = n % 64
            if (pos == 0):
                ir_serial.write(("b,%d\r\n" % bank).encode())
    
            ir_serial.write(("w,%d,%d\n\r" % (pos, rawX[n])).encode())
    
        ir_serial.write("p\r\n".encode())
        msg = ir_serial.readline()
        print(msg)

#オブジェクトを生成
yolo_obj = YOLO("CPU")