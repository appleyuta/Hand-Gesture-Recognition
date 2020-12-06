import tkinter as tk
from tkinter import ttk
from tkinter import font, messagebox
import threading
import sqlite3

class RegisterFrame(tk.Frame):
    def __init__(self,setting_f,master=None,**kwargs):
        tk.Frame.__init__(self,master=master,**kwargs,width=600,height=600)
        self.tree = ttk.Treeview(self)
        self.tree["columns"] = (1,2,3,4)
        self.tree.column(1,width=5)
        self.tree["show"] = "headings"
        self.tree.heading(1,text="id")
        self.tree.heading(2,text="登録名")
        self.tree.heading(3,text="クラス")
        self.tree.heading(4,text="動作")
        self.label = tk.Label(self,text="ジェスチャ登録",font=font.Font(size=30))
        self.class_name = tk.StringVar()
        self.move_name = tk.StringVar()
        self.ir_name = tk.StringVar()
        self.cls_label2idx = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"three_v2":6,"fit":7,"fox":8,"ok":9,"go":10,"little_finger":11}
        self.move_label2idx = {"stop":0,"up":1,"down":2,"right":3,"left":4}
        self.cls_idx2label = {value:key for key,value in self.cls_label2idx.items()}
        self.move_idx2label = {value:key for key,value in self.move_label2idx.items()}
        self.ir_label2idx = {value:key for key,value in self.get_data(load_id=True)}
        self.select_class = ttk.Combobox(self,state="readonly",textvariable=self.class_name,values=["zero","one","two","three","four","five","three_v2","fit","fox","ok","go","little_finger"])
        self.select_movement = ttk.Combobox(self,state="readonly",textvariable=self.move_name,values=["stop","up","down","right","left"])
        self.select_ir = ttk.Combobox(self,state="readonly",textvariable=self.ir_name,values=self.get_data(load_id=False))
        self.select_class.set("zero")
        self.select_movement.set("stop")
        self.select_ir.set(self.get_data(load_id=False)[0])
        self.register_button = tk.Button(self,text="登録",font=font.Font(size=30),command=self.Register)
        self.back_button = tk.Button(self,text="back",font=font.Font(size=10),command=self.Back)
        self.delete_button = tk.Button(self,text="選択した項目を削除",font=font.Font(size=10),command=self.delete)
        self.label.place(anchor=tk.CENTER,x=300,y=50)
        self.select_class.place(anchor=tk.CENTER,x=300,y=100)
        self.select_movement.place(anchor=tk.CENTER,x=300,y=130)
        self.select_ir.place(anchor=tk.CENTER,x=300,y=160)
        self.register_button.place(anchor=tk.CENTER,x=300,y=230)
        self.back_button.place(x=0,y=0)
        self.parent = setting_f #SettingFrame
        print(self.ir_label2idx)
        self.tree_update()
        self.tree.place(anchor=tk.CENTER,x=300,y=400)
        self.delete_button.place(anchor=tk.CENTER,x=300,y=550) 
        self.pack()
    
    def Register(self):
        #ここで所定の登録作業を実行する
        thread1 = threading.Thread(target=self.thread_register)
        thread1.start()
    
    def thread_register(self):
        target_id = 5*self.cls_label2idx[self.class_name.get()]+self.move_label2idx[self.move_name.get()]
        pkey_id = self.ir_label2idx[self.ir_name.get()]
        print("ir_name:",self.ir_name.get())
        if self.ir_name.get() == "":
            messagebox.showinfo("確認","赤外線名が登録されていません。\n赤外線登録画面から赤外線を登録してください。")
            return
        dbpath = "gesture_db.sqlite"
        connection = sqlite3.connect(dbpath)
        cursor = connection.cursor()
        try:
            cursor.execute("CREATE TABLE IF NOT EXISTS sample (id INTEGER PRIMARY KEY, irname TEXT,postscale INTEGER, freq INTEGER, data TEXT,format TEXT,target_id INTEGER)")
            cursor.execute("UPDATE sample SET target_id = :target_id where id = :id",{"id":pkey_id,"target_id":target_id})
        except sqlite3.Error as e:
            print("sqlite3.Error occured:",e.args[0])
        
        connection.commit()
        connection.close()
        print("COMMIT!")
        print(self.class_name.get(),self.move_name.get())
        messagebox.showinfo("確認","正常に登録されました")
        self.tree_update()
        

    def Back(self):
        self.pack_forget()
        self.parent.pack()

    
    def delete(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        ret = messagebox.askyesno("確認","選択した項目を削除しますか?")
        if ret == True:
            for selected_item in selected_items:
                values = self.tree.item(selected_item,'values')
                print(values)
                dbpath = "gesture_db.sqlite"
                connection = sqlite3.connect(dbpath)
                cursor = connection.cursor()
                cursor.execute("UPDATE sample SET target_id = null WHERE id = "+str(values[0]))
                connection.commit()
                connection.close()
                print("COMMIT!")
            messagebox.showinfo("確認","正常に削除されました")
            self.tree_update()

            
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

    def tree_update(self):
        self.tree.delete((*self.tree.get_children()))
        dbpath = "gesture_db.sqlite"
        connection = sqlite3.connect(dbpath)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS sample (id INTEGER PRIMARY KEY, irname TEXT,postscale INTEGER, freq INTEGER, data TEXT,format TEXT,target_id INTEGER)")
        cursor.execute("SELECT id,irname,target_id from sample where target_id >= 0")
        res = cursor.fetchall()
        print(res)
        for data in res:
            class_id = data[2]//5
            move_id = data[2]%5
            self.tree.insert("","end",values=data[:-1]+(self.cls_idx2label[class_id],self.move_idx2label[move_id]))
