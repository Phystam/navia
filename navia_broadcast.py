from PySide6.QtCore import QObject, Signal, Slot

from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
API_SERVER_URL = "http://localhost:11434"


class Broadcaster(QObject):
    voicevox_onnxruntime_path= r"./voicevox_core/onnxruntime/lib/" + Onnxruntime.LIB_VERSIONED_FILENAME
    open_jtalk_dict_dir = r"./voicevox_core/dict/open_jtalk_dic_utf_8-1.11"
    
    
    def __init__(self,parent=None):
        #Synthesizer初期化

        Synth = Synthesizer(Onnxruntime.load_once(filename=self.voicevox_onnxruntime_path),OpenJtalk(self.open_jtalk_dict_dir))
        with VoiceModelFile.open(r"./voicevox_core/models/vvms/0.vvm") as model:
            Synth.load_voice_model(model)


    
    @Slot(str)
    def append_weather_info(self):
        pass