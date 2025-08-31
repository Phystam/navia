# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser
from datetime import datetime, timezone,timedelta
class VPTW(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VPTW" # このパーサーが扱うデータタイプ
        self.degree_dict={
            "北":0,
            "北東":45,
            "東":90,
            "南東":135,
            "南":180,
            "南西":225,
            "西": 270,
            "北西":315
        }
        

    def parse(self, xml_tree, namespaces, data_type_code, test=False):
        """
        台風解析・予報情報（５日予報）（Ｈ３０） (VPTWii) のXMLを解析します。
        """
        print(f"台風解析・予報情報（５日予報）（Ｈ３０） ({data_type_code}) を解析中...----------------------------")
        parsed_data = {}
        # Control/Title
        parsed_data["category"]="meteorology"
        parsed_data["data_type"]=data_type_code
        parsed_data['control_title'] = self._get_text(xml_tree, '//jmx:Control/jmx:Title/text()', namespaces)
        parsed_data['publishing_office'] = self._get_text(xml_tree, '//jmx:Control/jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        parsed_data['report_datetime'] = self._get_datetime(xml_tree,'//jmx_ib:ReportDateTime/text()', namespaces) if not test else datetime.now(tz=self.jst)
        parsed_data['time']= self._get_datetime(xml_tree,'//jmx_mete:MeteorologicalInfo[1]/jmx_mete:DateTime/text()', namespaces)
        parsed_data['eventID']=self._get_text(xml_tree,'//jmx_ib:EventID/text()',namespaces)
        parsed_data['geojson']={}
        parsed_data['geojson']['type']="FeatureCollection"
        parsed_data['geojson']['features']=[]
        len_info = len(self._get_elements(xml_tree,f'//jmx_mete:MeteorologicalInfo', namespaces))
        path_feature={}
        path_feature['type']="Feature"
        path_feature['geometry']={}
        path_feature['properties']={}
        path_feature['geometry']['type']="LineString"
        path_feature['geometry']['coordinates']=[]
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
                path_feature['geometry']['coordinates'].append(feature['geometry']['coordinates'])
            else:
                feature['geometry']['coordinates']=self._get_coordinates_list(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:ProbabilityCircle/jmx_eb:BasePoint[@type="中心位置（度）"]/text()', namespaces)[0]
                feature['properties']['probability_radius']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:ProbabilityCircle//jmx_eb:Radius[@unit="km"]/text()', namespaces)
                path_feature['geometry']['coordinates'].append(feature['geometry']['coordinates'])
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
            feature['properties']['maxwindspeed']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WindPart/jmx_eb:WindSpeed[@type="最大風速" and @unit="m/s"]/text()', namespaces)
            feature['properties']['windspeed']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WindPart/jmx_eb:WindSpeed[@type="最大瞬間風速" and @unit="m/s"]/text()', namespaces)
            
            #強風域
            feature['properties'][f'strong_max_windspeed']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="強風域"]/jmx_eb:WindSpeed[@type="最大瞬間風速" and @unit="m/s"]/text()', namespaces)
            feature['properties'][f'strong_max_insta_windspeed']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="強風域"]/jmx_eb:WindSpeed[@type="最大瞬間風速" and @unit="m/s"]/text()', namespaces)
            feature['properties'][f'strong_long_radius']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="強風域"]//jmx_eb:Axis[1]/jmx_eb:Radius[@unit="km"]/text()', namespaces)
            feature['properties'][f'strong_long_direction']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="強風域"]//jmx_eb:Axis[1]/jmx_eb:Direction/text()', namespaces)
            feature['properties'][f'strong_short_radius']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="強風域"]//jmx_eb:Axis[2]/jmx_eb:Radius[@unit="km"]/text()', namespaces)
            feature['properties'][f'strong_short_direction']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="強風域"]//jmx_eb:Axis[2]/jmx_eb:Direction/text()', namespaces)
            if feature['properties'][f'strong_long_direction']=="":
                feature['properties'][f'strong_center']=feature['geometry']['coordinates']
                feature['properties'][f'strong_radius']=feature['properties']['strong_long_radius']
            else:
                degree=self.degree_dict[feature['properties'][f'strong_long_direction']]
                strong_radius=(feature['properties']['strong_long_radius']+feature['properties']['strong_short_radius'])/2
                distance=feature['properties']['strong_long_radius']-feature['properties']['strong_short_radius']
                feature['properties'][f'strong_center']=self.calc_center_point(feature['geometry']['coordinates'][0],feature['geometry']['coordinates'][0],degree,distance)
                feature['properties'][f'strong_radius']=strong_radius
                
            #暴風域
            feature['properties'][f'storm_max_windspeed']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="暴風域"]/jmx_eb:WindSpeed[@type="最大瞬間風速" and @unit="m/s"]/text()', namespaces)
            feature['properties'][f'storm_max_insta_windspeed']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="暴風域"]/jmx_eb:WindSpeed[@type="最大瞬間風速" and @unit="m/s"]/text()', namespaces)
            feature['properties'][f'storm_long_radius']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="暴風域"]//jmx_eb:Axis[1]/jmx_eb:Radius[@unit="km"]/text()', namespaces)
            feature['properties'][f'storm_long_direction']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="暴風域"]//jmx_eb:Axis[1]/jmx_eb:Direction/text()', namespaces)
            feature['properties'][f'storm_short_radius']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="暴風域"]//jmx_eb:Axis[2]/jmx_eb:Radius[@unit="km"]/text()', namespaces)
            feature['properties'][f'storm_short_direction']=self._get_text(xml_tree,f'//jmx_mete:MeteorologicalInfo[{i+1}]//jmx_mete:WarningAreaPart[@type="暴風域"]//jmx_eb:Axis[2]/jmx_eb:Direction/text()', namespaces)
            if feature['properties'][f'storm_long_direction']=="":
                feature['properties'][f'storm_center']=feature['geometry']['coordinates']
                feature['properties'][f'storm_radius']=feature['properties']['storm_long_radius']
            else:
                degree=self.degree_dict[feature['properties'][f'storm_long_direction']]
                storm_radius=(feature['properties']['storm_long_radius']+feature['properties']['storm_short_radius'])/2
                distance=feature['properties']['storm_long_radius']-feature['properties']['storm_short_radius']
                feature['properties'][f'storm_center']=self.calc_center_point(feature['geometry']['coordinates'][0],feature['geometry']['coordinates'][0],degree,distance)
                feature['properties'][f'storm_radius']=storm_radius
                
            
            #print(item_type)
            parsed_data['geojson']['features'].append(feature)
        parsed_data['geojson']['features'].append(path_feature)
        print(parsed_data)
        return parsed_data
    
    def content(self, xml_tree, namespaces, telop_dict):
        """
        XMLツリーと名前空間を受け取り、地震情報の内容を解析して辞書として返します。
        telop_dict: テロップ情報の辞書, logoとtextのペアをリストとして持つ。
        """
        # do nothing
        return None,None