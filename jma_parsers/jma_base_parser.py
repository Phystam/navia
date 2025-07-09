# jma_parsers/jma_base_parser.py
from PySide6.QtCore import QObject, Signal
import re

class BaseJMAParser(QObject):
    # 解析されたデータを通知するシグナル (データタイプと解析済みデータ)
    parsedData = Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
    
    def parse(self, xml_tree, namespaces, data_type_code):
        """
        XMLツリーと名前空間を受け取り、データを解析して辞書として返します。
        このメソッドは子クラスでオーバーライドされるべきです。
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def content(self, xml_tree, namespaces, data_type_code):
        """
        XMLツリーと名前空間を受け取り、データを解析して辞書として返します。
        このメソッドは子クラスでオーバーライドされるべきです。
        telop_dict: テロップ情報の辞書, logoとtextのペアをリストとして持つ。
        
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _get_text(self, element, xpath, namespaces, default="N/A"):
        """XPathで要素のテキストを取得するヘルパー関数"""
        result = element.xpath(xpath, namespaces=namespaces)
        return result[0] if result else default

    def _get_attribute(self, element, xpath, namespaces, default="N/A"):
        """XPathで要素の属性を取得するヘルパー関数"""
        result = element.xpath(xpath, namespaces=namespaces)
        return result[0] if result else default
    
    def _get_coordinates(self, element, xpath, namespaces):
        """座標情報を取得するヘルパー関数"""
        data_string = element.xpath(xpath, namespaces=namespaces)
        """
        入力されたテキストデータを(緯度, 経度, 高度)の順にフォーマットします。
        """
        results = []
        # /区切りで配列になることを考慮
        entries = data_string[0].split('/')
        for entry in entries:
            if not entry.strip():
                continue
            print(f"座標データ: {entry.strip()}")
            # 各要素を正規表現で抽出
            # 緯度、経度、高度がそれぞれ+または-で始まり、数字が続くことを想定
            match = re.match(r'([+-]\d+\.\d+)([+-]\d+\.\d+)([+-]\d+)', entry.strip())
            if match:
                latitude_str = match.group(1)
                longitude_str = match.group(2)
                altitude_str = match.group(3)

                #latitude = self.dms_to_decimal(latitude_str)
                #longitude = self.dms_to_decimal(longitude_str)
                latitude = float(latitude_str) if latitude_str else None
                longitude = float(longitude_str) if longitude_str else None
                altitude = int(altitude_str) # 高度は常に整数

                if latitude is not None and longitude is not None:
                    results.append({'latitude': latitude,
                                    'longitude': longitude,
                                    'altitude': altitude})
                else:
                    results.append(f'エラー: 無効なデータ形式 - {entry}')
            else:
                results.append(f'エラー: パースに失敗 - {entry}')
        return results
    
    def dms_to_decimal(self, dms_str):
        """
        度分秒形式の文字列を10進数の度数に変換します。
        例: "+3135.55" -> 31.5925
            "-3135.55" -> -31.5925
        """
        sign = 1
        if dms_str.startswith('-'):
            sign = -1
            dms_str = dms_str[1:] # 符号を除去

        # 度の部分を抽出
        degrees_str = dms_str[:2]
        minutes_seconds_str = dms_str[2:]

        try:
            degrees = int(degrees_str)
            # 分と秒の小数点以下を考慮して変換
            minutes_seconds = float(minutes_seconds_str)
            minutes = int(minutes_seconds / 100) # 最初の2桁が分
            seconds = minutes_seconds % 100 # 残りが秒

            decimal_degrees = degrees + (minutes / 60) + (seconds / 3600)
            return sign * decimal_degrees
        except ValueError:
            return None # 変換失敗