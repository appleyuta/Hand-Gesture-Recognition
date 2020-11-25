import tkinter as tk
from tkinter import font
from registerframe import RegisterFrame
from envframe import EnvironmentFrame
from infraredregisterframe import InfraredSignalRegisterFrame
import threading

class SettingFrame(tk.Frame):
    def __init__(self,start_f,master=None,**kwargs):
        tk.Frame.__init__(self,master=master,**kwargs,width=600,height=600)
        self.back_button = tk.Button(self,text="back menu",font=font.Font(size=10),command=self.Back)
        self.infrared_register_button = tk.Button(self,text="赤外線登録",font=font.Font(size=40),command=self.InfraredSignalRegister)
        self.register_button = tk.Button(self,text="ジェスチャ登録",font=font.Font(size=40),command=self.Register)
        self.env_button = tk.Button(self,text="環境設定",font=font.Font(size=40),command=self.Environment)
        self.back_button.place(x=0,y=0)
        self.infrared_register_button.place(anchor=tk.CENTER,x=300,y=150,width=400,height=150)
        self.register_button.place(anchor=tk.CENTER,x=300,y=300,width=400,height=150)
        self.env_button.place(anchor=tk.CENTER,x=300,y=450,width=400,height=150)
        self.parent = start_f #StratFrame
        self.pack()

    #ホーム画面へ移行
    def Back(self):
        self.pack_forget()
        self.parent.pack()
        #self.start_frame.pack() ?
    
    def InfraredSignalRegister(self):
        self.pack_forget()
        threading.Thread(target=InfraredSignalRegisterFrame,args=(self,)).start()
        #2InfraredSignalRegisterFrame(setting_f=self)

    #ジェスチャ登録画面へ移行
    def Register(self):
        self.pack_forget()
        threading.Thread(target=RegisterFrame,args=(self,)).start()
        #RegisterFrame(setting_f=self)

    #環境設定画面へ移行
    def Environment(self):
        self.pack_forget()
        threading.Thread(target=EnvironmentFrame,args=(self,)).start()

