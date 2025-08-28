# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser
from datetime import datetime, timezone,timedelta
class VPTW(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VPTW" # このパーサーが扱うデータタイプ
        

    def parse(self, xml_tree, namespaces, data_type_code, test=False):
        """
        台風解析・予報情報（５日予報）（Ｈ３０） (VPTWii) のXMLを解析します。
        """
        print(f"台風解析・予報情報（５日予報）（Ｈ３０） ({data_type_code}) を解析中...----------------------------")
        parsed_data = {}
        # Control/Title
        parsed_data["category"]="meteorology"
        parsed_data["data_type"]=self.data_type
        parsed_data['control_title'] = self._get_text(xml_tree, '//jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '//jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        parsed_data['report_datetime'] = self._get_datetime(xml_tree,'//jmx_ib:ReportDateTime/text()', namespaces) if not test else datetime.now(tz=self.jst)
        parsed_data['time']= self._get_datetime(xml_tree,'//jmx_mete:MeteorologicalInfo[1]/jmx_mete:DateTime/text()', namespaces)
        parsed_data['eventID']=self._get_text(xml_tree,'//jmx_ib:EventID/text()',namespaces)
        parsed_data['geojson']={}
        parsed_data['geojson']['type']="FeatureCollection"
        parsed_data['geojson']['features']=[]
        len_info = len(self._get_elements(xml_tree,f'//jmx_mete:MeteorologicalInfo', namespaces))
        # 高気圧
        for i in range(len_info):
            feature={}
            feature['type']="Feature"
            feature['geometry']={}
            feature['properties']={}
            feature['geometry']['type']="Point"
            datetime_type=self._get_attribute(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:DateTime/@type', namespaces)
            if datetime_type =="実況" or datetime_type=="推定　１時間後":
                feature['geometry']['coordinates']=self._get_coordinates_list(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_eb:Coordinate[@type="中心位置（度）"]/text()', namespaces)[0]
            else:
                feature['geometry']['coordinates']=self._get_coordinates_list(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:ProbabilityCircle/jmx_eb:BasePoint[@type="中心位置（度）"]/text()', namespaces)[0]
                feature['properties']['probability_radius']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:ProbabilityCircle//jmx_eb:Radius[@unit="km"]/text()', namespaces)
            
            feature['properties']['datetime_type']=self._get_attribute(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:DateTime/@type', namespaces)
            feature['properties']['datetime']=self._get_datetime(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:DateTime/text()', namespaces)
            feature['properties']['area_class']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_eb:AreaClass/text()', namespaces)
            feature['properties']['intensity_class']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_eb:IntensityClass/text()', namespaces)
            feature['properties']['name']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:NameKana/text()', namespaces)
            feature['properties']['number']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:Number/text()', namespaces)
            feature['properties']['remark']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:Remark/text()', namespaces)
            feature['properties']['location']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:Location/text()', namespaces)
            feature['properties']['direction']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_eb:Direction/text()', namespaces)
            speed=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_eb:Speed[@unit="km/h"]/text()', namespaces)
            feature['properties']['speed']=self._get_attribute(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_eb:Speed/@condition', namespaces) if speed=="" else speed
            feature['properties']['pressure']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_eb:Pressure/text()', namespaces)
            #print(item_type)

            print(feature)
            parsed_data['geojson']['features'].append(feature)
        
        return parsed_data
    
    def content(self, xml_tree, namespaces, telop_dict):
        """
        XMLツリーと名前空間を受け取り、地震情報の内容を解析して辞書として返します。
        telop_dict: テロップ情報の辞書, logoとtextのペアをリストとして持つ。
        """
        # do nothing
        return None,None