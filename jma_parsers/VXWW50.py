# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser
import re
from datetime import datetime,timedelta,timezone
class VXWW50(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.jst = timezone(timedelta(hours=9))
        self.data_type = "VXWW50" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code, test=False):
        """
        気象警報 (VXWW50) のXMLを解析します。
        """
        print(f"気象警報 ({self.data_type}) を解析中...")
        parsed_data = {}
        # Control/Title
        parsed_data["category"]="meteorology"
        parsed_data["data_type"]=self.data_type
        parsed_data['control_title'] = self._get_text(xml_tree, '//jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '//jmx:Control/jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        parsed_data['report_datetime'] = self._get_datetime(xml_tree,'//jmx_ib:ReportDateTime/text()', namespaces) if not test else datetime.now(tz=self.jst)
        headline = self._get_text(xml_tree, '//jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        parsed_data['headline_text']=headline
        notify_level=1
        if "最大級の警戒" in headline or "安全の確保" in headline:
            notify_level=5
        elif "厳重に警戒" in headline:
            notify_level=4
        elif "警戒" in headline:
            notify_level=3
        elif "注意" in headline:
            notify_level=2
        if "解除" in headline:
            notify_level=0
        parsed_data['warning_level']=notify_level
        #class20s
        types=["土砂災害警戒情報"]
        areakeys=["class20"]
        for i,type in enumerate(types):
            codeList=[]
            itemelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item',namespaces)
            lenitem=len(itemelements)
            for j in range(lenitem):
                codeelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{j+1}]/jmx_ib:Kind/jmx_ib:Code/text()',namespaces)
                areaelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{j+1}]//jmx_ib:Area',namespaces)
                for k in range(len(areaelements)):
                    areacode = self._get_text(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{j+1}]//jmx_ib:Area[{k+1}]/jmx_ib:Code/text()',namespaces)
                    #末尾2桁を削除し、00を付加する
                    areacode=f"{areacode[:-2]}00"
                    #print(areacode)
                    #print(codeelements)
                    codeList.append({areacode: codeelements})
            parsed_data[areakeys[i]]=codeList
        return parsed_data
    
    def content(self, xml_tree, namespaces, telop_dict):
        """
        XMLツリーと名前空間を受け取り、地震情報の内容を解析して辞書として返します。
        telop_dict: テロップ情報の辞書, logoとtextのペアをリストとして持つ。
        """
        logo_list = []
        text_list = []
        sound_list = []
        publishing_office = self._get_text(xml_tree, '//jmx:Control/jmx:PublishingOffice/text()', namespaces)
        title = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        headline = self._get_text(xml_tree, '//jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        notify_level=0
        sound="sounds/Forecast.wav"
        if "最大級の警戒" in headline or "安全の確保" in headline:
            sound="sounds/EEWalert.wav"
            notify_level=5
        elif "厳重に警戒" in headline:
            sound="sounds/Grade5-.wav"
            notify_level=4
        elif "非常に危険" in headline:
            sound="sounds/Grade5-.wav"
            notify_level=4
        elif "警戒" in headline:
            sound="sounds/GeneralWarning.wav"
            notify_level=3
        elif "注意" in headline:
            sound="sounds/GeneralInfo.wav"
            notify_level=2
        if "解除" in headline:
            sound="sounds/Forecast.wav"
            notify_level=0

        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {title}</b>",""])
        sound_list.append(sound)
        
        self.format_and_append_text(headline,logo_list,text_list,sound_list)
                
        codeCombinationList=[]
        areaList=[]
        #気象警報のコードと地域のペアを取得する
        type="土砂災害警戒情報"
        #type="気象警報・注意報（市町村等）"
        itemelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item',namespaces)
        lenitem=len(itemelements)
        for i in range(lenitem):
            codeelements = self._get_text(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{i+1}]/jmx_ib:Kind/jmx_ib:Code/text()',namespaces)
            areaelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{i+1}]//jmx_ib:Area/jmx_ib:Name/text()',namespaces)
            if not codeelements in codeCombinationList and len(codeelements)!=0:
                codeCombinationList.append(codeelements)
                areaList.append(areaelements) #最初はリストの状態で追加する
            else: #すでに登録した場合
                #該当するものを探す
                for j, codelist in enumerate(codeCombinationList):
                    if codeelements == codelist:
                        areaList[j].append(areaelements[0]) #テキストで追加する
                pass
        #print(f"{codeCombinationList}:{areaList}")
        
        #logo, textに整形する
        logos=[]
        texts=[]
        for i in range(len(codeCombinationList)):
            logo=""
            areatext=""
            for code in codeCombinationList[i]:
                if code=="3":
                    logo+=f"materials/doshasaigai.svg,"
                elif code=="1":
                    logo+=f"materials/code00.svg,"
            logos.append(logo[:-1]) #最後の,を除いておく
            for area in areaList[i]:
                areatext+=f"{area} "
            texts.append(areatext[:-1]) #最後の を除いておく
        #print(f"{logos} : {texts}")
        if len(logos)%2==1:
            logos.append("")
            texts.append("")
        #2行組に分けていく
        for i in range(len(logos)):
            if i%2 == 1:
                logo_list.append(logos[i-1:i+1])
                text_list.append(texts[i-1:i+1])
                sound_list.append("")
        
        telop_dict = {
            'sound_list': sound_list,
            'logo_list': logo_list,
            'text_list': text_list
        }
        return telop_dict, {publishing_office: notify_level}