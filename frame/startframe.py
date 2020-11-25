import tkinter as tk
from tkinter import font
import threading
from settingframe import SettingFrame
from execframe import ExecuteFrame
from serial_device import ir_serial


class StartFrame(tk.Frame):
    def __init__(self,master=None,**kwargs):
        tk.Frame.__init__(self,master,**kwargs,width=600,height=600)
        self.label = tk.Label(self,text="Gesture Recognition System",font=font.Font(family ="Times",size=30))
        self.start_button = tk.Button(self,text="Start",font=font.Font(size=40),height=2,command=self.Start)
        self.set_button = tk.Button(self,text="Setting",font=font.Font(size=40),height=2,command=self.Setting)
        self.label.place(anchor=tk.CENTER,x=300,y=30)
        self.start_button.place(anchor=tk.CENTER,x=300,y=200,width=250,height=200)
        self.set_button.place(anchor=tk.CENTER,x=300,y=400,width=250,height=200)

    #ジェスチャ認識を実行
    def Start(self):
        self.pack_forget()
        if ir_serial == None:
            threading.Thread(target=tk.messagebox.showerror,args=("警告","irMagicianが接続されていないか、認識されていません。\nデバイスを再接続してください。")).start()
        print("Button is clicked.")
        thread1 = threading.Thread(target=ExecuteFrame,args=(self,))
        thread1.start()
    
    #設定画面へ移行
    def Setting(self):
        print("setting")
        self.pack_forget()
        SettingFrame(start_f=self)