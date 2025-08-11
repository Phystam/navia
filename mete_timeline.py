from PySide6.QtCore import QObject, Signal, Slot

class MeteTimeline(QObject):
    def __init__(self,parent=None):
        super().__init__(parent=None)
        
    def _load_data(self):
        pass