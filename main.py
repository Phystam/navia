# main.py (Updated)
import sys
from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon, QAction
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

# clock.py から ClockApp をインポート
from clock import ClockApp

# メインアプリケーションクラス
class MainApp(QObject): # クラス名を変更して、ClockAppと区別しやすくしました
    def __init__(self, parent=None):
        super().__init__(parent)
        self.createTrayIcon() # タスクトレイアイコンを作成

    # タスクトレイアイコンを作成するメソッド
    def createTrayIcon(self):
        # タスクトレイアイコンのインスタンスを作成
        self.trayIcon = QSystemTrayIcon(self)
        # アイコンを設定（一時的にデフォルトのアプリケーションアイコンを使用。後で変更可能）
        # アイコンファイルが存在しない場合でも動作するように、QIcon.fromTheme()を使用
        # もしアイコンファイル（例: icon.png）を使用する場合は、QIcon("icon.png") のように指定
        self.trayIcon.setIcon(QIcon.fromTheme("applications-other", QIcon("materials/icon.svg"))) # 作成したロゴを使用

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
    # ClockAppはclock.pyからインポート
    clock_app = ClockApp()
    engine.rootContext().setContextProperty("clockApp", clock_app)

    # MainAppのインスタンスを作成し、QMLに公開（タスクトレイアイコン用）
    main_app_instance = MainApp()
    engine.rootContext().setContextProperty("mainApp", main_app_instance)


    # QMLファイルをロード
    # QMLファイルはPythonスクリプトと同じディレクトリにあると仮定
    engine.load("main.qml")

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
