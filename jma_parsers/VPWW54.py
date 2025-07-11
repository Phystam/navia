# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser

class VPWW54(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VPWW54" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code):
        """
        気象警報 (VPWW54) のXMLを解析します。
        """
        print(f"気象警報 ({self.data_type}) を解析中...")
        parsed_data = {}
        # Control/Title
        parsed_data['control_title'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Title/text()', namespaces)

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
        
        headline = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        if "最大級の警戒" in headline or "安全の確保" in headline:
            sound="sound/EEWalert.wav"
            level=5
        elif "厳重に警戒" in headline:
            sound="sound/Grade5-.wav"
            level=4
        elif "警戒" in headline:
            sound="sound/GeneralWarning.wav"
            level=3
        elif "注意" in headline:
            sound="sound/GeneralInfo.wav"
            level=2
        if "解除" in headline:
            sound="sound/Forecast.wav"
            level=0

        # headlineを句点で分割
        tlist=headline.split("。")
        # 要素数が奇数の場合、空文字を追加して偶数にする
        if len(tlist) %2 != 0:
            tlist.append("")
        for i in range(len(tlist)):
            # 消された句点を復元
            if tlist[i] !="":
                tlist[i] = f"{tlist[i]}。"
            # 偶数番目のとき、2行分のリストを追加
            if i % 2 == 0:
                logo_list.append(["", ""])
                text_list.append(tlist[i:i+2])

        telop_dict = {
            'sound': sound,
            'logo_list': logo_list,
            'text_list': text_list
        }
        return telop_dict