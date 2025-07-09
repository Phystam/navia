# jma_parsers/jma_earthquake_parser.py
from .jma_base_parser import BaseJMAParser

class VXSE53(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VXSE53" # このパーサーが扱うデータタイプ

    def parse(self, xml_tree, namespaces, data_type_code):
        """
        地震情報 (VXSE53) のXMLを解析します。
        """
        print(f"地震情報 ({self.data_type}) を解析中...")
        parsed_data = {}

        # Control/Title
        parsed_data['control_title'] = self._get_text(xml_tree, '/jmx:Report/jmx:Control/jmx:Title/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Title/text()', namespaces)
        # Head/Headline/Text
        parsed_data['headline_text'] = self._get_text(xml_tree, '/jmx:Report/jmx_ib:Head/jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        # Body/Earthquake/Hypocenter/Area/Name (震央地名)
        parsed_data['hypocenter_name'] = self._get_text(xml_tree, '/jmx:Report/jmx_seis:Body/jmx_seis:Earthquake/jmx_seis:Hypocenter/jmx_seis:Area/jmx_seis:Name/text()', namespaces)
        # Body/Earthquake/Magnitude/@description (マグニチュードの説明)
        parsed_data['magnitude_description'] = self._get_attribute(xml_tree, '/jmx:Report/jmx_seis:Body/jmx_seis:Earthquake/jmx_eb:Magnitude/@description', namespaces)
        # Body/Earthquake/Magnitude/Value (マグニチュードの値)
        parsed_data['magnitude_value'] = self._get_text(xml_tree, '/jmx:Report/jmx_seis:Body/jmx_seis:Earthquake/jmx_eb:Magnitude/text()', namespaces)
        # Body/Intensity/Observation/MaxInt (最大震度)
        parsed_data['max_intensity'] = self._get_text(xml_tree, '/jmx:Report/jmx_seis:Body/jmx_seis:Intensity/jmx_seis:Observation/jmx_seis:MaxInt/text()', namespaces)
        # Body/Comments/ForecastComment/Text (津波の心配など)
        parsed_data['forecast_comment'] = self._get_text(xml_tree, '/jmx:Report/jmx_seis:Body/jmx_seis:Comments/jmx_seis:ForecastComment/jmx_seis:Text/text()', namespaces)

        # 必要に応じて、さらに詳細な震度情報などを抽出することも可能

        self.parsedData.emit(self.data_type, parsed_data)
        return parsed_data
