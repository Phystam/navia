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
                "notify_observatories_warning": { # 注意報以上
                    "気象庁": True,
                    "札幌管区気象台": True,
                    "函館地方気象台": False,
                    "旭川地方気象台": False,
                    "室蘭地方気象台": False,
                    "釧路地方気象台": False,
                    "網走地方気象台": False,
                    "稚内地方気象台": False,
                    "大阪管区気象台": False,
                    "東京管区気象台": True
                },
                "notify_observatories_alert": { # 警報以上
                    "気象庁": True,
                    "大阪管区気象台": True,
                    "東京管区気象台": True
                },
                "display_region_level": "細分区域", # 地域区分
                "display_info_types": ["天気予報", "注意報", "警報"] # テロップ表示情報
            },
            "seismology": {
                "notify_regions": { # 通知する地域
                    "全国": True,
                    "関東地方": False,
                    "近畿地方": True
                },
                "min_magnitude": 2.5, # 規模
                "display_info_types": ["震源・震度情報", "津波情報"] # テロップ表示情報
            },
            "volcanology": {
                "notify_volcanoes": { # 通知する火山
                    "桜島": True,
                    "阿蘇山": False
                },
                "display_info_types": ["噴火速報", "降灰予報"] # テロップ表示情報
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
