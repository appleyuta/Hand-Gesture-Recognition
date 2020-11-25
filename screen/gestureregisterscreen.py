import sqlite3
import threading
from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from msgpopup import MessagePopup
from rv import RV
from customspinner import CustomSpinner

class GestureRegisterScreen(Screen):
    rows = ListProperty(["id"])
    def __init__(self,**kwargs):
        super(GestureRegisterScreen,self).__init__(**kwargs)
        self.cls_label2idx = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"three_v2":6,"fit":7,"fox":8,"ok":9,"go":10,"little_finger":11}
        self.move_label2idx = {"stop":0,"up":1,"down":2,"right":3,"left":4}
        self.cls_idx2label = {value:key for key,value in self.cls_label2idx.items()}
        self.move_idx2label = {value:key for key,value in self.move_label2idx.items()}
        self.ir_label2idx = {value:key for key,value in self.get_data(load_id=True)}
        self.data = []
        self.update_treeview()

    def build(self):
        pass


    def Register(self):
        #ここで所定の登録作業を実行する
        thread1 = threading.Thread(target=self.thread_register)
        thread1.start()
    
    def thread_register(self):
        target_id = 5*self.cls_label2idx[self.ids.class_name.text]+self.move_label2idx[self.ids.move_name.text]
        print("ir_name:",self.ids.class_name.text)
        pkey_id = self.ir_label2idx[self.ids.ir_name.text]
        print("ir_name:",self.ids.ir_name.text)
        if self.ids.ir_name.text == "":
            #messagebox.showinfo("確認","赤外線名が登録されていません。\n赤外線登録画面から赤外線を登録してください。")
            MessagePopup("確認","赤外線名が登録されていません。\n赤外線登録画面から赤外線を登録してください。",size_hint=(.6,.6)).popup_open()
            return
        box = GridLayout()
        box.add_widget(Label(text="DBにジェスチャを登録しています",center=self.center))
        print(self.center)
        popupwindow = Popup(title="登録中",size_hint=(.5,.5),pos_hint={'center_x':.5,'center_y':.5},content=box,auto_dismiss=False)
        popupwindow.open()
        dbpath = "gesture_db.sqlite"
        connection = sqlite3.connect(dbpath)
        cursor = connection.cursor()
        try:
            #cursor.execute("DROP TABLE IF EXISTS sample")
            cursor.execute("CREATE TABLE IF NOT EXISTS sample (id INTEGER PRIMARY KEY, irname TEXT,postscale INTEGER, freq INTEGER, data TEXT,format TEXT,target_id INTEGER)")
            cursor.execute("UPDATE sample SET target_id = :target_id where id = :id",{"id":pkey_id,"target_id":target_id})
        except sqlite3.Error as e:
            print("sqlite3.Error occured:",e.args[0])
        
        connection.commit()
        connection.close()
        print("COMMIT!")
        print(self.ids.class_name.text,self.ids.move_name.text)
        #messagebox.showinfo("確認","正常に登録されました")
        popupwindow.dismiss()
        MessagePopup("確認","正常に登録されました",size_hint=(.5,.5)).popup_open()
        self.update_treeview()
    
    def deletecheck(self):
        print(self.ids.datatable.index)
        #selected_items = self.tree.selection()
        selected_items = self.ids.datatable.index
        if not selected_items:
            return
        #ret = messagebox.askyesno("確認","選択した項目を削除しますか?")
        MessagePopup("確認","選択した項目を削除しますか?",size_hint=(.5,.5),mtype="YesNo",yes_func=self.delete).popup_open()
    
    def delete(self):
        print(self.ids.datatable.index)
        #selected_items = self.tree.selection()
        selected_items = self.ids.datatable.index
        if not selected_items:
            return
        box = GridLayout()
        box.add_widget(Label(text="DBから削除しています",center=self.center))
        popupwindow = Popup(title="削除中",size_hint=(.5,.5),pos_hint={'center_x':.5,'center_y':.5},content=box,auto_dismiss=False)
        popupwindow.open()
        ret = True
        if ret == True:
            for selected_item in selected_items:
                values = self.ids.datatable.data[selected_item]
                print(values)
                dbpath = "gesture_db.sqlite"
                connection = sqlite3.connect(dbpath)
                cursor = connection.cursor()
                cursor.execute("UPDATE sample SET target_id = null WHERE id = "+values['text'])
                connection.commit()
                connection.close()
                print("COMMIT!")
            #messagebox.showinfo("確認","正常に削除されました")
            MessagePopup("確認","正常に削除されました",size_hint=(.5,.5)).popup_open()
            #create_Popup("確認","正常に削除されました",center=self.center).open()
            popupwindow.dismiss()
            self.ids.datatable.index = []
            self.update_treeview()
    
    def get_data(self,load_id=True):    
        dbpath = "gesture_db.sqlite"
        connection = sqlite3.connect(dbpath)
        cursor = connection.cursor()
        if load_id == True:
            cursor.execute("SELECT id,irname FROM sample ORDER BY id")
            res = cursor.fetchall()
            print(res)
            if res.__len__() != 0:
                return res
            else:
                return [('','')]
        else:
            cursor.execute("SELECT irname FROM sample ORDER BY id")
            res = cursor.fetchall()
            print(res)
            if res.__len__() != 0:
                return res
            else:
                return ['']
    
    def update_treeview(self):
        #self.tree.delete((*self.tree.get_children()))
        dbpath = "gesture_db.sqlite"
        connection = sqlite3.connect(dbpath)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS sample (id INTEGER PRIMARY KEY, irname TEXT,postscale INTEGER, freq INTEGER, data TEXT,format TEXT,target_id INTEGER)")
        cursor.execute("SELECT id,irname,target_id from sample where target_id >= 0")
        res = cursor.fetchall()
        print(res)
        self.data.clear()
        for i,name,target_id in res:
            class_id = target_id//5
            move_id = target_id%5
            self.data.append(str(i))
            self.data.append(name)
            self.data.append(self.cls_idx2label[class_id])
            self.data.append(self.move_idx2label[move_id])
        self.rows = self.data
        print(self.rows)
        """for data in res:
            class_id = data[2]//5
            move_id = data[2]%5
            # = self.cls_label2idx[class_id]+self.move_label2idx[move_id]
            self.tree.insert("","end",values=data[:-1]+(self.cls_idx2label[class_id],self.move_idx2label[move_id]))"""
