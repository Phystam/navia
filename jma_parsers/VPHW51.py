# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser

class VPHW51(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VPHW51" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code):
        """
        竜巻注意情報 (VPHW51) のXMLを解析します。
        """
        print(f"竜巻注意情報 ({self.data_type}) を解析中...")
        parsed_data = {}
        # Control/Title
        parsed_data["category"]="meteorology"
        parsed_data["data_type"]=self.data_type
        parsed_data['control_title'] = self._get_text(xml_tree, '//jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '//jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        parsed_data['report_datetime'] = self._get_datetime(xml_tree,'//jmx_ib:ReportDateTime/text()', namespaces)
        parsed_data['valid_datetime'] = self._get_datetime(xml_tree,'//jmx_ib:ValidDateTime/text()', namespaces)
        headline = self._get_text(xml_tree, '//jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
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
        types=["竜巻注意情報（発表細分）",
               "竜巻注意情報（一次細分区域等）",
               "竜巻注意情報（市町村等をまとめた地域等）",
               "竜巻注意情報（市町村等）"]
        areakeys=["pref","class10","class15","class20"]
        for i,type in enumerate(types):
            codeList=[]
            itemelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item',namespaces)
            lenitem=len(itemelements)
            for j in range(lenitem):
                # codeelements は["1"]になる
                codeelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{j+1}]/jmx_ib:Kind/jmx_ib:Code/text()',namespaces)
                
                areacode = self._get_text(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{j+1}]//jmx_ib:Area/jmx_ib:Code/text()',namespaces)
                #print(areacode)
                #print(codeelements)
                codeList.append({areacode: codeelements})
            parsed_data[areakeys[i]]=codeList
        return parsed_data

        return parsed_data
    
    def content(self, xml_tree, namespaces, telop_dict):
        """
        XMLツリーと名前空間を受け取り、地震情報の内容を解析して辞書として返します。
        telop_dict: テロップ情報の辞書, logoとtextのペアをリストとして持つ。
        """
        logo_list = []
        text_list = []
        sound_list = []
        publishing_office = self._get_text(xml_tree, '//jmx:PublishingOffice/text()', namespaces)
        title = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)

        
        headline = self._get_text(xml_tree, '//jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        notify_level=1
        if "最大級の警戒" in headline or "安全の確保" in headline:
            sound="sounds/EEWalert.wav"
            notify_level=5
        elif "厳重に警戒" in headline:
            sound="sounds/Grade5-.wav"
            notify_level=4
        elif "警戒" in headline:
            sound="sounds/GeneralWarning.wav"
            notify_level=3
        elif "注意" in headline:
            sound="sounds/GeneralWarning.wav"
            notify_level=3
        if "解除" in headline:
            sound="sounds/Forecast.wav"
            notify_level=0

        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {title}</b>",""])
        sound_list.append(sound)
        # headlineを句点で分割
        tlist=headline.split("。")
        # 最後。で終わるので、最後尾の要素を削除する
        tlist=tlist[:-1]
        # 要素数が奇数の場合、空文字を追加して偶数にする
        if len(tlist) %2 != 0:
            tlist.append("")
        for i in range(len(tlist)):
            # 消された句点を復元
            if tlist[i] !="":
                tlist[i] = f"{tlist[i]}。"
            # 奇数番目のとき、2行分のリストを追加
            if i % 2 == 1:
                sound_list.append("")
                logo_list.append(["", ""])
                text_list.append(tlist[i-1:i+1])
                
        
        #気象警報のコードと地域のペアを取得する
        types=["竜巻注意情報（目撃情報あり）","竜巻注意情報（市町村等をまとめた地域等）"]
        for type in types:
            #type="気象警報・注意報（市町村等）"
            codeCombinationList=[]
            areaList=[]
            itemelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item',namespaces)
            lenitem=len(itemelements)
            for i in range(lenitem):
                codeelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{i+1}]/jmx_ib:Kind/jmx_ib:Code/text()',namespaces)
                #(codeelements)
                areaelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{i+1}]//jmx_ib:Area/jmx_ib:Name/text()',namespaces)
                if not codeelements in codeCombinationList and len(codeelements)!=0:
                    codeCombinationList.append(codeelements)
                    areaList.append(areaelements) #最初はリストの状態で追加する
                else: #すでに登録した場合
                    #該当するものを探す
                    for j, codelist in enumerate(codeCombinationList):
                        if codeelements == codelist:
                            areaList[j].append(areaelements[0]) #テキストで追加する
            #print(f"{codeCombinationList}:{areaList}")
            #logo, textに整形する
            if len(codeCombinationList)==0:
                continue
            logos=[]
            texts=[]
            for i in range(len(codeCombinationList)):
                logo=""
                areatext=""
                for code in codeCombinationList[i]:
                    logo+=f"materials/tatsumaki.svg," if type==types[1] else f"materials/tatsumaki_observed.svg,"
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