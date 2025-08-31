# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser

class VTSE52(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VTSE52" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code, test=False):
        """
        気象警報 (VPWW54) のXMLを解析します。
        """
        print(f"気象警報 ({self.data_type}) を解析中...")
        parsed_data = {}
        parsed_data['category']="seismology"
        parsed_data["data_type"]=self.data_type
        # Control/Title
        parsed_data['control_title'] = self._get_text(xml_tree, '//jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '//jmx:Control/jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '//jmx_ib:Head/jmx_ib:Title/text()', namespaces)

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
        title = self._get_text(xml_tree, '//jmx_ib:Head/jmx_ib:Title/text()', namespaces)

        
        headline = self._get_text(xml_tree, '//jmx_ib:Head/jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        notify_level=5
        sound="sounds/Grade7.wav"

        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {title}</b>",""])
        sound_list.append(sound)
        
        self.format_and_append_text(headline,logo_list,text_list,sound_list)
                
        codeCombinationList=[]
        areaList=[]
        #気象警報のコードと地域のペアを取得する
        type="気象警報・注意報（市町村等をまとめた地域等）"
        #type="気象警報・注意報（市町村等）"
        itemelements = self._get_elements(xml_tree, f'//jmx_seis:Observation/jmx_seis:Item',namespaces)
        lenitem=len(itemelements)
        for i in range(lenitem):
            logo="materials/tsunami_observed.svg"
            areatext = self._get_text(xml_tree, f'//jmx_seis:Observation/jmx_seis:Item[{i+1}]/jmx_seis:Area/jmx_seis:Name/text()',namespaces)
            stationtext = self._get_text(xml_tree, f'//jmx_seis:Observation/jmx_seis:Item[{i+1}]/jmx_seis:Station/jmx_seis:Name/text()',namespaces)
            datetimetext = self._get_datetime(xml_tree, f'//jmx_seis:Observation/jmx_seis:Item[{i+1}]/jmx_seis:Station/jmx_seis:MaxHeight/jmx_seis:DateTime/text()',namespaces)
            heighttext = self._get_text(xml_tree, f'//jmx_seis:Observation/jmx_seis:Item[{i+1}]/jmx_seis:Station/jmx_seis:MaxHeight/jmx_eb:TsunamiHeight/text()',namespaces)
            conditiontext = self._get_text(xml_tree, f'//jmx_seis:Observation/jmx_seis:Item[{i+1}]/jmx_seis:Station/jmx_seis:MaxHeight/jmx_seis:Condition/text()',namespaces)
            logo_list.append([logo,""])
            sound_list.append("")
            if heighttext !="":
                text_list.append([f"{areatext} {stationtext}",f"{datetimetext.hour}時{datetimetext.minute}分ごろ 最大波  {heighttext}m"])
            else:
                text_list.append([f"{areatext} {stationtext}",f"{conditiontext}"])   
        #print(f"{codeCombinationList}:{areaList}")
        telop_dict = {
            'sound_list': sound_list,
            'logo_list': logo_list,
            'text_list': text_list
        }
        return telop_dict, {publishing_office: notify_level}