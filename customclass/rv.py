from kivy.properties import NumericProperty,ListProperty,BooleanProperty
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior 
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView

class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior, 
           RecycleGridLayout): 
    ''' Adds selection and focus behaviour to the view. ''' 

class SelectableLabel(RecycleDataViewBehavior, Label): 
    ''' Add selection support to the Label ''' 
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    cols = NumericProperty(2)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        self.cols = rv.cols
        return super(SelectableLabel, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            clickindex = self.index % self.cols
            if clickindex == 0:
                for i in range(self.cols-1):
                    self.parent.select_with_touch(self.index+i+1,touch)
                #self.index
                #self.parent.select_with_touch(self.index+1,touch)
            else:
                for i in range(clickindex):
                    self.parent.select_with_touch(self.index-i-1,touch)
                for i in range(self.cols - clickindex-1):
                    self.parent.select_with_touch(self.index+i+1,touch)
                #self.parent.select_with_touch(self.index-1,touch)
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            #self.index = index
            #print(self.index)
            if index % rv.cols == 0:
                rv.index = rv.index + [index]
                rv.index = list(set(rv.index))
            print("selection changed to {0}".format(rv.data[index]))
        else:
            try:
                rv.index = rv.index.remove(index)
            except:
                print("error")
            #rv.index = []
            rv.index = list(set(rv.index))
            print("selection removed for {0}".format(rv.data[index]))


class RV(RecycleView):
    index = ListProperty([])
    cols = NumericProperty(2)
    def __init__(self,**kwargs):
        super(RV,self).__init__(**kwargs)