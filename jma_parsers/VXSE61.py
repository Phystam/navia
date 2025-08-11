# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser

class VXSE61(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VXSE61" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code):
        """
        地震情報 (VXSE61) のXMLを解析します。
        """
        print(f"地震情報 ({self.data_type}) を解析中...")
        parsed_data = {}
        parsed_data['category']="seismology"
        parsed_data["data_type"]=self.data_type
        # Control/Title
        parsed_data['control_title'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Title/text()', namespaces)
        # Head/Headline/Text
        parsed_data['headline_text'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        parsed_data['forecast_comment'] = self._get_text(xml_tree, '/jmx:Report/jmx_seis:Body/jmx_seis:Comments/jmx_seis:ForecastComment/jmx_seis:Text/text()', namespaces)

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
                       "震度４": "4",
                       "震度３": "3",
                       "震度２": "2",
                       "震度１": "1"
                       }
        publishing_office = self._get_text(xml_tree, '//jmx:PublishingOffice/text()', namespaces)
        title = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        # 最大震度に応じたサウンドを設定
        sound = f"./sounds/GeneralInfo.wav"  # デフォルトのサウンドファイル
        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {title}</b>",""])
        sound_list.append(sound)
        headline = self._get_text(xml_tree, '//jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        hypocenter_name = self._get_text(xml_tree, '//jmx_seis:Hypocenter/jmx_seis:Area/jmx_seis:Name/text()', namespaces)
        magnitude_value = self._get_text(xml_tree, '//jmx_eb:Magnitude/text()', namespaces)
        
        coordinates = self._get_coordinates(xml_tree, '//jmx_seis:Hypocenter/jmx_seis:Area/jmx_eb:Coordinate/text()', namespaces)
        comment = self._get_text(xml_tree, '//jmx_seis:ForecastComment/jmx_seis:Text/text()', namespaces)
        message=f"震源は{hypocenter_name} 深さ{-int(coordinates[0]['altitude']/1000)}km マグニチュード{magnitude_value}"
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
        notify_level=3
        telop_dict = {
            'sound_list': sound_list,
            'logo_list': logo_list,
            'text_list': text_list
        }
        return telop_dict, {publishing_office: notify_level}