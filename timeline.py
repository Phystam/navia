## timeline.py
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot
import zstd, json,os
import pandas as pd
import datetime
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
        self.jst = datetime.timezone(datetime.timedelta(hours=9))
        self.areacode={}
        
        #with open("settings/area.json.zst","rb") as f:
        #    area_txt=zstd.decompress(f.read())
        #    self.areacode=json.loads(area_txt)
        with open("settings/area.json","rb") as f:
            area_txt=f.read()
            self.areacode=json.loads(area_txt)
        with open("settings/area_decode.json","rb") as f:
            area_txt=f.read()
            self.area_decode=json.loads(area_txt)
        region_codes=list(self.areacode["centers"].keys())
        pref_codes=list(self.areacode["prefs"].keys())
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
                "updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst)
                }
            self.mete_status[self.hierarchy[0]][c]=l
        for c in pref_codes:
            name = self.areacode["prefs"][c]["name"]
            children = self.areacode["prefs"][c]["children"]
            par = self.areacode["prefs"][c]["parent"]
            l={ "name":name,
                "parent":par,
                "children": children,
                "status": ["00"],
                "id": "",
                "VXWW50_status": ["1"],
                "VXWW50_id": "",
                "VPHW51_status": ["0"],
                "VPHW51_id": "",
                "warning_level":0,
                "updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VXWW50_updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VPHW51_updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VPHW51_valid": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst)
                    }
            self.mete_status[self.hierarchy[1]][c]=l
        for c in class10_codes:
            name = self.areacode["class10s"][c]["name"]
            children = self.areacode["class10s"][c]["children"]
            par = self.areacode["class10s"][c]["parent"]
            l={ "name":name,
                "parent":par,
                "children": children,
                "status": ["00"],
                "id": "",
                "VXWW50_status": ["1"],
                "VXWW50_id": "",
                "VPHW51_status": ["0"],
                "VPHW51_id": "",
                "warning_level":0,
                "updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VXWW50_updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VPHW51_updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VPHW51_valid": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst)
            }
            self.mete_status[self.hierarchy[2]][c]=l
        for c in class15_codes:
            name = self.areacode["class15s"][c]["name"]
            children = self.areacode["class15s"][c]["children"]
            par = self.areacode["class15s"][c]["parent"]
            l={ "name":name,
                "parent":par,
                "children": children,
                "status": ["00"],
                "id": "",
                "VXWW50_status": ["1"],
                "VXWW50_id": "",
                "VPHW51_status": ["0"],
                "VPHW51_id": "",
                "warning_level":0,
                "updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VXWW50_updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VPHW51_updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VPHW51_valid": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst)
            }
            self.mete_status[self.hierarchy[3]][c]=l
        for c in class20_codes:
            name = self.areacode["class20s"][c]["name"]
            par = self.areacode["class20s"][c]["parent"]
            l={ "name":name,
                "parent":par,
                "children": [],
                "status": ["00"],
                "id": "",
                "VXWW50_status": ["1"],
                "VXWW50_id": "",
                "VPHW51_status": ["0"],
                "VPHW51_id": "",
                "warning_level":0,
                "updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VXWW50_updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VPHW51_updated": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst),
                "VPHW51_valid": datetime.datetime(2000,1,1,0,0,0,tzinfo=self.jst)
            }
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
            self.VPWW54(id,data)
            #print(self.mete_status["pref"])
            self.meteStatusChanged.emit()
        if data["data_type"]=="VXWW50":
            self.VXWW50(id,data)
            #print(self.mete_status["pref"])
            self.meteStatusChanged.emit()
        if data["data_type"]=="VPHW51":
            self.VPHW51(id,data)
            #print(self.mete_status["pref"])
            self.meteStatusChanged.emit()
        if data["data_type"]=="VPOA50":
            self.VPOA50(id,data)
            #print(self.mete_status["pref"])
            self.meteStatusChanged.emit()
        
        if data["data_type"]=="VPFJ50" or data["data_type"]=="VPFG50":
            self.VPZJ50(id,data)
            #print(self.mete_status["pref"])
            #self.meteStatusChanged.emit()
        if data["data_type"]=="VPFD51":
            self.VPFD51(id,data)
            #print(self.mete_status["pref"])
            #self.meteStatusChanged.emit()
            
    def VPWW54(self,id,data):
        dt=data["report_datetime"]
        for hier in self.hierarchy:
            if hier=="region":
                continue
            for item in data[hier]:
                areacodes = item.keys()
                for areacode in areacodes:
                    #print(f"{dt}, {self.mete_status[hier][areacode]['updated']}")
                    try:
                        if self.mete_status[hier][areacode]["updated"] < dt:
                            self.mete_status[hier][areacode]["updated"]=dt
                            self.mete_status[hier][areacode]["status"].clear()
                            self.mete_status[hier][areacode]["status"]=item[areacode]
                            self.mete_status[hier][areacode]["id"]=id
                    except:
                        print(f"key error at area code {areacode}" )
    
    def VXWW50(self,id,data):
        #土砂災害警戒情報はclass20のみ発表。親地域に伝播させる
        dt=data["report_datetime"]
        for hier in self.hierarchy:
            if hier!="class20" :
                continue
            
            for item in data[hier]:
                areacodes = item.keys()
                for areacode in areacodes:
                    #print(f"{dt}, {self.mete_status[hier][areacode]['updated']}")
                    try:
                        if self.mete_status[hier][areacode]["VXWW50_updated"] < dt:
                            self.mete_status[hier][areacode]["VXWW50_updated"]=dt
                            if item[areacode] == ["3"]:
                                self.mete_status[hier][areacode]["VXWW50_status"]=item[areacode]
                                self.mete_status[hier][areacode]["VXWW50_id"]=id
                                #親地域に伝播させる
                                parent_hier=hier
                                parent_areacode=areacode
                                while True:
                                    parent_areacode=self.mete_status[parent_hier][parent_areacode]["parent"]
                                    parent_hier=self.getParent(parent_hier)
                                    if parent_hier=="":
                                        break
                                    self.mete_status[parent_hier][parent_areacode]["VXWW50_updated"]=dt
                                    self.mete_status[parent_hier][parent_areacode]["VXWW50_status"]=item[areacode]
                                    self.mete_status[parent_hier][parent_areacode]["VXWW50_id"]=id
                                #hier=parent_hier
                                #areacode=parent_areacode
                            else:
                                self.mete_status[hier][areacode]["VXWW50_status"]=item[areacode]
                                self.mete_status[hier][areacode]["VXWW50_id"]=""
                    except:
                        print(f"key error at area code {areacode}" )
    
    def VPHW51(self,id,data):
        dt=data["report_datetime"]
        for hier in self.hierarchy:
            if hier=="region":
                continue
            for item in data[hier]:
                areacodes = item.keys()
                for areacode in areacodes:
                    #print(f"{dt}, {self.mete_status[hier][areacode]['updated']}")
                    try:
                        if self.mete_status[hier][areacode]["VPHW51_updated"] < dt:
                            self.mete_status[hier][areacode]["VPHW51_updated"]=dt
                            self.mete_status[hier][areacode]["VPHW51_valid"]=data["valid_datetime"]
                            self.mete_status[hier][areacode]["VPHW51_status"]=item[areacode]
                            self.mete_status[hier][areacode]["VPHW51_id"]=id
                    except:
                        print(f"key error at area code {areacode}" )
                        
    def VPOA50(self,id,data):
        dt=data["report_datetime"]
        for hier in self.hierarchy:
            if hier=="region":
                continue
            for item in data["pref"]:
                areacodes = item.keys()
                for areacode in areacodes:
                    #print(f"{dt}, {self.mete_status[hier][areacode]['updated']}")
                    try:
                        self.mete_status[hier][areacode]["VPOA50_updated"]=dt
                        self.mete_status[hier][areacode]["VPOA50_id"]=id
                        #子に伝播させる
                        self.appendForAllChildren(hier,areacode,dt,id)
                    except:
                        print(f"key error at area code {areacode}" )
                        
    def VPZJ50(self,id,data):
        dt=data["report_datetime"]
        hier=data["hier"]
        areacode=""
        for item in self.area_decode.keys():
            if item in data["head_title"]:
                areacode=self.area_decode[item]
        if data["data_type"]=="VPFG50":
            areacode=data['areacode']
        print(f"{data['data_type']} {data['head_title']}: areacode={areacode}")

        self.mete_status[hier][areacode][f"{data['data_type']}_updated"]=dt
        self.mete_status[hier][areacode][f"{data['data_type']}_id"]=id
        #子に伝播させる
        self.appendForAllChildren(hier,areacode,dt,id,prefix=data["data_type"])
        
    def VPFD51(self,id,data):
        dt=data["report_datetime"]
        hier=data["hier"]
        areacode=""
        for item in self.area_decode.keys():
            if item in data["head_title"]:
                areacode=self.area_decode[item]
        print(f"{data['data_type']} {data['head_title']}: areacode={areacode}")
        print(areacode)
        self.mete_status[hier][areacode][f"{data['data_type']}_updated"]=dt
        self.mete_status[hier][areacode][f"{data['data_type']}_id"]=id
        #子に伝播させる
        self.appendForAllChildren(hier,areacode,dt,id,prefix=data["data_type"])
    
    def appendForAllChildren(self,hier,areacode,dt,id,prefix="VPOA50"):
        child_hier=self.getChild(hier)
        if child_hier=="":
            return
        child_areacodes=self.mete_status[hier][areacode]["children"]
        for child_areacode in child_areacodes:
            self.mete_status[child_hier][child_areacode][f"{prefix}_updated"]=dt
            self.mete_status[child_hier][child_areacode][f"{prefix}_id"]=id
            self.appendForAllChildren(child_hier,child_areacode,dt,id,prefix)
    
    def getParent(self,hier):
        if hier=="pref" or hier=="region":
            return ""
        if hier=="class10":
            return "pref"
        if hier=="class15":
            return "class10"
        if hier=="class20":
            return "class15"
    
    def getChild(self,hier):
        if hier=="pref":
            return "class10"
        if hier=="class10":
            return "class15"
        if hier=="class15":
            return "class20"
        if hier=="class20":
            return ""

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
            VXWW50_status_list = self.mete_status[hierarchy][code]["VXWW50_status"]
            VPHW51_status_list = self.mete_status[hierarchy][code]["VPHW51_status"]
            special_rain=["33"]
            emergency=["32","35","36","37","38","08"]
            VXWW50_emergency=["3"]
            warning = ["02","03","04","05","06","07","19"]
            VPHW51_warning = ["1"]
            caution = ["10","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27"]
            for item in special_rain:
                if item in status_list:
                    return 5
            for item in emergency:
                if item in status_list:
                    return 4
            for item in VXWW50_emergency:
                if item in VXWW50_status_list:
                    return 4
            for item in warning:
                if item in status_list:
                    return 3
            for item in VPHW51_warning:
                if item in VPHW51_status_list:
                    return 3
            for item in caution:
                if item in status_list:
                    return 2
            return 0
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

    @Slot(str,str,result=list)
    def getMeteWarningLogoPath(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            item = self.mete_status[hierarchy][code]['status']
            warning_textlist = [f"../materials/code{item[i]}.svg" for i in range(len(item))]
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
    def getUpdated(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            dt: datetime.datetime =self.mete_status[hierarchy][code]["updated"]
            text = dt.strftime("%Y/%m/%d %H:%M:%S")
            if text != "2000/01/01 00:00:00":
                return text
            else:
                return ""
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
            return ""
        
    @Slot(str,str,result=str)
    def getTitle(self, hierarchy, code):
        """情報IDを取得"""
        try:
            id=self.getID(hierarchy,code)
            return self.mete_timeline[id]["head_title"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    @Slot(str,str,result=str)
    def getPrefName(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        hokkaido=["宗谷地方",
                  "網走・北見・紋別地方",
                  "釧路・根室地方",
                  "釧路地方",
                  "根室地方",
                  "十勝地方",
                  "上川・留萌地方",
                  "上川地方",
                  "留萌地方",
                  "胆振・日高地方",
                  "胆振地方",
                  "日高地方",
                  "渡島・檜山地方",
                  "檜山地方",
                  "渡島地方",
                  "石狩・空知・後志地方",
                  "石狩地方",
                  "空知地方",
                  "後志地方"]
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
    
    @Slot(str,str,result=str)
    def getVXWW50ID(self, hierarchy, code):
        """情報IDを取得"""
        try:
            return self.mete_status[hierarchy][code]["VXWW50_id"]
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    
    @Slot(str,str,result=str)
    def getVXWW50Updated(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            dt: datetime.datetime =self.mete_status[hierarchy][code]["VXWW50_updated"]
            text = dt.strftime("%Y/%m/%d %H:%M:%S")
            if text != "2000/01/01 00:00:00":
                return text
            else:
                return ""
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    @Slot(str,str,result=str)
    def getVXWW50Title(self,hierarchy, code):
        """情報IDを取得"""
        try:
            id=self.getVXWW50ID(hierarchy,code)
            return self.mete_timeline[id]["head_title"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    @Slot(str,str,result=str)
    def getVXWW50HeadlineText(self,hierarchy, code):
        """情報IDを取得"""
        try:
            id=self.getVXWW50ID(hierarchy,code)
            return self.mete_timeline[id]["headline_text"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    @Slot(str,str,result=list)
    def getVXWW50LogoPath(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            item = self.mete_status[hierarchy][code]['VXWW50_status']
            warning_textlist = [f"../materials/doshasaigai.svg"] if item==['3'] else []
            return warning_textlist
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return []
        
    @Slot(str,str,result=list)
    def getVXWW50WarningCode(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            item = self.mete_status[hierarchy][code]['VXWW50_status']
            return item
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return []

    #VPHW51 竜巻注意情報
    @Slot(str,str,result=bool)
    def checkVPHW51(self, hierarchy, code):
        """valid datetimeと比較"""
        try:
            dt=self.mete_status[hierarchy][code]["VPHW51_valid"]
            now = datetime.datetime.now(tz=self.jst)
            if dt < now:
                self.mete_status[hierarchy][code]["VPHW51_id"]=""
                self.mete_status[hierarchy][code]["VPHW51_status"]="0"
                self.mete_status[hierarchy][code]["VPHW51_updated"]=dt
                self.mete_status[hierarchy][code]["VPHW51_valid"]=dt
                return False
            return True
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    @Slot(str,str,result=str)
    def getVPHW51ID(self, hierarchy, code):
        """情報IDを取得"""
        try:
            return self.mete_status[hierarchy][code]["VPHW51_id"]
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    
    @Slot(str,str,result=str)
    def getVPHW51Updated(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            dt: datetime.datetime =self.mete_status[hierarchy][code]["VPHW51_updated"]
            text = dt.strftime("%Y/%m/%d %H:%M:%S")
            if text != "2000/01/01 00:00:00":
                return text
            else:
                return ""
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    @Slot(str,str,result=str)
    def getVPHW51Title(self,hierarchy, code):
        """情報IDを取得"""
        try:
            id=self.getVPHW51ID(hierarchy,code)
            return self.mete_timeline[id]["head_title"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    @Slot(str,str,result=str)
    def getVPHW51HeadlineText(self,hierarchy, code):
        """情報IDを取得"""
        try:
            id=self.getVPHW51ID(hierarchy,code)
            return self.mete_timeline[id]["headline_text"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    @Slot(str,str,result=list)
    def getVPHW51LogoPath(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            item = self.mete_status[hierarchy][code]['VPHW51_status']
            warning_textlist = [f"../materials/tatsumaki.svg"] if item==['1'] else []
            return warning_textlist
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return []
        
    @Slot(str,str,result=list)
    def getVPHW51WarningCode(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            item = self.mete_status[hierarchy][code]['VPHW51_status']
            return item
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return []
        
    #VPOA50 記録的短時間大雨情報
    @Slot(str,str,result=str)
    def getVPOA50ID(self, hierarchy, code):
        """情報IDを取得"""
        try:
            return self.mete_status[hierarchy][code]["VPOA50_id"]
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    
    @Slot(str,str,result=str)
    def getVPOA50Updated(self, hierarchy, code):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            dt: datetime.datetime =self.mete_status[hierarchy][code]["VPOA50_updated"]
            text = dt.strftime("%Y/%m/%d %H:%M:%S")
            if text != "2000/01/01 00:00:00":
                return text
            else:
                return ""
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    @Slot(str,str,result=str)
    def getVPOA50Title(self,hierarchy, code):
        """情報IDを取得"""
        try:
            id=self.getVPOA50ID(hierarchy,code)
            return self.mete_timeline[id]["head_title"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    @Slot(str,str,result=str)
    def getVPOA50HeadlineText(self,hierarchy, code):
        """情報IDを取得"""
        try:
            id=self.getVPOA50ID(hierarchy,code)
            return self.mete_timeline[id]["headline_text"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    # VPZJ50
    @Slot(str,str,str,result=str)
    def getVPZJ50ID(self, hierarchy, code, data_type):
        """情報IDを取得"""
        try:
            return self.mete_status[hierarchy][code][f"{data_type}_id"]
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    
    @Slot(str,str,str,result=str)
    def getVPZJ50Updated(self, hierarchy, code, data_type):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            dt: datetime.datetime =self.mete_status[hierarchy][code][f"{data_type}_updated"]
            text = dt.strftime("%Y/%m/%d %H:%M:%S")
            if text != "2000/01/01 00:00:00":
                return text
            else:
                return ""
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        except:
            return ""
    @Slot(str,str,str,result=str)
    def getVPZJ50Title(self,hierarchy, code, data_type):
        """情報IDを取得"""
        try:
            id=self.getVPZJ50ID(hierarchy,code, data_type)
            return self.mete_timeline[id]["head_title"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    @Slot(str,str,str,result=str)
    def getVPZJ50HeadlineText(self,hierarchy, code, data_type):
        """情報IDを取得"""
        try:
            id=self.getVPZJ50ID(hierarchy,code, data_type)
            return self.mete_timeline[id]["headline_text"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    @Slot(str,str,str,result=str)
    def getVPZJ50BodyText(self,hierarchy, code, data_type):
        """情報IDを取得"""
        try:
            id=self.getVPZJ50ID(hierarchy,code, data_type)
            return self.mete_timeline[id]["body_text"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    # VPFD51
    @Slot(str,str,str,result=str)
    def getVPFD51ID(self, hierarchy, code, data_type):
        """情報IDを取得"""
        try:
            return self.mete_status[hierarchy][code][f"{data_type}_id"]
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    
    @Slot(str,str,str,result=str)
    def getVPFD51Updated(self, hierarchy, code, data_type):
        """指定された階層とコードの警報レベルを取得する"""
        try:
            dt: datetime.datetime =self.mete_status[hierarchy][code][f"{data_type}_updated"]
            text = dt.strftime("%Y/%m/%d %H:%M:%S")
            if text != "2000/01/01 00:00:00":
                return text
            else:
                return ""
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        except:
            return ""
    @Slot(str,str,str,result=str)
    def getVPFD51Title(self,hierarchy, code, data_type):
        """情報IDを取得"""
        try:
            id=self.getVPFD51ID(hierarchy,code, data_type)
            return self.mete_timeline[id]["head_title"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
        
    @Slot(str,str,str,result=str)
    def getVPFD51HeadlineText(self,hierarchy, code, data_type):
        """情報IDを取得"""
        try:
            id=self.getVPFD51ID(hierarchy,code, data_type)
            return self.mete_timeline[id]["headline_text"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""
    @Slot(str,str,str,result=str)
    def getVPFD51BodyText(self,hierarchy, code, data_type):
        """情報IDを取得"""
        try:
            id=self.getVPFD51ID(hierarchy,code, data_type)
            return self.mete_timeline[id]["body_text"]
            
        except KeyError:
            #print(f"Warning: Code {code} not found in hierarchy {hierarchy}")
            return ""