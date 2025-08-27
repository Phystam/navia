# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser
from datetime import datetime, timezone,timedelta
class VZSA50(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VZSA50" # このパーサーが扱うデータタイプ
        

    def parse(self, xml_tree, namespaces, data_type_code, test=False):
        """
        天気実況図 (VZSA50) のXMLを解析します。
        """
        print(f"天気実況図 ({self.data_type}) を解析中...----------------------------")
        parsed_data = {}
        # Control/Title
        parsed_data["category"]="meteorology"
        parsed_data["data_type"]=self.data_type
        parsed_data['control_title'] = self._get_text(xml_tree, '//jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '//jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        parsed_data['report_datetime'] = self._get_datetime(xml_tree,'//jmx_ib:ReportDateTime/text()', namespaces) if not test else datetime.now(tz=self.jst)
        parsed_data['time']= self._get_datetime(xml_tree,'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:DateTime/text()', namespaces)
        parsed_data['geojson']={}
        parsed_data['geojson']['type']="FeatureCollection"
        parsed_data['geojson']['features']=[]
        
        len_item = len(self._get_elements(xml_tree,'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item', namespaces))
        # 高気圧
        for i in range(len_item):
            feature={}
            feature['type']="Feature"
            feature['geometry']={}
            item_type=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]/jmx_mete:Kind[1]//jmx_mete:Type/text()', namespaces)
            #print(item_type)
            if item_type=="等圧線":
                feature['geometry']['type']="LineString"
                feature['geometry']['coordinates']=self._get_coordinates_list(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]//jmx_eb:Line/text()', namespaces)
                feature['properties']={}
                feature['properties']['type']=item_type
                feature['properties']['pressure']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]//jmx_eb:Pressure/text()', namespaces)
            if item_type=="高気圧" or item_type=="低気圧" or item_type=="低圧部" or item_type=="熱帯低気圧" or item_type=="台風":
                feature['geometry']['type']="Point"
                feature['geometry']['coordinates']=self._get_coordinates_list(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]//jmx_eb:Coordinate/text()', namespaces)[0]
                feature['properties']={}
                feature['properties']['type']=item_type
                feature['properties']['pressure']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]//jmx_eb:Pressure/text()', namespaces)
                speed=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]//jmx_eb:Speed/text()', namespaces)
                speed_condition=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]//jmx_eb:Speed/@description', namespaces)
                feature['properties']['speed']=speed if speed!="" else speed_condition
                feature['properties']['direction']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]//jmx_eb:Direction/text()', namespaces)
                if item_type=="台風":
                    feature['properties']['max_windspeed']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]/jmx_mete:Kind[2]//jmx_eb:WindSpeed/text()', namespaces)
                    typhoontype=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]/jmx_mete:Kind[3]//jmx_eb:Type/text()', namespaces)
                    if typhoontype!="":
                        feature['properties']['name']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]/jmx_mete:Kind[3]//jmx_eb:Name/text()', namespaces)
                        feature['properties']['namekana']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]/jmx_mete:Kind[3]//jmx_eb:NameKana/text()', namespaces)
                        feature['properties']['number']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]/jmx_mete:Kind[3]//jmx_eb:Number/text()', namespaces)
            if item_type=="停滞前線" or item_type=="閉塞前線" or item_type=="寒冷前線" or item_type=="温暖前線":
                feature['geometry']['type']="LineString"
                feature['geometry']['coordinates']=self._get_coordinates_list(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]//jmx_eb:Line/text()', namespaces)
                feature['properties']={}
                feature['properties']['type']=item_type
                feature['properties']['condition']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfos[@type="天気図情報"]/jmx_mete:MeteorologicalInfo/jmx_mete:Item[{i+1}]//jmx_eb:Line/@condition', namespaces)

            parsed_data['geojson']['features'].append(feature)
        
        return parsed_data
    
    def content(self, xml_tree, namespaces, telop_dict):
        """
        XMLツリーと名前空間を受け取り、地震情報の内容を解析して辞書として返します。
        telop_dict: テロップ情報の辞書, logoとtextのペアをリストとして持つ。
        """
        # do nothing
        return None,None