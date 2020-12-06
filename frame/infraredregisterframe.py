import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkinter import messagebox
import threading
import sqlite3

import sys
import serial
import time
import json
import argparse
import os
from serial_device import ir_serial


class CountWindow(tk.Toplevel):
    def __init__(self,master=None,**kwargs):
        tk.Toplevel.__init__(self,master,**kwargs)
        self.count = 0
        self.label = tk.Label(self, text = "irMagicianに向けてリモコンのボタンを押して赤外線登録")
        self.label2 = tk.Label(self, text = str(self.count)+"秒")
        self.label.pack()
        self.label2.pack()
        self.focus()
        self.attributes("-topmost", True) #最前面表示
        self.grab_set()
        self.id = None
        self.protocol('WM_DELETE_WINDOW', (lambda: 'pass')())

    
    def timer(self):
        self.count += 1
        self.label2.configure(text=str(self.count)+"秒")
        if self.count <= 2:
            self.id = self.after(1000,self.timer)
        else:
            self.after_cancel(self.id)
    
    def register_waiting(self):
        self.label2.configure(text="赤外線をデータベースに登録中です")



class InfraredSignalRegisterFrame(tk.Frame):
    def __init__(self,setting_f,master=None,**kwargs):
        tk.Frame.__init__(self,master=master,**kwargs,width=600,height=600)
        self.label = tk.Label(self,text="赤外線登録",font=font.Font(size=30))
        self.label2 = tk.Label(self,text="登録名")
        self.register_name = tk.Entry(self,width=20)
        self.irbutton = tk.Button(self,text="リモコンボタンを押して登録",command=self.irRegister,font=font.Font(size=20))
        self.back_button = tk.Button(self,text="back",command=self.Back)
        self.delete_button = tk.Button(self,text="選択した項目を削除",command=self.delete)
        self.back_button.place(x=0,y=0)
        self.label.place(anchor=tk.CENTER,x=300,y=50)
        self.label2.place(anchor=tk.CENTER,x=170,y=100)
        self.register_name.place(anchor=tk.CENTER,x=300,y=100)
        self.irbutton.place(anchor=tk.CENTER,x=300,y=150)
        self.parent = setting_f #SettingFrame
        self.tree = ttk.Treeview(self)
        self.tree["columns"] = (1,2)
        self.tree.column(1,width=5)
        self.tree["show"] = "headings"
        self.tree.heading(1,text="id")
        self.tree.heading(2,text="登録名")
        self.tree_update()
        self.tree.place(anchor=tk.CENTER,x=300,y=300)
        self.delete_button.place(anchor=tk.CENTER,x=300,y=500)
        self.pack()
        
    def Back(self):
        self.pack_forget()
        self.parent.pack()

    def irRegister(self):
        if ir_serial == None:
            messagebox.showerror("警告","irMagicianが接続されていません。\nデバイスを接続してアプリを再起動してください。")
            return
        thread1 = threading.Thread(target=self.captureIR)
        thread1.start()
    
    def captureIR(self):
        name = self.register_name.get()
        if name == "":
            messagebox.showinfo("確認","登録名が入力されていません。\n登録名を入力してください。")
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
                messagebox.showinfo("確認","既に登録されている登録名です。\n重複しない登録名を入力してください。")
                return
        newWindow = CountWindow(self)
        geo = self.master.geometry()
        geo = geo.split("+")
        x = int(geo[1])+160
        y = int(geo[2])+160
        newWindow.geometry("+"+str(x)+"+"+str(y))
        newWindow.timer()
        print("Capturing IR...")
        ir_serial.write("c\r\n".encode())
        time.sleep(3.0)
        msg = ir_serial.readline()
        print(msg)
        if name and not "Time Out" in str(msg):
            newWindow.register_waiting()
            self.saveIR(name)
            newWindow.destroy()
            self.tree_update()
        else:
            newWindow.destroy()
            messagebox.showinfo("確認","タイムアウトしました")


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
  
        #for n in range(640):
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
        pkey_id = 1
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
        res = messagebox.showinfo("確認","正常に登録されました")


    def serial_close(self):
        print("Reset IR...")
        self.ir_serial.write("r\r\n".encode())
        self.ir_serial.close()
    
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
                cursor.execute("DELETE FROM sample WHERE id = "+str(values[0]))
                connection.commit()
                connection.close()
                print("COMMIT!")
            messagebox.showinfo("確認","正常に削除されました")
            self.tree_update()


    def tree_update(self):
        self.tree.delete((*self.tree.get_children()))
        dbpath = "gesture_db.sqlite"
        connection = sqlite3.connect(dbpath)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS sample (id INTEGER PRIMARY KEY, irname TEXT,postscale INTEGER, freq INTEGER, data TEXT,format TEXT,target_id INTEGER)")
        cursor.execute("SELECT id,irname from sample ORDER BY id")
        res = cursor.fetchall()
        print(res)
        for data in res:
            self.tree.insert("","end",values=data)
