## timeline.py
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot
import zstd, json
import pandas as pd
from datetime import datetime

class TimelineManager(QObject):
    meteStatusChanged = Signal()
    def __init__(self,parent=None):
        super().__init__(parent)
        """タイムラインデータを管理するクラス"""
        self.mete_timeline = {}  # タイムラインデータを格納するリスト
        self.seis_timeline = {}  # タイムラインデータを格納するリスト
        self.volc_timeline = {}  # タイムラインデータを格納するリスト

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
        #print(self.mete_status[self.hierarchy[3]]['100011'])

    def add_entry(self, id, data):
        """
        パースされたデータをタイムラインに追加
        
        Args:
            data: パース結果の辞書（jma_base_parserの出力形式）
        """
        if data["category"]=="meteorology":
            self.mete_timeline[id]=data
        if data["category"]=="seismology":
            self.seis_timeline[id]=data
        if data["category"]=="volcanology":
            self.volc_timeline[id]=data
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
                        #print(areacode)
                        #print(item[areacode])
                        try:
                            self.mete_status[hier][areacode]["warning_level"]=warning_level
                            self.mete_status[hier][areacode]["status"]=item[areacode]
                            self.mete_status[hier][areacode]["id"]=id
                        except:
                            print(f"key error at area code {areacode}" )
            #print(self.mete_status["pref"])
            self.meteStatusChanged.emit()
        
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

    @Slot(str, str, result=int)
    def getMeteWarningLevel(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            status_list = self.mete_status[hierarchy][code]["status"]
            special_rain=["33"]
            emergency=["32","35","36","37","38","08","do","ta_ob"]
            warning = ["02","03","04","05","06","07","19","ta"]
            caution = ["10","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27"]
            for item in special_rain:
                if item in status_list:
                    return 5
            for item in emergency:
                if item in status_list:
                    return 4
            for item in warning:
                if item in status_list:
                    return 3
            for item in caution:
                if item in status_list:
                    return 2
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return 0
        
    @Slot(str, str, result=list)
    def getMeteWarningCode(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            warning_textlist = self.mete_status[hierarchy][code]["status"]
            return warning_textlist
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return []

    @Slot(str, str, result=list)
    def getMeteWarningName(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        warning_code = {
            "00": "発表なし",
            "02": "暴風雪警報",
            "03": "大雨警報",
            "04": "洪水警報",
            "05": "暴風警報",
            "06": "大雪警報",
            "07": "波浪警報",
            "08": "高潮警報",
            "10": "大雨注意報",
            "12": "大雪注意報",
            "13": "風雪注意報",
            "14": "雷注意報",
            "15": "強風注意報",
            "16": "波浪注意報",
            "17": "融雪注意報",
            "18": "洪水注意報",
            "19": "高潮注意報",
            "20": "濃霧注意報",
            "21": "乾燥注意報",
            "22": "なだれ注意報",
            "23": "低温注意報",
            "24": "霜注意報",
            "25": "着氷注意報",
            "26": "着雪注意報",
            "27": "その他の注意報",
            "32": "暴風雪特別警報",
            "33": "大雨特別警報",
            "35": "暴風特別警報",
            "36": "大雪特別警報",
            "37": "波浪特別警報",
            "38": "高潮特別警報"
        }
        try:
            warning_textlist = [warning_code[wcode] for wcode in self.mete_status[hierarchy][code]["status"]]
            return warning_textlist
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return []
    @Slot(str,str,result=list)
    def getParentAreaCode(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            if hierarchy=="pref":
                return ["",""]
            if hierarchy=="class10":
                return ["pref",self.mete_status[hierarchy][code]["parent"]]
            if hierarchy=="class15":
                return ["class10",self.mete_status[hierarchy][code]["parent"]]
            if hierarchy=="class20":
                return ["class15",self.mete_status[hierarchy][code]["parent"]]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""

    @Slot(str,str,result=str)
    def getAreaName(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            return self.mete_status[hierarchy][code]["name"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    @Slot(str,str,result=str)
    def getID(self, hierarchy, code):
        """情報IDを取得"""
        try:
            return self.mete_status[hierarchy][code]["id"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    @Slot(str,str,result=str)
    def getHeadlineText(self, hierarchy, code):
        """情報IDを取得"""
        try:
            id=self.getID(hierarchy,code)
            return self.mete_timeline[id]["headline_text"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return "現在、発表されている情報はありません。"
        
    @Slot(str,str,result=str)
    def getPrefName(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        hokkaido=["宗谷地方",
                  "網走・北見・紋別地方",
                  "釧路・根室地方",
                  "十勝地方",
                  "上川・留萌地方",
                  "胆振・日高地方",
                  "渡島・檜山地方",
                  "石狩・空知・後志地方"]
        kagoshima=["鹿児島県（奄美地方除く）","奄美地方"]
        okinawa=["沖縄本島地方","宮古島地方","八重山地方","大東島地方"]
        try:
            if hierarchy=="pref":
                name = self.getAreaName(hierarchy,code)
                if name in hokkaido:
                    return "北海道"
                elif name in kagoshima:
                    return "鹿児島県"
                elif name in okinawa:
                    return "沖縄県"
                else:
                    return name
            else:
                parent1 = self.getParentAreaCode(hierarchy,code)
                return self.getPrefName(parent1[0],parent1[1])
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""