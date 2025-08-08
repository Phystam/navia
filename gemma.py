import json
import ollama
import zstd
import re
import sys
from pydub import AudioSegment
import io
#from PySide6.QtMultimedia import QMediaPlayer, QMediaContent
#from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
API_SERVER_URL = "http://localhost:11434"

def main():
    #Synthesizer初期化
    voicevox_onnxruntime_path= r"./voicevox_core/onnxruntime/lib/" + Onnxruntime.LIB_VERSIONED_FILENAME
    open_jtalk_dict_dir = r"./voicevox_core/dict/open_jtalk_dic_utf_8-1.11"
    Synth = Synthesizer(Onnxruntime.load_once(filename=voicevox_onnxruntime_path),OpenJtalk(open_jtalk_dict_dir))
    with VoiceModelFile.open(r"./voicevox_core/models/vvms/8.vvm") as model:
        Synth.load_voice_model(model)
    with VoiceModelFile.open(r"./voicevox_core/models/vvms/15.vvm") as model:
        Synth.load_voice_model(model)

    model="qwen3:8b"
    files=["jmadata/20250719071046_0_VPCJ50_471000.xml.zst",
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
このとき、読み上げることを考慮して、括弧で括られている部分は文意を損なわないよう適切に処理してください。
最後は「以上、◯◯県(◯◯地方)の気象情報でした。」で締めくくってください。'''
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
    #jsonfile={'script': [{'speaker': 'man', 'text': '2025年7月19日午後7時、沖縄地方の気象情報です。'}, {'speaker': 'woman', 'text': '今後の天候について、詳しくお伝えします。'}, {'speaker': 'man', 'text': '今週末にかけて、台風第6号 の影響が続きます。'}, {'speaker': 'woman', 'text': '特に、沖縄本島地方と先島諸島では21日にかけて強い風が吹き 、海上ではうねりを伴う高波が発生する見込みです。'}, {'speaker': 'man', 'text': '波の高さは、先島諸島で最大5メートル、うねりを伴う状態が予想されています。'}, {'speaker': 'woman', 'text': 'また、先島諸島では落雷や竜巻な どの激しい突風にも十分ご注意ください。'}, {'speaker': 'man', 'text': '風速については、20日から21日にかけて、 沖縄本島地方と先島諸島で最大風速15メートル（瞬間風速25メートル）の強風が吹く見込みです。'}, {'speaker': 'woman', 'text': '雨量も気になります。先島諸島では20日にかけて1時間に30ミリもの大雨が予想されています。'}, {'speaker': 'man', 'text': '24時間降水量は、先島諸島で80ミリと、土砂災害や低い土地の浸水に警戒が必要です。'}, {'speaker': 'woman', 'text': '台風と太平洋高気圧の間で気圧の傾きが急なので、南東の風が強く吹く可能性があります。'}, {'speaker': 'man', 'text': '防災のポイントは、うねりを伴う高波や強風に備え、屋外での活動を控えることです。'}, {'speaker': 'woman', 'text': '特に先島諸島では、激しい雨や突風に注意し、積乱雲の近づき始めにはすぐに安全な 場所に避難してください。'}, {'speaker': 'man', 'text': '今後の情報は、20日午前5時頃に発表される「大雨と強風及び高波に関する沖縄地方気象情報」をご確認ください。'}, {'speaker': 'woman', 'text': '以上、沖縄地方の気象情報 でした。'}]}
    print(text)
    jsonfile=json.loads(text)
    print(jsonfile)
    #メッセージ読み上げ
    #style_id=0
    wavs=[]
    for line in jsonfile["script"]:
        if line["speaker"]=="woman":
            speaker_id=23
        else:
            speaker_id=81
        wav_bytes=Synth.tts(line["text"],speaker_id)
        audio = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
        wavs.append(audio)

    # 全てのAudioSegmentを結合
    if wavs:
        combined = wavs[0]
        for seg in wavs[1:]:
            combined += seg
        combined.export("output.wav", format="wav")
    
     

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.quit()
