# settings_manager.py
import json
import os
from PySide6.QtCore import QObject, Property, Signal, Slot

class SettingsManager(QObject):
    # 設定が変更されたことを通知するシグナル
    settingsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_file = "settings/settings.json"
        self._settings = self._load_settings()

        # 各設定項目をQMLからアクセス可能なプロパティとして公開
        # 注意: リストや辞書を直接Propertyで公開するとQML側での変更検知が難しい場合があるため、
        # 必要に応じてgetter/setterを工夫するか、QML側で直接操作するスロットを用意します。
        # ここでは、設定値を辞書として保持し、QMLからはその辞書全体を渡す/受け取る形式にします。

    def _load_settings(self):
        """設定ファイルを読み込みます。ファイルが存在しない場合はデフォルト値を返します。"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    print(f"設定をロードしました: {self.settings_file}")
                    return settings
            except json.JSONDecodeError as e:
                print(f"設定ファイルの読み込みエラー: {e}. デフォルト設定を使用します。")
                return self._get_default_settings()
        else:
            print("設定ファイルが見つかりません。デフォルト設定を使用します。")
            return self._get_default_settings()

    def _save_settings(self):
        """現在の設定をファイルに保存します。"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4, ensure_ascii=False)
            print(f"設定を保存しました: {self.settings_file}")
        except IOError as e:
            print(f"設定ファイルの保存エラー: {e}")

    def _get_default_settings(self):
        """デフォルトの設定値を返します。"""
        return {
        "general": {
            "theme": "dark",
            "data_retention_days": 30
        },
        "meteorology": {
            "notify_observatories_telop_level": { 
                "気象庁": {
                    "気象庁": 1,
                    "気象庁本庁": 1
                },
                "札幌管区": {
                    "札幌管区気象台": 2,
                    "函館地方気象台": 3,
                    "旭川地方気象台": 3,
                    "室蘭地方気象台": 3,
                    "釧路地方気象台": 3,
                    "網走地方気象台": 3,
                    "稚内地方気象台": 3,
                    "帯広測候所": 3
                },
                "仙台管区": {
                    "仙台管区気象台": 2,
                    "青森地方気象台": 3,
                    "盛岡地方気象台": 3,
                    "秋田地方気象台": 3,
                    "山形地方気象台": 3,
                    "福島地方気象台": 3
                },
                "東京管区": {
                    "東京管区気象台": 2,
                    "水戸地方気象台": 3,
                    "宇都宮地方気象台": 3,
                    "前橋地方気象台": 3,
                    "熊谷地方気象台": 3,
                    "銚子地方気象台": 3,
                    "横浜地方気象台": 3,
                    "新潟地方気象台": 3,
                    "富山地方気象台": 3,
                    "金沢地方気象台": 3,
                    "福井地方気象台": 3,
                    "甲府地方気象台": 3,
                    "長野地方気象台": 3,
                    "岐阜地方気象台": 3,
                    "静岡地方気象台": 3,
                    "名古屋地方気象台": 3,
                    "津地方気象台": 3
                },
                "大阪管区": {
                    "大阪管区気象台": 2,
                    "神戸地方気象台": 2,
                    "彦根地方気象台": 3,
                    "京都地方気象台": 3,
                    "奈良地方気象台": 3,
                    "和歌山地方気象台": 3,
                    "鳥取地方気象台": 3,
                    "松江地方気象台": 3,
                    "岡山地方気象台": 3,
                    "広島地方気象台": 3,
                    "徳島地方気象台": 3,
                    "高松地方気象台": 3,
                    "松山地方気象台": 3,
                    "高知地方気象台": 3
                },
                "福岡管区": {
                    "福岡管区気象台": 2,
                    "長崎地方気象台": 3,
                    "下関地方気象台": 3,
                    "佐賀地方気象台": 3,
                    "熊本地方気象台": 3,
                    "大分地方気象台": 3,
                    "宮崎地方気象台": 3,
                    "鹿児島地方気象台": 3,
                    "名瀬測候所": 3
                },
                "沖縄": {
                    "沖縄気象台": 2,
                    "宮古島地方気象台": 3,
                    "石垣島地方気象台": 3,
                    "南大東島地方気象台": 3
                }
            },
            "notify_observatories_alert": {
                "気象庁": True,
                "大阪管区気象台": True,
                "東京管区気象台": True
            },
            "display_region_level": "細分区域",
            "display_info_types": [
                "天気予報",
                "注意報",
                "警報"
            ]
        },
        "seismology": {
            "notify_regions": {
                "全国": True,
                "関東地方": False,
                "近畿地方": True
            },
            "min_magnitude": 2.5,
            "display_info_types": [
                "震源・震度情報",
                "津波情報"
            ]
        },
        "volcanology": {
            "notify_volcanoes": {
                "桜島": True,
                "阿蘇山": True
            },
            "display_info_types": [
                "噴火速報",
                "降灰予報"
            ]
        }
    }

    # QMLから設定全体にアクセスするためのプロパティ
    @Property(dict, notify=settingsChanged)
    def settings(self):
        return self._settings

    @Slot(str, str, str, bool)
    def updateBooleanSetting(self, category, sub_category, key, value):
        """
        ブーリアン型の設定を更新します。
        例: updateBooleanSetting("weather", "notify_observatories_warning", "気象庁", true)
        """
        if category in self._settings and sub_category in self._settings[category]:
            if key in self._settings[category][sub_category]:
                self._settings[category][sub_category][key] = value
                self.settingsChanged.emit()
                print(f"設定更新: {category}.{sub_category}.{key} = {value}")
            else:
                print(f"警告: 設定キー '{key}' が見つかりません。")
        else:
            print(f"警告: 設定カテゴリ '{category}' またはサブカテゴリ '{sub_category}' が見つかりません。")

    @Slot(str, str, str, str)
    def updateStringSetting(self, category, key, value):
        """
        文字列型の設定を更新します。
        例: updateStringSetting("weather", "display_region_level", "都道府県")
        """
        if category in self._settings:
            if key in self._settings[category]:
                self._settings[category][key] = value
                self.settingsChanged.emit()
                print(f"設定更新: {category}.{key} = {value}")
            else:
                print(f"警告: 設定キー '{key}' が見つかりません。")
        else:
            print(f"警告: 設定カテゴリ '{category}' が見つかりません。")

    @Slot(str, str, str, float) # int/float対応
    def updateNumberSetting(self, category, key, value):
        """
        数値型の設定を更新します。
        例: updateNumberSetting("earthquake", "min_magnitude", 3.0)
        """
        if category in self._settings:
            if key in self._settings[category]:
                self._settings[category][key] = value
                self.settingsChanged.emit()
                print(f"設定更新: {category}.{key} = {value}")
            else:
                print(f"警告: 設定キー '{key}' が見つかりません。")
        else:
            print(f"警告: 設定カテゴリ '{category}' が見つかりません。")
    
    @Slot()
    def saveSettings(self):
        """現在の設定をファイルに保存します。QMLから呼び出されます。"""
        self._save_settings()

    @Slot()
    def reloadSettings(self):
        """設定をファイルから再読み込みします。"""
        self._settings = self._load_settings()
        self.settingsChanged.emit() # QMLに更新を通知
