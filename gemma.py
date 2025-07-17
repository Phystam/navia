import requests
import json
import ollama
import zstd
API_SERVER_URL = "http://localhost:11434/api/chat"

def main():
    headers = {"Content-Type": "application/json"}
    model="deepseek-r1"
    files=[#"jmadata/20250717125051_0_VPCJ50_230000.xml.zst",
           #"jmadata/20250717075726_0_VPZJ50_010000.xml.zst",
           #"jmadata/20250717072031_0_VPCJ50_340000.xml.zst",
           #"jmadata/20250717071541_0_VPCJ50_130000.xml.zst",
           "jmadata/20250717071527_0_VPCJ50_230000.xml.zst"
           ] #["jmadata/20250709080017_0_VPFJ50_400000.xml"]
    xmltexts=[]
    for file in files:
        with open(file,'rb') as f:
            xmltexts.append(zstd.decompress(f.read()))
    input = [{"role": "user",
            "content": 
'''以下のxmlファイルを要約して、天気予報のラジオ(あるいはテレビ)風に日本語で気象情報を伝える原稿を作ってください。
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
まず、「m月d日、H時の◯◯県気象情報です。」などのように、発表日時とタイトルを読み上げます。時間や場所は実際のXMLのデータに合わせて修正してください。
その後、ヘッドラインや本文に書かれている情報をもとに、わかりやすく解説を始めてください。
最後は「以上、◯◯県の気象情報でした。」で締めくくってください。'''
            }]
    for xmltext in xmltexts:
        input.append({"role": "user",
             "content": xmltext
             })
    print(input)
    print("sending...")
    response = ollama.chat(model=model, messages=input)
    print("waiting...")
    print(response["message"]["content"])

main()
'''   '''