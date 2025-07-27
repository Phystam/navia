from PySide6.QtCore import QObject, Signal, Slot
import json
import ollama
import zstd
import re
import sys
import asyncio
from voicevox_core.asyncio import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
API_SERVER_URL = "http://localhost:11434"


class Broadcaster(QObject):
    """AIを使ったテキストの生成と音声合成を行う。

    Args:
        QObject (_type_): _description_
    """
    voicevox_onnxruntime_path= r"./voicevox_core/onnxruntime/lib/" + Onnxruntime.LIB_VERSIONED_FILENAME
    open_jtalk_dict_dir = r"./voicevox_core/dict/open_jtalk_dic_utf_8-1.11"
    
    model="qwen3:30b-a3b"
    def __init__(self,parent=None):
        model_path=r"./voicevox_core/models/vvms/0.vvm"
        self.synth: Synthesizer = asyncio.run(self.create_synthesizer())
        asyncio.run(self.load_model(model_path))

        self.prompt = [{"role": "user",
            "content": 
'''以下のテキストをすべて総合して要約し、天気予報のラジオ(あるいはテレビ)風に日本語で気象情報を伝える原稿を作ってください。
アナウンサーは男性(man)、女性(woman)がいて、女性は質問や解説、男性は主に解説をする役割です。
この原稿は直接音声合成ソフトに通して読み上げます。そのため、jsonでパースできるテキスト形式にしてください。
具体的には、
{"script": [
    {"speaker": "man", "text": "~"},
    {"speaker": "woman", "text": "~"},
    ...
    ]
}
の形式で出力してください。
まず、「m月d日、H時の気象情報です。」などのように、発表日時とタイトルを読み上げます。時間や場所は実際のXMLのデータに合わせて修正してください。
その後、ヘッドラインや本文に書かれている情報をもとに、わかりやすく解説を始めてください。
最後は「以上、◯◯県(◯◯地方)の気象情報でした。」で締めくくってください。'''
            }]

    async def create_synthesizer(self):
        #Synthesizer初期化
        ort=await Onnxruntime.load_once(filename=self.voicevox_onnxruntime_path)
        ojt=await OpenJtalk.new(self.open_jtalk_dict_dir)
        return Synthesizer(ort,ojt)
    
    async def load_model(self, model_path):
        async with await VoiceModelFile.open(model_path) as model:
            await self.synth.load_voice_model(model)
            
    async def generate_wav(self, text_json):
        """
        Generate a single WAV file by concatenating audio segments from each entry in text_json.
        Each entry must have 'speaker' and 'message' fields.
        """

        audio_segments = []
        
        await asyncio.gather(*[
        await self.synth.tts( t["message"], 0 if t["speaker"]=="man" else 11)
        for t in text_json ])
        for entry in text_json:
            speaker = entry["speaker"]
            message = entry["message"]

            # Generate audio for the current message and speaker
            audio = await self.synth.tts(message, speaker)
            audio_segments.append(audio)

        

    print("WAV file generated successfully.")
    @Slot(str)
    def append_broadcast_info(self):
        pass