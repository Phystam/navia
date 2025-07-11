# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser

class VFVO52(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VFVO52" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code):
        """
        噴火に関する火山観測報 (VFVO52) のXMLを解析します。
        """
        print(f"噴火に関する火山観測報 ({self.data_type}) を解析中...")
        parsed_data = {}
        # Control/Title
        parsed_data['control_title'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Title/text()', namespaces)
        # Head/Headline/Text
        parsed_data['headline_text'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Headline/jmx_ib:Text/text()', namespaces)

        # 必要に応じて、さらに詳細な震度情報などを抽出することも可能

        self.parsedData.emit(self.data_type, parsed_data)
        return parsed_data
    
    def content(self, xml_tree, namespaces, telop_dict):
        """
        XMLツリーと名前空間を受け取り、地震情報の内容を解析して辞書として返します。
        telop_dict: テロップ情報の辞書, logoとtextのペアをリストとして持つ。
        """
        logo_list = []
        text_list = []
        publishing_office = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:PublishingOffice/text()', namespaces)
        title = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Title/text()', namespaces)
        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {title}</b>",""])
        
        # 火山名
        volcname = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Headline/jmx_ib:Information/jmx_ib:Item/jmx_ib:Areas/jmx_ib:Area/jmx_ib:Name/text()', namespaces)
        # 火山の状態
        kind = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Headline/jmx_ib:Information/jmx_ib:Item/jmx_ib:Kind/jmx_ib:Name/text()', namespaces)
        # 火口上噴煙高度
        height = self._get_text(xml_tree, '//jmx_eb:PlumeHeightAboveCrater/text()', namespaces)
        if height == "N/A":
            height = "不明"
        else:
            height = f"{height}m"
        # 噴煙の流向
        direction = self._get_text(xml_tree, '//jmx_eb:PlumeDirection/text()', namespaces)
        if direction == "流向不明":
            direction = "不明"
        logo_list.append(["", ""])
        text_list.append([kind,f"火口上噴煙高度 {height} 噴煙の流向 {direction}"])
        sound = "sounds/GeneralInfo.wav"  # デフォルトのサウンドファイル
        telop_dict = {
            'sound': sound,
            'logo_list': logo_list,
            'text_list': text_list
        }
        return telop_dict
