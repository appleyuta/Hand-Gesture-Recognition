import tkinter as tk
import os
import sys

sys.path.append(os.path.abspath("./frame"))

from startframe import StartFrame
from serial_device import ir_serial
import threading


class GUIAPP(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Gesture Recognition System")
        self.geometry("600x600")
        self.resizable(width = False,height = False)
        self.start_frame = StartFrame(self)
        self.start_frame.pack()
    
    def GUIStart(self):
        self.mainloop()


if __name__ == "__main__":
    app = GUIAPP()
    app.GUIStart()
    if ir_serial != None:
        ir_serial.write("r,0\r\n".encode())
        msg = ir_serial.readline()
        print(msg)
        ir_serial.close()
