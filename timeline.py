# timeline.py
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot
import zstd, json
import pandas as pd
from datetime import datetime

class TimelineManager(QObject):
    def __init__(self,parent=None):
        #super().__init__(self)
        """タイムラインデータを管理するクラス"""
        self.mete_timeline = []  # タイムラインデータを格納するリスト
        self.seis_timeline = []  # タイムラインデータを格納するリスト
        self.volc_timeline = []  # タイムラインデータを格納するリスト

        self.mete_status = {}  # タイムラインデータを格納するリスト
        self.seis_status = {}  # タイムラインデータを格納するリスト
        self.volc_status = {}  # タイムラインデータを格納するリスト

        self.areacode={}
        with open("settings/area.json.zst","rb") as f:
            area_txt=zstd.decompress(f.read())
            self.areacode=json.loads(area_txt)
        region_codes=list(self.areacode["centers"].keys())
        pref_codes=list(self.areacode["offices"].keys())
        class10_codes=list(self.areacode["class10s"].keys())
        class15_codes=list(self.areacode["class15s"].keys())
        class20_codes=list(self.areacode["class20s"].keys())
        self.hierarchy=["region","pref","class10","class15","class20"]
        for hier in self.hierarchy:
            self.mete_status[hier] ={}

        for c in region_codes:
            name = self.areacode["centers"][c]["name"]
            children = self.areacode["centers"][c]["children"]
            l= {"name":name,
                "parent":"",
                "children": children,
                "status": ["00"],
                "warning_level":0,
                "updated": datetime(2000,1,1)
                }
            self.mete_status[self.hierarchy[0]][c]=l
        for c in pref_codes:
            name = self.areacode["offices"][c]["name"]
            children = self.areacode["offices"][c]["children"]
            par = self.areacode["offices"][c]["parent"]
            l={"name":name,
                    "parent":par,
                    "children": children,
                    "status": ["00"],
                    "warning_level":0,
                    "updated": datetime(2000,1,1)
                    }
            self.mete_status[self.hierarchy[1]][c]=l
        for c in class10_codes:
            name = self.areacode["class10s"][c]["name"]
            children = self.areacode["class10s"][c]["children"]
            par = self.areacode["class10s"][c]["parent"]
            l={"name":name,
               "parent":par,
               "children": children,
               "status": ["00"],
               "warning_level":0,
               "updated": datetime(2000,1,1)}
            self.mete_status[self.hierarchy[2]][c]=l
        for c in class15_codes:
            name = self.areacode["class15s"][c]["name"]
            children = self.areacode["class15s"][c]["children"]
            par = self.areacode["class15s"][c]["parent"]
            l={"name":name,
               "parent":par,
               "children": children,
               "status": ["00"],
               "warning_level":0,
               "updated": datetime(2000,1,1)}
            self.mete_status[self.hierarchy[3]][c]=l
        for c in class20_codes:
            name = self.areacode["class20s"][c]["name"]
            par = self.areacode["class20s"][c]["parent"]
            l={
               "name":name,
               "parent":par,
               "children": [],
               "status": ["00"],
               "warning_level":0,
               "updated": datetime(2000,1,1)}
            self.mete_status[self.hierarchy[4]][c]=l
        print(self.mete_status[self.hierarchy[3]]['100011'])

    def add_entry(self, data):
        """
        パースされたデータをタイムラインに追加
        
        Args:
            data: パース結果の辞書（jma_base_parserの出力形式）
        """
        if data["category"]=="meteorology":
            self.mete_timeline.append(data)
        if data["category"]=="seismology":
            self.seis_timeline.append(data)
        if data["category"]=="volcanology":
            self.volc_timeline.append(data)
        #vpww54
        if data["data_type"]=="VPWW54":
            dt=data["report_datetime"]
            warning_level=data["warning_level"]
            for hier in self.hierarchy:
                if hier=="region":
                    continue
                for item in data[hier]:
                    areacodes = item.keys()
                    for areacode in areacodes:
                        print(areacode)
                        print(item[areacode])
                        self.mete_status[hier][areacode]["warning_level"]=warning_level
                        self.mete_status[hier][areacode]["status"]=item[areacode]
            print(self.mete_status["pref"])
        
    def _format_content(self, data):
        """コンテンツの整形（ヘッドライン＋本文の統合）"""
        return f"{data.get('headline_text', '')}\n\n{data.get('body_text', '')}"
    
    def get_all_entries(self):
        """すべてのタイムラインエントリを取得"""
        return self.timeline
    
    def find_by_area(self, area):
        """指定されたエリアのエントリをフィルタリング"""
        return [entry for entry in self.timeline if entry['area'] == area]
    
    def find_by_date(self, date):
        """指定された日付のエントリをフィルタリング"""
        target_date = datetime(date.year, date.month, date.day)
        return [entry for entry in self.timeline 
                if entry['timestamp'].date() == target_date.date()]

# サンプルデータ構造（テスト用）
sample_entry = {
    'title': '地震情報',
    'datetime': '2025-07-25T10:00:00',
    'publishing_office': '気象庁',
    'area': '関東地方',
    'headline_text': '最大級の警戒',
    'body_text': '東京湾を震源とする地震が発生しました。',
    'data_type': 'VPZJ50'
}