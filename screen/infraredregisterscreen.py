import sqlite3
import threading
from serial_device import ir_serial
from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
import time
from msgpopup import MessagePopup
from rv import RV

class InfraredRegisterScreen(Screen):
    rows = ListProperty(["id"])
    def __init__(self,**kwargs):
        super(InfraredRegisterScreen,self).__init__(**kwargs)
        self.data = []
        self.update_treeview()

    def build(self):
        pass

    def irRegister(self):
        if ir_serial == None:
            MessagePopup("警告","irMagicianが接続されていません。\nデバイスを接続してアプリを再起動してください。",size_hint=(.6,.6)).popup_open()
            return
        thread1 = threading.Thread(target=self.captureIR)
        thread1.start()
    
    def captureIR(self):
        name = self.ids.register_name.text
        if name == "":
            print("登録名未入力")
            MessagePopup("確認","登録名が入力されていません。\n登録名を入力してください。",size_hint=(.5,.5)).popup_open()
            return
        dbpath = "gesture_db.sqlite"
        connection = sqlite3.connect(dbpath)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS sample (id INTEGER PRIMARY KEY, irname TEXT,postscale INTEGER, freq INTEGER, data TEXT,format TEXT,target_id INTEGER)")
        cursor.execute("SELECT irname from sample ORDER BY id")
        res = cursor.fetchall()
        print(res)
        for data in res:
            if name == data[0]:
                print("登録名重複")
                MessagePopup("確認","常に登録されている登録名です。\n重複しない登録名を入力してください。",size_hint=(.7,.7)).popup_open()
                return
        box = GridLayout()
        box.add_widget(Label(text="irMagicianに向けてリモコンのボタンを押して赤外線登録",center=self.center))
        popupwindow = Popup(title="登録中",size_hint=(.7,.7),pos_hint={'center_x':.5,'center_y':.5},content=box)
        popupwindow.open()
        print("Capturing IR...")
        ir_serial.write("c\r\n".encode())
        time.sleep(3.0)
        msg = ir_serial.readline()
        print(msg)
        if name and not "Time Out" in str(msg):
            box = GridLayout()
            box.add_widget(Label(text="DBに赤外線を登録中",center=self.center))
            popupwindow.content = box
            self.saveIR(name)
            popupwindow.dismiss()
            self.update_treeview()
        else:
            popupwindow.dismiss()
            MessagePopup("確認","タイムアウトしました",size_hint=(.5,.5)).popup_open()


    def saveIR(self,name):
        print("Saving IR data to %s ..." % name)
        rawX = []
        ir_serial.write("I,1\r\n".encode())
        time.sleep(1.0)
        recNumberStr = ir_serial.readline()
        recNumber = int(recNumberStr, 16)
  
        ir_serial.write("I,6\r\n".encode())
        time.sleep(1.0)
        postScaleStr = ir_serial.readline()
        postScale = int(postScaleStr, 10)
  
        for n in range(recNumber):
            bank = n / 64
            pos = n % 64
            if (pos == 0):
                ir_serial.write(("b,%d\r\n" % bank).encode())
  
            ir_serial.write(("d,%d\n\r" % pos).encode())
            xStr = ir_serial.read(3) 
            xData = int(xStr, 16)
            rawX.append(xData)
  
        data = {'format':'raw', 'freq':38, 'data':rawX, 'postscale':postScale}

        print("Done !")
        print(rawX)
        rawX_str = ""
        for data in rawX:
            rawX_str += str(data)+","
        print(rawX_str)
        dbpath = "gesture_db.sqlite"
        connection = sqlite3.connect(dbpath)
        cursor = connection.cursor()
        try:
            cursor.execute("CREATE TABLE IF NOT EXISTS sample (id INTEGER PRIMARY KEY, irname TEXT,postscale INTEGER, freq INTEGER, data TEXT,format TEXT,target_id INTEGER)")
            cursor.execute("INSERT INTO sample(irname, postscale, freq, data, format) VALUES (:irname, :postscale, :freq, :data, :format)",{"irname":name,"postscale":postScale,"freq":38,"data":rawX_str[:-1],"format":"raw"})
        except sqlite3.Error as e:
            print("sqlite3.Error occured:",e.args[0])
        
        connection.commit()
        connection.close()
        print("COMMIT!")
        MessagePopup("確認","正常に登録されました",size_hint=(.5,.5)).popup_open()
    
    def deletecheck(self):
        print(self.ids.datatable.index)
        selected_items = self.ids.datatable.index
        if not selected_items:
            return
        MessagePopup("確認","選択した項目を削除しますか?",size_hint=(.5,.5),mtype="YesNo",yes_func=self.delete).popup_open()

    def delete(self):
        print(self.ids.datatable.index)
        selected_items = self.ids.datatable.index
        if not selected_items:
            return
        box = GridLayout()
        box.add_widget(Label(text="DBから削除しています",center=self.center))
        popupwindow = Popup(title="削除中",size_hint=(.5,.5),pos_hint={'center_x':.5,'center_y':.5},content=box,auto_dismiss=False)
        popupwindow.open()
        yesno = True
        if yesno == True:
            for selected_item in selected_items:
                values = self.ids.datatable.data[selected_item]
                print(values)
                dbpath = "gesture_db.sqlite"
                connection = sqlite3.connect(dbpath)
                cursor = connection.cursor()
                cursor.execute("DELETE FROM sample WHERE id = "+values['text'])
                connection.commit()
                connection.close()
                print("COMMIT!")
            popupwindow.dismiss()
            MessagePopup("確認","正常に削除されました",size_hint=(.5,.5)).popup_open()
            self.ids.datatable.index = []
            self.update_treeview()

    def update_treeview(self):
        dbpath = "gesture_db.sqlite"
        connection = sqlite3.connect(dbpath)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS sample (id INTEGER PRIMARY KEY, irname TEXT,postscale INTEGER, freq INTEGER, data TEXT,format TEXT,target_id INTEGER)")
        cursor.execute("SELECT id,irname from sample ORDER BY id")
        res = cursor.fetchall()
        self.data.clear()
        for i,name in res:
            self.data.append(str(i))
            self.data.append(name)
        self.rows = self.data
        print(self.rows)
