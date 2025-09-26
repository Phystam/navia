import json
from pathlib import Path
from PySide6.QtCore import QObject, Slot, QUrl, QVariant
from PySide6.QtPositioning import QGeoCoordinate

class MapManager(QObject):
    def __init__(self, timeline_manager, parent=None):
        """
        MapManagerのコンストラクタ
        :param timeline_manager: 既存のtimelineManagerオブジェクトへの参照
        :param parent: 親QObject
        """
        super().__init__(parent)
        self._timeline_manager = timeline_manager
        self._geojson_cache = {}
        self._current_dir = Path(__file__).parent.resolve()

    def _get_color_by_warning_level(self, level):
        """
        警報レベルに応じた色を返す
        """
        return {
            0: "#c8c8cb",  # 平常
            1: "#ffffff",  # レベル1・早期注意情報
            2: "#f2e700",  # レベル2・注意報
            3: "#ff2800",  # レベル3・警報
            4: "#aa00aa",  # レベル4・特別警報など
            5: "#0c000c",  # レベル5・大雨特別警報
        }.get(level, "#c8c8cb") # デフォルトは平常

    def _load_geojson(self, hierarchy):
        """
        指定された階層のGeoJSONファイルを読み込み、キャッシュする
        """
        if hierarchy in self._geojson_cache:
            return self._geojson_cache[hierarchy]

        # ファイルパスのマッピング
        file_map = {
            "pref": "geo/府県予報区等.geojson",
            "class10": "geo/一次細分区域等.geojson",
            "class15": "geo/市町村等をまとめた地域等.geojson",
            "class20": "geo/市町村等（気象警報等）.geojson",
        }

        file_path = self._current_dir / file_map.get(hierarchy)
        if not file_path or not file_path.exists():
            print(f"Error: GeoJSON file not found for hierarchy '{hierarchy}' at {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._geojson_cache[hierarchy] = data
                return data
        except Exception as e:
            print(f"Error loading or parsing GeoJSON for '{hierarchy}': {e}")
            return None

    @Slot(str, result=QVariant)
    def getMapViewModel(self, hierarchy):
        """
        QMLのMapItemViewに渡すための描画用モデルを生成する
        :param hierarchy: 地図の階層 ('pref', 'class10'など)
        :return: QVariantList形式の描画データ
        """
        geojson_data = self._load_geojson(hierarchy)
        if not geojson_data or 'features' not in geojson_data:
            return []

        view_model = []
        for feature in geojson_data['features']:
            properties = feature.get('properties', {})
            code = properties.get('code')
            name = properties.get('name')
            
            if not code:
                continue

            # timelineManagerから警報レベルを取得
            level = self._timeline_manager.getMeteWarningLevel(hierarchy, code)
            color = self._get_color_by_warning_level(level)

            geometry = feature.get('geometry', {})
            geom_type = geometry.get('type')
            coordinates = geometry.get('coordinates')

            if not geom_type or not coordinates:
                continue

            # QMLで扱える形式にポリゴンデータを変換
            paths = []
            if geom_type == 'Polygon':
                for ring in coordinates:
                    path = [QGeoCoordinate(lat, lon) for lon, lat in ring]
                    paths.append(path)
            elif geom_type == 'MultiPolygon':
                for polygon in coordinates:
                    for ring in polygon:
                        path = [QGeoCoordinate(lat, lon) for lon, lat in ring]
                        paths.append(path)
            
            # 1地物に対する描画情報をまとめる
            # QML側では、この 'path', 'color', 'code', 'name' を直接利用する
            item = {
                'path': paths, # 1地物が複数のポリゴンを持つ場合に対応
                'color': color,
                'code': code,
                'name': name
            }
            view_model.append(item)

        return view_model