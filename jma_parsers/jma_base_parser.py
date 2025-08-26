# jma_parsers/jma_base_parser.py
from PySide6.QtCore import QObject, Signal
import re
from datetime import datetime,timedelta,timezone

class BaseJMAParser(QObject):
    # 解析されたデータを通知するシグナル (データタイプと解析済みデータ)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.jst = timezone(timedelta(hours=9))
    
    def parse(self, xml_tree, namespaces, data_type_code, test):
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

    def _get_text(self, element, xpath, namespaces, default=""):
        """XPathで要素のテキストを取得するヘルパー関数"""
        result = element.xpath(xpath, namespaces=namespaces)
        return result[0] if result else default
    
    def _get_elements(self, element, xpath, namespaces, default=[]):
        """XPathで要素のテキストを取得するヘルパー関数"""
        result = element.xpath(xpath, namespaces=namespaces)
        return result if result else default

    def _get_attribute(self, element, xpath, namespaces, default=""):
        """XPathで要素の属性を取得するヘルパー関数"""
        result = element.xpath(xpath, namespaces=namespaces)
        return result[0] if result else default
    
    def _get_datetime(self, element, xpath, namespaces, default=datetime(2000,1,1,0,0,0)):
        """XPathで要素の属性を取得するヘルパー関数"""
        result = element.xpath(xpath, namespaces=namespaces)
        return datetime.fromisoformat(result[0]) if result else default
    
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
            #print(f"座標データ: {entry.strip()}")
            # 各要素を正規表現で抽出
            # 緯度、経度、高度がそれぞれ+または-で始まり、数字が続くことを想定
            match = re.match(r'([+-]\d+\.\d+)([+-]\d+\.\d+)([+-]\d+)?', entry.strip())
            if match:
                latitude_str = match.group(1)
                longitude_str = match.group(2)
                altitude_str = match.group(3)
                #print(f"lat: {latitude_str}, lon: {longitude_str}, alt: {altitude_str}")
                #latitude = self.dms_to_decimal(latitude_str)
                #longitude = self.dms_to_decimal(longitude_str)
                latitude = float(latitude_str) if latitude_str else None
                longitude = float(longitude_str) if longitude_str else None
                if altitude_str is not None:
                    altitude = int(altitude_str) # 高度は常に整数
                else:
                    altitude = None
                if latitude is not None and longitude is not None:
                    results.append({'latitude': latitude,
                                    'longitude': longitude,
                                    'altitude': altitude})
                else:
                    results.append(f'エラー: 無効なデータ形式 - {entry}')
            else:
                results.append(f'エラー: パースに失敗 - {entry}')
        return results
    
    def _get_coordinates_list(self, element, xpath, namespaces):
        """座標情報を取得するヘルパー関数 
        高度を考慮しない[lat,lon]形式のリストを返す"""
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
            #print(f"座標データ: {entry.strip()}")
            # 各要素を正規表現で抽出
            # 緯度、経度がそれぞれ+または-で始まり、数字が続くことを想定
            match = re.match(r'([+-]\d+\.\d+)([+-]\d+\.\d+)', entry.strip())
            if match:
                latitude_str = match.group(1)
                longitude_str = match.group(2)
                #print(f"lat: {latitude_str}, lon: {longitude_str}")
                #latitude = self.dms_to_decimal(latitude_str)
                #longitude = self.dms_to_decimal(longitude_str)
                latitude = float(latitude_str) if latitude_str else None
                longitude = float(longitude_str) if longitude_str else None
                if latitude is not None and longitude is not None:
                    # geojsonでは経度、緯度の順
                    results.append([longitude,latitude])
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
        
    def format_and_append_text(self, txt:str, logo_list:list, text_list:list, sound_list:list):
        """テキストをテロップ用に区切り、適切にリスト化する。

        Args:
            txt (_type_): _description_

        Returns:
            list: _description_
        """
        yaku =["＞", "》", "】","］","〉"]
        # txtを句点または改行で分割
        tlist=re.split("[。\\n]",txt)
        # 空の行を削除
        tlist = [ line for line in tlist if line != "" ] 
        
        # 要素数が奇数の場合、空文字を追加して偶数にする
        if len(tlist) %2 != 0:
            tlist.append("")
        for i in range(len(tlist)):
            # 消された句点を復元
            # 約物括弧付きの行は。をつけない
            if set(yaku).isdisjoint(set(tlist[i])):
                tlist[i] = f"{tlist[i]}。"
            if tlist[i]=="。":
                tlist[i]=""
            # 奇数番目のとき、2行分のリストを追加
            if i % 2 == 1:
                sound_list.append("")
                logo_list.append(["", ""])
                text_list.append(tlist[i-1:i+1])

    def get_warning_level(self,codeelement):
        
        caution_code=["10","12","13","14","15","16","17","18",
                      "20","21,","22","23","24","25","26","27"]
        warning_code=["02","03","04","05","06","07"]
        special_code=["32","35","36","37","38","08"]
        emergency_code=["33"]
        if "00" in codeelement:
            return 0
        
        for item in emergency_code:
            if item in codeelement:
                return 5
        for item in special_code:
            if item in codeelement:
                return 4
        for item in warning_code:
            if item in codeelement:
                return 3
        for item in caution_code:
            if item in codeelement:
                return 2