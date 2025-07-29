# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser

class VFVO53(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VFVO53" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code):
        """
        降灰予報 (定時) (VFVO53) のXMLを解析します。
        """
        print(f"VFVO53 ({self.data_type}) を解析中...")
        parsed_data = {}
        # Control/Title
        parsed_data['control_title'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Title/text()', namespaces)
        # Head/Headline/Text
        
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
        sound_list = []
        publishing_office = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:PublishingOffice/text()', namespaces)
        title = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:Title/text()', namespaces)
        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {title}</b>",""])
        sound_list.append("sounds/GeneralInfo.wav")  # デフォルトのサウンドファイル
        headline = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        notify_level=1
        telop_dict = {
            'sound_list': sound_list,
            'logo_list': logo_list,
            'text_list': text_list
        }
        return telop_dict, {publishing_office: notify_level}