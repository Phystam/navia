# jma_parsers/jma_base_parser.py
from PySide6.QtCore import QObject, Signal
import re, math
from datetime import datetime,timedelta,timezone
from geopy.distance import geodesic,Distance
import geopy.distance
import numpy as np
class BaseJMAParser(QObject):
    # 解析されたデータを通知するシグナル (データタイプと解析済みデータ)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.jst = timezone(timedelta(hours=9))
        # 地球半径（km）
        self.RADIUS = 6371.0
    
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
    
    def _get_coordinates_degmin(self, element, xpath, namespaces):
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
                
                latitude_degmin = float(latitude_str) if latitude_str else None
                lat_sign=1 if latitude_degmin>=0 else -1
                latitude_deg=math.floor(abs(latitude_degmin)/100)
                latitude_min=(abs(latitude_degmin)-latitude_deg)/60
                latitude=lat_sign*(latitude_deg + latitude_min)
                
                longitude_degmin = float(longitude_str) if longitude_str else None
                lon_sign=1 if longitude_degmin>=0 else -1
                longitude_deg=math.floor(abs(longitude_degmin)/100)
                longitude_min=(abs(longitude_degmin)-longitude_deg)/60
                longitude=lon_sign*(longitude_deg+longitude_min)
                
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
        
        caution_code=["10","12","13","14","15","16","17","18","19",
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
            


    def calc_center_point(self, coord_lonlat, bearing_deg, distance_km):
        """
        球面近似での目的地計算
        lat_deg, lon_deg : 出発点の緯度・経度（度）
        bearing_deg       : 北から時計回りの方位角（度）
        distance_km       : 距離（km）
        戻り値            : (目的地緯度[度], 目的地経度[度])
        """
        pointA1=geopy.distance.distance(kilometers=distance_km).destination((coord_lonlat[1],coord_lonlat[0]),bearing=bearing_deg)
        # ラジアン→度変換
        return [pointA1[1],pointA1[0]]
    
    def ll_to_xy(self, lat, lon, ref_lat, ref_lon):
        """緯度経度を基準点からの平面座標(km)に変換します。"""
        lat_rad, lon_rad = math.radians(lat), math.radians(lon)
        ref_lat_rad, ref_lon_rad = math.radians(ref_lat), math.radians(ref_lon)

        x = self.RADIUS * (lon_rad - ref_lon_rad) * math.cos(ref_lat_rad)
        y = self.RADIUS * (lat_rad - ref_lat_rad)
        return np.array([x, y])

    def xy_to_ll(self, x, y, ref_lat, ref_lon):
        """平面座標(km)を緯度経度に変換します。"""
        ref_lat_rad, ref_lon_rad = math.radians(ref_lat), math.radians(ref_lon)

        lat_rad = (y /  self.RADIUS) + ref_lat_rad
        lon_rad = (x / (self.RADIUS * math.cos(ref_lat_rad))) + ref_lon_rad

        return math.degrees(lat_rad), math.degrees(lon_rad)

    def calculate_typhoon_envelope(self, positions, radii_km, points_per_arc=30):
        """
        台風の予測位置と暴風警戒域の半径から、その包絡線を計算します。
        positions: [[lon, lat], [lon, lat], ...]
        radii_km: [r1, r2, ...]
        """
        if len(positions) < 2:
            if not positions:
                return []
            # 円が1つの場合
            center_lon, center_lat = positions[0]
            radius_km = radii_km[0]
            envelope = []
            for angle in np.linspace(0, 360, 144, endpoint=False):
                dest = geodesic(kilometers=radius_km).destination((center_lat, center_lon), angle)
                envelope.append([dest.longitude, dest.latitude])
            envelope.append(envelope[0]) # 閉じる
            return envelope

        # 基準点を設定 最初の円の中心とする
        ref_lon, ref_lat = positions[0]

        # 緯度経度をxy座標(km)に変換
        xy_coords = [self.ll_to_xy(lat, lon, ref_lat, ref_lon) for lon, lat in positions]

        # 接線と円弧で包絡線を構築
        # 包絡線を描く配列の初期化
        envelope_xy = []
        
        # 最初の円の
        p1, r1 = xy_coords[0], radii_km[0]
        p2, r2 = xy_coords[1], radii_km[1]
        
        result = self.connectTwoCircles(self,positions[0],positions[1],radii_km[0],radii_km[1])
        d = np.linalg.norm(p2 - p1)
        
        # 2円間の角度
        theta = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        
        # 共通外接線の角度
        if d < abs(r1 - r2): # 片方の円がもう片方を完全に含む
             # 大きい方の円を返す
            if r1 > r2:
                 return self.calculate_typhoon_envelope([positions[0]], [radii_km[0]], points_per_arc)
            else:
                 return self.calculate_typhoon_envelope([positions[1]], [radii_km[1]], points_per_arc)

        alpha = math.acos((r1 - r2) / d)

        # 最初の円の開始点 (右側接点)
        angle1_r = theta - alpha
        
        # 最初の円の半円部分を追加
        # 進行方向右側の半円
        vec_start = xy_coords[1] - xy_coords[0]
        init_angle = math.atan2(vec_start[1], vec_start[0]) - math.pi / 2
        
        angles = np.linspace(angle1_r, init_angle, points_per_arc)#np.linspace(init_angle, angle1_r, points_per_arc)
        envelope_xy.extend([p1 + r1 * np.array([np.cos(a), np.sin(a)]) for a in angles])


        # 中間の円と接線
        for i in range(len(xy_coords) - 1):
            p1, r1 = xy_coords[i], radii_km[i]
            p2, r2 = xy_coords[i+1], radii_km[i+1]
            d = np.linalg.norm(p2 - p1)

            if d < 1e-6: continue
            if d < abs(r1 - r2): # 円が内包される場合、スキップ
                continue

            theta = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            alpha = math.acos((r1 - r2) / d)

            # 右側接線
            angle1_r = theta - alpha
            angle2_r = theta - alpha
            t1_r = p1 + r1 * np.array([math.cos(angle1_r), math.sin(angle1_r)])
            t2_r = p2 + r2 * np.array([math.cos(angle2_r), math.sin(angle2_r)])
            
            # 前の円弧の終わりから接線開始点まで
            if i > 0:
                prev_p2, prev_r2 = xy_coords[i-1], radii_km[i-1]
                prev_d = np.linalg.norm(p1 - prev_p2)
                if prev_d > abs(prev_r2-r1):
                    prev_theta = math.atan2(p1[1] - prev_p2[1], p1[0] - prev_p2[0])
                    prev_alpha = math.acos((prev_r2 - r1) / prev_d)
                    angle_end_arc = prev_theta - prev_alpha
                    angles = np.linspace(angle_end_arc, angle1_r, points_per_arc)
                    envelope_xy.extend([p1 + r1 * np.array([np.cos(a), np.sin(a)]) for a in angles])

            envelope_xy.append(t1_r)
            envelope_xy.append(t2_r)

        # 最後の円の半円
        pn, rn = xy_coords[-1], radii_km[-1]
        p_prev, r_prev = xy_coords[-2], radii_km[-2]
        d = np.linalg.norm(pn - p_prev)
        theta = math.atan2(pn[1] - p_prev[1], pn[0] - p_prev[0])
        alpha = math.acos((r_prev - rn) / d)
        
        angle_n_r = theta - alpha
        angle_n_l = theta + alpha
        
        angles = np.linspace(angle_n_r, angle_n_l, points_per_arc * 2)
        envelope_xy.extend([pn + rn * np.array([np.cos(a), np.sin(a)]) for a in angles])

        # 左側の接線を逆順に追加
        for i in range(len(xy_coords) - 1, 0, -1):
            p1, r1 = xy_coords[i], radii_km[i]
            p2, r2 = xy_coords[i-1], radii_km[i-1]
            d = np.linalg.norm(p1 - p2)

            if d < 1e-6: continue
            if d < abs(r1 - r2): continue

            theta = math.atan2(p1[1] - p2[1], p1[0] - p2[0])
            alpha = math.acos((r2 - r1) / d)

            # 左側接線
            angle1_l = theta - alpha
            angle2_l = theta - alpha
            t1_l = p1 + r1 * np.array([math.cos(angle1_l), math.sin(angle1_l)])
            t2_l = p2 + r2 * np.array([math.cos(angle2_l), math.sin(angle2_l)])
            
            # 円弧部分
            if i < len(xy_coords) -1:
                next_p, next_r = xy_coords[i], radii_km[i]
                next_p1, next_r1 = xy_coords[i+1], radii_km[i+1]
                next_d = np.linalg.norm(next_p1 - next_p)
                if next_d > abs(next_r - next_r1):
                    next_theta = math.atan2(next_p1[1] - next_p[1], next_p[0] - next_p[0])
                    next_alpha = math.acos((next_r - next_r1) / next_d)
                    angle_start_arc = next_theta + next_alpha
                    angles = np.linspace(angle_start_arc, angle1_l, points_per_arc)
                    envelope_xy.extend([p1 + r1 * np.array([np.cos(a), np.sin(a)]) for a in angles])

            envelope_xy.append(t1_l)
            envelope_xy.append(t2_l)

        # 最初の円の最後の円弧
        p_first, r_first = xy_coords[0], radii_km[0]
        p_second, r_second = xy_coords[1], radii_km[1]
        d = np.linalg.norm(p_second - p_first)
        theta = math.atan2(p_second[1] - p_first[1], p_second[0] - p_first[0])
        alpha = math.acos((r_first - r_second) / d)
        angle_first_l_end = theta + alpha
        
        angles = np.linspace(angle_first_l_end, init_angle, points_per_arc)
        envelope_xy.extend([p_first + r_first * np.array([np.cos(a), np.sin(a)]) for a in angles])


        # xy座標を緯度経度に戻す
        envelope_ll = [self.xy_to_ll(x, y, ref_lat, ref_lon) for x, y in envelope_xy]
        
        # [lon, lat] の形式に変換
        envelope_lonlat = [[lon, lat] for lat, lon in envelope_ll]
        if envelope_lonlat:
            envelope_lonlat.append(envelope_lonlat[0]) # 閉じる

        return envelope_lonlat

    def connectTwoCircles(self,lonlat1,lonlat2,radius1,radius2):
        cons=math.pi/180.
        point1=[lonlat1[1],lonlat1[0]]
        point2=[lonlat2[1],lonlat2[0]]
        length1=geodesic(point1,point2).kilometers
        print(length1)
        if length1<abs(radius1-radius2):
            return None, None
        delta_lon=lonlat2[0]-lonlat1[0]
        x=math.cos(cons*lonlat1[1])*math.tan(cons*lonlat2[1])-math.sin(cons*lonlat1[1])*math.cos(cons*(delta_lon))
        y=math.sin(cons*delta_lon)
        phi=90-math.atan2( x,y )/cons
        
        theta=math.asin((radius1-radius2)/length1)/cons
        ##2点の角度を求める /rad
        pointA_deg=phi+90-theta
        pointB_deg=phi-90+theta
        print(f'{theta},{phi},{pointA_deg}')
        pointA1=geopy.distance.distance(kilometers=radius1).destination(point1,bearing=pointA_deg)
        pointA2=geopy.distance.distance(kilometers=radius2).destination(point2,bearing=pointA_deg)
        pointB1=geopy.distance.distance(kilometers=radius1).destination(point1,bearing=pointB_deg)
        pointB2=geopy.distance.distance(kilometers=radius2).destination(point2,bearing=pointB_deg)
        
        return [[pointA1[1],pointA1[0]],[pointA2[1],pointA2[0]]], [[pointB1[1],pointB1[0]],[pointB2[1],pointB2[0]]]
    
    def drawCircle(self,lonlat1,radius1,start_deg=0, end_deg=360):
        cons=math.pi/180.
        point1=[lonlat1[1],lonlat1[0]]
        path=[]
        for deg in range(start_deg,end_deg,2.5):
            point=geopy.distance.distance(kilometers=radius1).destination(point1,bearing=deg)
            path.append([point[1],point[0]])
        # end_deg を個別に処理
        point=geopy.distance.distance(kilometers=radius1).destination(point1,bearing=end_deg)
        path.append([point[1],point[0]])
        return path

