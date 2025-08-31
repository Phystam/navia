# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser
import datetime

class VFVO56(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VFVO56" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code, test=False):
        """
        噴火速報 (VFVO56) のXMLを解析します。
        """
        print(f"噴火速報 ({self.data_type}) を解析中...")
        parsed_data = {}
        parsed_data['category']="volcanology"
        parsed_data["data_type"]=self.data_type
        # Control/Title
        parsed_data['control_title'] = self._get_text(xml_tree, '//jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '//jmx:Control/jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '//jmx_ib:Head/jmx_ib:Title/text()', namespaces)
        # Head/Headline/Text
        parsed_data['headline_text'] = self._get_text(xml_tree, '//jmx_ib:Head/jmx_ib:Headline/jmx_ib:Text/text()', namespaces)

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
        title = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        sound = "sounds/GeneralInfo.wav"  # デフォルトのサウンドファイル
        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {title}</b>",""])
        sound_list.append(sound)
        # 火山名
        volcname = self._get_text(xml_tree, '//jmx_ib:Item/jmx_ib:Areas/jmx_ib:Area/jmx_ib:Name/text()', namespaces)
        # 火山の状態
        kind = self._get_text(xml_tree, '//jmx_ib:Item/jmx_ib:Kind/jmx_ib:Name/text()', namespaces)
        
        dtime = self._get_datetime(xml_tree,'//jmx_ib:TargetDateTime/text()',namespaces)
        headlinetext=f"{dtime.day}日{dtime.hour}時{dtime.minute}分ごろ、{volcname}で"
        if "もよう" in kind:
            headlinetext+= f"{kind}です。"
        else:
            headlinetext+= f"{kind}が観測されました。"
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
        text_list.append([headlinetext,f"火口上噴煙高度 {height} 噴煙の流向 {direction}"])
        sound_list.append("")
        
        notify_level=3
        telop_dict = {
            'sound_list': sound_list,
            'logo_list': logo_list,
            'text_list': text_list
        }
        return telop_dict, {publishing_office: notify_level}
