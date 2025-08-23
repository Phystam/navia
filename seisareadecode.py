## timeline.py
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot
import zstd, json,os
import pandas as pd
import datetime

coded={}
coded["prefs"]={}
coded["class10s"]={}
prefnames=[]
prefcodes=[]
parentnames=[]
with open("geo/緊急地震速報／府県予報区.geojson","rb") as f:
    geo_txt=f.read()
    geo=json.loads(geo_txt)

childrencodes={}
for features in geo["features"]:
    code=features["properties"]["code"]
    name=features["properties"]["name"]
    prefnames.append(name)
    prefcodes.append(code)
    childrencodes[code]=[]

with open("geo/地震情報／細分区域.json","rb") as f:
    geo2_txt=f.read()
    geo2=json.loads(geo2_txt)



for features in geo2["features"]:
    code=features["properties"]["code"]
    name=features["properties"]["name"]
    coded["class10s"][code]={}
    coded["class10s"][code]["name"]=name
    for i,pref in enumerate(prefnames):
        if pref in name:
            coded["class10s"][code]["parent"]=prefcodes[i]
            childrencodes[prefcodes[i]].append(code)

for features in geo["features"]:
    code=features["properties"]["code"]
    name=features["properties"]["name"]
    coded["prefs"][code]={}
    coded["prefs"][code]["name"]=name
    coded["prefs"][code]["children"]=childrencodes[code]
    
#print(coded)
        
with open("settings/seis_areacode.json","w",encoding="utf-8") as f:
    json.dump(coded,f,ensure_ascii=False, indent=2)