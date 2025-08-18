# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser

class VFVO50(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VFVO50" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code, test=False):
        """
        噴火警報 (VFVO50) のXMLを解析します。
        """
        #print(f"VFVO50 ({self.data_type}) を解析中...")
        parsed_data = {}
        parsed_data['category']="volcanology"
        parsed_data["data_type"]=self.data_type
        # Control/Title
        parsed_data['control_title'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Title/text()', namespaces)
        # Head/Headline/Text
        return parsed_data
    
    def content(self, xml_tree, namespaces, telop_dict):
        """
        XMLツリーと名前空間を受け取り、地震情報の内容を解析して辞書として返します。
        telop_dict: テロップ情報の辞書, logoとtextのペアをリストとして持つ。
        """
        level_icon_dict={
            "11": "materials/volc_level1.svg",
            "12": "materials/volc_level2.svg",
            "13": "materials/volc_level3.svg",
            "14": "materials/volc_level4.svg",
            "15": "materials/volc_level5.svg"
        }
        logo_list = []
        text_list = []
        sound_list = []
        # sound
        sound=""
        headline = self._get_text(xml_tree, '//jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        notify_level=1
        if "警戒レベル５" in headline:
            sound="sounds/Grade7.wav"
            notify_level=5
        elif "警戒レベル４" in headline:
            sound="sounds/Grade5+.wav"
            notify_level=4
        elif "警戒レベル３" in headline:
            sound="sounds/Grade3.wav"
            notify_level=3
        elif "警戒レベル２" in headline:
            sound="sounds/GeneralInfo.wav"
            notify_level=2
        else:
            sound="sounds/GeneralInfo.wav"
            notify_level=1
        publishing_office = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:PublishingOffice/text()', namespaces)
        title = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {title}</b>",""])
        sound_list.append(sound)  # デフォルトのサウンドファイル
        
        self.format_and_append_text(headline, logo_list,text_list,sound_list)
        type_volc="噴火警報・予報（対象火山）"
        type_alert="噴火警報・予報（対象市町村等）"
        type_area="気象・地震・火山情報／市町村等"
        
        levelcode = self._get_text(xml_tree, f'//jmx_ib:Headline/jmx_ib:Information[@type="{type_volc}"]/jmx_ib:Item/jmx_ib:Kind/jmx_ib:Code/text()', namespaces)
        volcname = self._get_text(xml_tree, f'//jmx_ib:Headline/jmx_ib:Information[@type="{type_volc}"]/jmx_ib:Item/jmx_ib:Areas/jmx_ib:Area/jmx_ib:Name/text()', namespaces)
        arealist=self._get_elements(xml_tree, f'//jmx_ib:Headline/jmx_ib:Information[@type="{type_alert}"]/jmx_ib:Item/jmx_ib:Areas[@codeType="{type_area}"]/jmx_ib:Area/jmx_ib:Name/text()', namespaces)
        areatext=""
        for area in arealist:
            areatext += f"{area} "
        
        logo_list.append([level_icon_dict[levelcode],""])
        text_list.append([volcname,""])
        sound_list.append("")
        
        logo_list.append([level_icon_dict[levelcode],""])
        text_list.append([areatext,""])
        sound_list.append("")
        telop_dict = {
            'sound_list': sound_list,
            'logo_list': logo_list,
            'text_list': text_list
        }
        return telop_dict, {publishing_office: notify_level}