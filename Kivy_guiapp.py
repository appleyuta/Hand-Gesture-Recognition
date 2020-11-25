from kivy.config import Config
Config.set('graphics', 'width', '600')
Config.set('graphics', 'height', '600')
Config.set('graphics','resizable',False)
import os
import sys
sys.path.append(os.path.abspath("./screen"))
sys.path.append(os.path.abspath("./customclass"))

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager
from mainscreen import MainScreen
from executescreen import ExecuteScreen
from settingscreen import SettingScreen
from infraredregisterscreen import InfraredRegisterScreen
from gestureregisterscreen import GestureRegisterScreen
from environmentsettingscreen import EnvironmentSettingScreen
import japanize_kivy

class GUIApp(App):
    def __init__(self, **kwargs):
        super(GUIApp,self).__init__(**kwargs)
        self.title = 'Gesture Recognition System'
    
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(ExecuteScreen(name='exec'))
        self.sm.add_widget(SettingScreen(name='setting'))
        self.sm.add_widget(InfraredRegisterScreen(name='irregister'))
        self.sm.add_widget(GestureRegisterScreen(name='gesregister'))
        self.sm.add_widget(EnvironmentSettingScreen(name='envsetting'))
        return self.sm


if __name__ == "__main__":
    GUIApp().run()