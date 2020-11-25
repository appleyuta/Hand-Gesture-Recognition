from kivy.uix.spinner import Spinner
import sqlite3

class CustomSpinner(Spinner):
    def __init__(self,**kwargs):
        super(CustomSpinner,self).__init__(**kwargs)
        self.values = self.get_data(load_id=False)
        self.text = self.values[0]

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
                for i,text in enumerate(res):
                    res[i] = text[0]
                return res
            else:
                return ['']