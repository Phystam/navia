# clock.py
from PySide6.QtCore import QObject, Slot, Property, QTimer, QDateTime, Signal

# 時計のロジックを扱うクラス
class ClockApp(QObject):
    # プロパティ変更をQMLに通知するためのシグナルを定義
    currentTimeStrChanged = Signal()
    currentDateStrChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._currentTimeStr = "" # 時刻部分を保持するプロパティ
        self._currentDateStr = "" # 日付部分を保持するプロパティ

        # 1秒ごとに時刻を更新するためのタイマーを設定
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000) # 1000ミリ秒（1秒）ごとにタイムアウト

        self.updateTime() # 初期時刻を設定

    # 時刻部分のゲッターとセッター、およびnotifyシグナル
    @Property(str, notify=currentTimeStrChanged)
    def currentTimeStr(self):
        return self._currentTimeStr

    def _setCurrentTimeStr(self, time_str):
        if self._currentTimeStr != time_str:
            self._currentTimeStr = time_str
            self.currentTimeStrChanged.emit() # 値が変更されたらシグナルを発行

    # 日付部分のゲッターとセッター、およびnotifyシグナル
    @Property(str, notify=currentDateStrChanged)
    def currentDateStr(self):
        return self._currentDateStr

    def _setCurrentDateStr(self, date_str):
        if self._currentDateStr != date_str:
            self._currentDateStr = date_str
            self.currentDateStrChanged.emit() # 値が変更されたらシグナルを発行

    # 時刻を更新するスロット
    @Slot()
    def updateTime(self):
        # 現在の時刻と日付を取得し、指定されたフォーマットで文字列化
        now = QDateTime.currentDateTime()
        time_str = now.toString("hh:mm") # 例: 12:34
        date_str = now.toString("yyyy/MM/dd(ddd)") # 例: 2023/07/01(月)

        self._setCurrentTimeStr(time_str)
        self._setCurrentDateStr(date_str)
