import json
import ollama
import zstd
import re
import io
import sys
#from PySide6.QtMultimedia import QMediaPlayer, QMediaContent
#from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
import pydub
API_SERVER_URL = "http://ne:11434"

def main():
    #Synthesizer初期化
    voicevox_onnxruntime_path= r"./voicevox_core/onnxruntime/lib/" + Onnxruntime.LIB_VERSIONED_FILENAME
    open_jtalk_dict_dir = r"./voicevox_core/dict/open_jtalk_dic_utf_8-1.11"
    Synth = Synthesizer(Onnxruntime.load_once(filename=voicevox_onnxruntime_path),OpenJtalk(open_jtalk_dict_dir))
    with VoiceModelFile.open(r"./voicevox_core/models/vvms/0.vvm") as model:
        Synth.load_voice_model(model)
    
    model="qwen3:14b"
    files=["jmadata/20250729044149_0_VPTI51_010000.xml.zst",
           #"jmadata/20250717075726_0_VPZJ50_010000.xml.zst",
           #"jmadata/20250717072031_0_VPCJ50_340000.xml.zst",
           #"jmadata/20250717071541_0_VPCJ50_130000.xml.zst",
           #"jmadata/20250717071527_0_VPCJ50_230000.xml.zst"
           ] #["jmadata/20250709080017_0_VPFJ50_400000.xml"]
    xmltexts=""
    for file in files:
        with open(file,'rb') as f:
            xmltexts=xmltexts+zstd.decompress(f.read()).decode(encoding='utf-8')
    input = [{"role": "user",
            "content": 
'''以下の複数のxmlファイルをすべて総合して要約し、天気予報のラジオ(あるいはテレビ)風に日本語で気象情報を伝える原稿を作ってください。
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
最後は「以上、◯◯県(◯◯地方)の気象情報でした。」で締めくくってください。\\no_think'''
            }]

    input.append({"role": "user",
     "content": xmltexts
     })
    print(input)
    
    client = ollama.Client(host=API_SERVER_URL)
    print("sending...")
    response = client.chat(model=model, messages=input)
    print("waiting...")
    #テキストを整形
    text=re.sub(r"<.+>[\s\S\n]+</.+>","",response["message"]["content"])
    text=re.sub(r"```(json)?","",text)
    print(text)
    jsonfile=json.loads(text)
    print(jsonfile)
    #メッセージ読み上げ
    style_id=0
    
    aseg = None
    for t in jsonfile["script"]:
        txt= t["text"]
        wav=Synth.tts(txt,style_id)
        awav = pydub.AudioSegment.from_wav(io.BytesIO(wav))
        if aseg is None:
            aseg = awav
        else:
            aseg += awav
    aseg.export("output_combined.wav",format="wav")


    
     

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.quit()
