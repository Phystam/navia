from .jma_base_parser import BaseJMAParser

class VGSK50(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VGSK50" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code):
        """
        生物気象観測 (VGSK50) のXMLを解析します。
        """
        print(f"気象観測 ({self.data_type}) を解析中...")
        parsed_data = {}
        parsed_data['category']="volcanology"
        parsed_data["data_type"]=self.data_type
        # Control/Title
        parsed_data['control_title'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Title/text()', namespaces)
        # Head/Headline/Text
        parsed_data['headline_text'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Headline/jmx_ib:Text/text()', namespaces)

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
        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {title}</b>",""])
        sound_list.append("sounds/Forecast.wav")  # デフォルトのサウンドファイル
        
        station=self._get_text(xml_tree, '//jmx_mete:Station/jmx_mete:Name/text()', namespaces)
        kind=self._get_text(xml_tree, '//jmx_mete:Kind/jmx_mete:Name/text()', namespaces)
        days=self._get_text(xml_tree, '//jmx_mete:DeviationFromNormal/text()', namespaces)
        add_text=self._get_text(xml_tree, '//jmx_mete:ObservationAddition/jmx_mete:Text/text()', namespaces)
        headline = f"{station}で{kind}を観測"
        if days != "N/A":
            dev_day= f"平年より{-int(days)}日早い" if days<0 else f"平年より{int(days)}日遅い"
            if int(days)==0:
                dev_day="平年と同じ"
            headline += f" {dev_day}"
        if add_text != "N/A":
            headline += f" {add_text}"
            
        logo_list.append(["", ""])
        text_list.append([headline, ""])
        sound_list.append("")
        notify_level=5
        telop_dict = {
            'logo_list': logo_list,
            'text_list': text_list,
            'sound_list': sound_list
        }
        return telop_dict, {publishing_office: notify_level}
