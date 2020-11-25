import tkinter as tk
from tkinter import ttk
from tkinter import font

class EnvironmentFrame(tk.Frame):
    def __init__(self,setting_f,master=None,**kwargs):
        tk.Frame.__init__(self,master=master,**kwargs)
        self.label = tk.Label(self,text="環境設定",font=font.Font(size=30))
        self.back_button = tk.Button(self,text="back",command=self.Back)
        self.exec_env = ttk.Combobox(self,values = ["CPU","GPU","MYRIAD"])
        self.exec_env.set("CPU")
        self.label.grid()
        self.exec_env.grid()
        self.back_button.grid()
        self.pack()
        self.parent = setting_f #SettingFrame

    def Back(self):
        self.pack_forget()
        self.parent.pack()

