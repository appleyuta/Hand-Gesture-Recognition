import tkinter as tk
from tkinter import font
from PIL import Image,ImageTk
from yolo import yolo_obj

class ExecuteFrame(tk.Frame):
    def __init__(self,start_f,master=None,**kwargs):
        tk.Frame.__init__(self,master,**kwargs)
        self.canvas = tk.Canvas(self,width=600,height=400)
        self.canvas.grid()
        self.label = tk.Label(self,text="実行中",font=font.Font(size=30))
        self.label.grid()
        self.button = tk.Button(self,text="Stop",font=font.Font(size=30),command=self.Stop)
        self.button.grid()
        #self.pack()
        self.parent = start_f #StartFrame
        #self.model = YOLO(exec_f=self,use_device="CPU")
        self.model = yolo_obj
        self.model.set_exec_f(self)
        self.checker = None
        self.Start()
    
    def Start(self):
        self.pack()
        #self.model = YOLO(exec_f=self,use_device="CPU")
        self.model.stop = False
        self.model.exec_model()

    def Stop(self):
        if self.model != None:
            self.model.stop = True
        #cv2.destroyAllWindows()
        self.pack_forget()
        self.parent.pack()
        #del self.model
        #self.model = None
    
    def update(self):
        if self.checker != self.model.img:
            self.canvas.create_image((0,0),image=self.model.img,anchor=tk.NW,tag="img")
            self.checker = self.model.img
        else:
            pass
        self.after(1,self.update)
