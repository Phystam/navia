import sys
from PySide6.QtCore import QObject, Slot, Property, QTimer, QDateTime
from PySide6.QtGui import QIcon, QAction
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu # QApplicationをQtWidgetsからインポート

# メインアプリケーションクラス
class ClockApp(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._currentTime = "" # 現在時刻を保持するプロパティ

        # 1秒ごとに時刻を更新するためのタイマーを設定
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000) # 1000ミリ秒（1秒）ごとにタイムアウト

        self.updateTime() # 初期時刻を設定

        self.createTrayIcon() # タスクトレイアイコンを作成

    # 現在時刻のゲッター
    @Property(str, notify=None) # notifyシグナルは今回は不要なのでNone
    def currentTime(self):
        return self._currentTime

    # 現在時刻のセッター（内部使用）
    def _setCurrentTime(self, time):
        if self._currentTime != time:
            self._currentTime = time
            # プロパティが変更されたことをQMLに通知するシグナルがあればここでemitする
            # 今回はnotify=Noneなので、QML側でタイマーを使って更新する

    # 時刻を更新するスロット
    @Slot()
    def updateTime(self):
        # 現在の時刻と日付を取得し、指定されたフォーマットで文字列化
        now = QDateTime.currentDateTime()
        time_str = now.toString("hh:mm") # 例: 12:34
        date_str = now.toString("yyyy/MM/dd(ddd)") # 例: 2023/07/01(月)
        self._setCurrentTime(f"{time_str}\n{date_str}") # 時刻と日付を結合して設定

    # タスクトレイアイコンを作成するメソッド
    def createTrayIcon(self):
        # タスクトレイアイコンのインスタンスを作成
        self.trayIcon = QSystemTrayIcon(self)
        # アイコンを設定（一時的にデフォルトのアプリケーションアイコンを使用。後で変更可能）
        # アイコンファイルが存在しない場合でも動作するように、QIcon.fromTheme()を使用
        # もしアイコンファイル（例: icon.png）を使用する場合は、QIcon("icon.png") のように指定
        self.trayIcon.setIcon(QIcon.fromTheme("applications-other", QIcon("./materials/icon.svg"))) # デフォルトのQtロゴをフォールバックとして使用

        # メニューを作成
        trayMenu = QMenu()

        # 終了アクションを作成し、メニューに追加
        quitAction = QAction("終了", self)
        quitAction.triggered.connect(QApplication.quit) # アプリケーション終了に接続
        trayMenu.addAction(quitAction)

        # タスクトレイアイコンにメニューを設定
        self.trayIcon.setContextMenu(trayMenu)

        # タスクトレイアイコンを表示
        self.trayIcon.show()


if __name__ == "__main__":
    # QApplicationを使用するように変更
    app = QApplication(sys.argv)

    # アプリケーションが最後のウィンドウを閉じても終了しないように設定
    # これにより、タスクトレイアイコンからの終了が可能になる
    app.setQuitOnLastWindowClosed(False)

    engine = QQmlApplicationEngine()

    # PythonオブジェクトをQMLに公開
    clock_app = ClockApp()
    engine.rootContext().setContextProperty("clockApp", clock_app)

    # QMLファイルをロード
    engine.load("main.qml")

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
