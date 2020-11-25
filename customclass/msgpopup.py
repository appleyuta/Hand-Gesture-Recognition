from kivy.properties import StringProperty,ObjectProperty,BooleanProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
import threading

class PopupMenu(BoxLayout):
    popup_close = ObjectProperty(None)
    text = StringProperty('')
    def __init__(self,text,**kwargs):
        super(PopupMenu,self).__init__(**kwargs)
        self.text = text

class PopupYesNo(BoxLayout):
    popup_close = ObjectProperty(None)
    setYes = ObjectProperty(None)
    setNo = ObjectProperty(None)
    text = StringProperty('')
    def __init__(self,text,**kwargs):
        super(PopupYesNo,self).__init__(**kwargs)
        self.text = text
    

class MessagePopup(GridLayout):
    title = StringProperty('')
    YesNo = BooleanProperty(None)
    def __init__(self,title,text,size_hint=(1.0,1.0),mtype="Menu",yes_func=lambda *args: None,no_func=lambda *args: None,**kwargs):
        super(MessagePopup,self).__init__(**kwargs)
        self.title = title
        self.text = text
        self.size_hint = size_hint
        self.mtype = mtype
        self.yes_func = yes_func
        self.no_func = no_func


    def popup_open(self):
        if self.mtype == "Menu":
            content = PopupMenu(text=self.text,popup_close=self.popup_close)
        elif self.mtype == "YesNo":
            content = PopupYesNo(text=self.text,popup_close=self.popup_close,setYes=self.setYes,setNo=self.setNo)
        self.popup = Popup(title=self.title,size_hint=self.size_hint,pos_hint={'center_x':.5,'center_y':.5},content=content,auto_dismiss=False)
        self.popup.open()
        

    def popup_close(self):
        self.popup.dismiss()
    
    def setYes(self):
        threading.Thread(target=self.yes_func).start()
        self.YesNo = True
    
    def setNo(self):
        threading.Thread(target=self.no_func).start()
        self.YesNo = False
