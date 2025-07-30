import json
import ollama
import zstd
import re
import io
import sys
import os
from lxml import etree
from lxml.etree import XMLSchema, XMLParser, parse, Resolver
#from PySide6.QtMultimedia import QMediaPlayer, QMediaContent
#from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile

from pydub import AudioSegment
# 既存のコードに加えて、以下のインポートを追加
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication
#from pydub.playback import play
API_SERVER_URL = "http://localhost:11434"

class LocalXSDResolver(Resolver):
    def __init__(self, xsd_base_dir):
        super().__init__()
        self.xsd_base_dir = xsd_base_dir
        # JMAの共通名前空間URIとローカルXSDパスの明示的なマッピング
        self.uri_to_local_map = {
            "http://xml.kishou.go.jp/jmaxml1/": os.path.join("jmaxml1", "jmx.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/informationBasis1/": os.path.join("jmaxml1", "informationBasis1", "jma_ib.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/body/seismology1/": os.path.join("jmaxml1", "body", "seismology1", "jma_seis.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/body/seismology1/": os.path.join("jmaxml1", "body", "seismology1", "jma_seis.xsd"), # バージョン付きURIの場合
            "http://xml.kishou.go.jp/jmaxml1/body/volcanology1/": os.path.join("jmaxml1", "body", "volcanology1", "jma_volc.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/body/meteorology1/": os.path.join("jmaxml1", "body", "meteorology1", "jma_mete.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/elementBasis1/": os.path.join("jmaxml1", "elementBasis1", "jma_eb.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/body/addition1/": os.path.join("jmaxml1", "body", "addition1", "jma_add.xsd"),
            # 他のスキーマもここに追加
        }
        #print(f"LocalXSDResolver initialized with xsd_base_dir: {self.xsd_base_dir}")

    def resolve(self, url, public_id, context):

        # URLがJMAの名前空間URIで、ローカルXSDにマッピングされている場合
        for uri_prefix, relative_path in self.uri_to_local_map.items():
            if url.startswith(uri_prefix):
                local_path = os.path.join(self.xsd_base_dir, relative_path)
                if os.path.exists(local_path):
                    print(f"Resolved JMA URI '{url}' to local file: {local_path}")
                    return self.resolve_filename(local_path, context)
        
        # それ以外の場合はデフォルトのリゾルバーにフォールバック
        return super().resolve(url, public_id, context)
    
def main():
    #Synthesizer初期化
    voicevox_onnxruntime_path= r"./voicevox_core/onnxruntime/lib/" + Onnxruntime.LIB_VERSIONED_FILENAME
    open_jtalk_dict_dir = r"./voicevox_core/dict/open_jtalk_dic_utf_8-1.11"
    Synth = Synthesizer(Onnxruntime.load_once(filename=voicevox_onnxruntime_path),OpenJtalk(open_jtalk_dict_dir))
    with VoiceModelFile.open(r"./voicevox_core/models/vvms/4.vvm") as model:
        Synth.load_voice_model(model)
    with VoiceModelFile.open(r"./voicevox_core/models/vvms/6.vvm") as model:
        Synth.load_voice_model(model)
    model="qwen3:30b-a3b"
    files=["jmadata/20250727141849_0_VPCJ50_460100.xml.zst",
           #"jmadata/20250717075726_0_VPZJ50_010000.xml.zst",
           #"jmadata/20250717072031_0_VPCJ50_340000.xml.zst",
           #"jmadata/20250717071541_0_VPCJ50_130000.xml.zst",
           #"jmadata/20250717071527_0_VPCJ50_230000.xml.zst"
           ] #["jmadata/20250709080017_0_VPFJ50_400000.xml"]
    xmltexts=b''
    for file in files:
        with open(file,'rb') as f:
            xmltexts=xmltexts+zstd.decompress(f.read())#.decode(encoding='utf-8')
    xsd_dir = "xsdschema"
    namespaces = {
                'jmx': "http://xml.kishou.go.jp/jmaxml1/",
                'jmx_ib': "http://xml.kishou.go.jp/jmaxml1/informationBasis1/",
                'jmx_seis': "http://xml.kishou.go.jp/jmaxml1/body/seismology1/",
                'jmx_volc': "http://xml.kishou.go.jp/jmaxml1/body/volcanology1/",
                'jmx_mete': "http://xml.kishou.go.jp/jmaxml1/body/meteorology1/",
                'jmx_add': "http://xml.kishou.go.jp/jmaxml1/addition1/",
                'jmx_eb': "http://xml.kishou.go.jp/jmaxml1/elementBasis1/",
                'xsi': "http://www.w3.org/2001/XMLSchema" # xsi名前空間も必要
            }
    parser = etree.XMLParser()
    parser.resolvers.add(LocalXSDResolver(xsd_dir))
    report_tree = etree.fromstring(xmltexts, parser)
    datetime = report_tree.xpath("//jmx_ib:ReportDateTime/text()", namespaces=namespaces)[0]
    title = report_tree.xpath("//jmx_ib:Title/text()", namespaces=namespaces)[0]
    
    headline = report_tree.xpath("//jmx_ib:Headline/jmx_ib:Text/text()", namespaces=namespaces)[0]
    body_text = report_tree.xpath("//jmx_mete:Text/text()", namespaces=namespaces)[0]
    
    token = f"日時: {datetime}\nタイトル: {title}\n見出し: {headline}\n\n {body_text}"

    input = [{"role": "user",
            "content": 
'''\\no_think 以下の複数のxmlファイルをすべて総合して要約し、天気予報のラジオ(あるいはテレビ)風に日本語で気象情報を伝える原稿を作ってください。
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
まず、「m月d日、H時の気象情報です。」のように、発表日時とタイトルを読み上げます。時間や場所は実際のXMLのデータに合わせて修正してください。
年と分は読み上げに含める必要はありません。
その後、ヘッドラインや本文に書かれている情報をもとに、わかりやすく解説を始めてください。
最後は「以上、◯◯県(◯◯地方)の気象情報でした。」で締めくくってください。\\no_think'''
            }]

    input.append({"role": "user",
     "content": token
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
    
    audio_segments =[]
    for t in jsonfile["script"]:
        style_id=11 if t["speaker"]=="man" else 29
        txt= t["text"]
        wav=Synth.tts(txt,style_id)
        audio = AudioSegment(wav)
        audio_segments.append(audio)
    
    # すべてのセグメントを結合
    combined_audio = AudioSegment.empty()
    for segment in audio_segments:
        combined_audio += segment
    
    # 結合した音声を出力
    
    combined_audio.export("output_combined.wav", format="wav")
    #play(combined_audio)
    #with open("output.wav","wb") as f:
    #f.write(combined_audio.)
    # PySide6で音声再生
    #player = QMediaPlayer()
    #url = QUrl.fromLocalFile("output_combined.wav")
    #player.setSource(url)
    #player.play()
     

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.quit()
