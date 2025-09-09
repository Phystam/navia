# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser

class VXSE53(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VXSE53" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code, test=False):
        """
        地震情報 (VXSE53) のXMLを解析します。
        """
        shindo_codelist = {"震度７": "7",
                       "震度６強": "6+",
                       "震度６弱": "6-",
                       "震度５強": "5+",
                       "震度５弱": "5-",
                       "震度５弱以上未入電": "5-+",
                       "震度４": "4",
                       "震度３": "3",
                       "震度２": "2",
                       "震度１": "1"
                       }
        parsed_data = {}
        parsed_data['category']="seismology"
        parsed_data["data_type"]=data_type_code
        # Control/Title
        parsed_data['control_title'] = self._get_text(xml_tree, '//jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '//jmx:Control/jmx:PublishingOffice/text()', namespaces)
        parsed_data['event_id']=self._get_text(xml_tree, '//jmx_ib:EventID/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '//jmx_ib:Head/jmx_ib:Title/text()', namespaces)
        # Head/Headline/Text
        parsed_data['headline_text'] = self._get_text(xml_tree, '//jmx_ib:Head/jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        # Body/Earthquake/Hypocenter/Area/Name (震央地名)
        parsed_data['forecast_comment'] = self._get_text(xml_tree, '//jmx_seis:ForecastComment/jmx_seis:Text/text()', namespaces)

        parsed_data['hypocenter_name'] = self._get_text(xml_tree, '//jmx_seis:Earthquake/jmx_seis:Hypocenter/jmx_seis:Area/jmx_seis:Name/text()', namespaces)
        parsed_data['magnitude'] = self._get_text(xml_tree, '//jmx_seis:Earthquake/jmx_eb:Magnitude/text()', namespaces)
        
        parsed_data['coordinates'] = self._get_coordinates(xml_tree, '//jmx_seis:Hypocenter/jmx_seis:Area/jmx_eb:Coordinate/text()', namespaces)
        return parsed_data
    
    def content(self, xml_tree, namespaces, telop_dict):
        """
        XMLツリーと名前空間を受け取り、地震情報の内容を解析して辞書として返します。
        telop_dict: テロップ情報の辞書, logoとtextのペアをリストとして持つ。
        """
        sound_list = []
        logo_list = []
        text_list = []
        shindo_codelist = {"震度７": "7",
                       "震度６強": "6+",
                       "震度６弱": "6-",
                       "震度５強": "5+",
                       "震度５弱": "5-",
                       "震度５弱以上未入電": "5-+",
                       "震度４": "4",
                       "震度３": "3",
                       "震度２": "2",
                       "震度１": "1"
                       }
        publishing_office = self._get_text(xml_tree, '//jmx:PublishingOffice/text()', namespaces)
        title = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        max_intensity = self._get_text(xml_tree, '//jmx_seis:MaxInt/text()', namespaces)
        if max_intensity=="":
            max_intensity="不明"
        # 最大震度に応じたサウンドを設定
        sound = f"./sounds/Grade{max_intensity}.wav"  # デフォルトのサウンドファイル
        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {title}</b>",""])
        sound_list.append(sound)
        headline = self._get_text(xml_tree, '//jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        hypocenter_name = self._get_text(xml_tree, '//jmx_seis:Earthquake/jmx_seis:Hypocenter/jmx_seis:Area/jmx_seis:Name/text()', namespaces)
        magnitude_value = self._get_text(xml_tree, '//jmx_seis:Earthquake/jmx_eb:Magnitude/text()', namespaces)
        
        coordinates = self._get_coordinates(xml_tree, '/jmx:Report/jmx_seis:Body/jmx_seis:Earthquake/jmx_seis:Hypocenter/jmx_seis:Area/jmx_eb:Coordinate/text()', namespaces)
        comment = self._get_text(xml_tree, '//jmx_seis:ForecastComment/jmx_seis:Text/text()', namespaces)
        print(coordinates)
        if coordinates[0]['altitude'] is not None:
            message=f"震源は{hypocenter_name} 深さ{-int(coordinates[0]['altitude']/1000)}km マグニチュード{magnitude_value} 最大震度 {max_intensity}"
        else:
            message=f"震源は{hypocenter_name} マグニチュード{magnitude_value} 最大震度 {max_intensity}"
        logo_list.append(["", ""])
        text_list.append([headline, message])
        sound_list.append("")
        
        # headlineを句点で分割
        comment=comment.replace("\n","")
        tlist=comment.split("。")
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
        type="震源・震度に関する情報（細分区域）"
        #type="気象警報・注意報（市町村等）"
        shindoList=[]
        areaList=[]
        itemelements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item',namespaces)
        lenitem=len(itemelements)
        for i in range(lenitem):
            shindo = shindo_codelist[ self._get_text(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{i+1}]/jmx_ib:Kind/jmx_ib:Name/text()',namespaces) ]
            areaselements = self._get_elements(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{i+1}]/jmx_ib:Areas/jmx_ib:Area',namespaces)
            shindoList.append(shindo)
            areas=[]
            for j in range(len(areaselements)):
                area = self._get_text(xml_tree, f'//jmx_ib:Information[@type="{type}"]/jmx_ib:Item[{i+1}]/jmx_ib:Areas/jmx_ib:Area[{j+1}]/jmx_ib:Name/text()',namespaces)
                areas.append(area)
            areaList.append(areas)

        #print(f"{shindoList}:{areaList}")
        
        # areasが6箇所以上より長いとき、分割する。
        ndiv=5
        shindoList_div=[]
        areaList_div=[]
        
        row_counter=0
        for i in range(len(shindoList)):
            counter=0    
            for j in range(0, len(areaList[i]), ndiv):
                if row_counter%2==0 or counter==0:
                    shindoList_div.append(shindoList[i])
                else:
                    shindoList_div.append("")
                areaList_div.append(areaList[i][j:j+ndiv])
                counter+=1
                row_counter+=1
            if counter>1 and row_counter%2==1:
                areaList_div.append([])
                shindoList_div.append("")
                row_counter+=1
                
        #logo, textに整形する
        logos=[]
        texts=[]
        for i in range(len(shindoList_div)):
            logo=""
            areatext=""
            if(shindoList_div[i]!=""):
                logos.append(f"materials/grade{shindoList_div[i]}.svg")
            else:
                logos.append("")
            for area in areaList_div[i]:
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
        notify_level=3
        telop_dict = {
            'sound_list': sound_list,
            'logo_list': logo_list,
            'text_list': text_list
        }
        return telop_dict, {publishing_office: notify_level}
