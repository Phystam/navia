# main.py (Updated with Data Fetcher)
import sys
from PySide6.QtCore import QObject, Slot, Signal # アプリ部分を移動させても忘れずにimport
from PySide6.QtGui import QIcon, QAction
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

# clock.py から ClockApp をインポート
from clock import ClockApp
# jma_data_fetcher.py から JMADataFetcher をインポート
from jma_data_fetcher import JMADataFetcher

# メインアプリケーションクラス
class MainApp(QObject):
    
    telopDataReceived= Signal(dict)  # テロップ情報を受け取るためのシグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.createTrayIcon() # タスクトレイアイコンを作成

        # JMADataFetcher のインスタンスを作成
        # JMADataFetcherは内部でQTimerを持っており、定期的にデータ取得を行います
        self.jma_fetcher = JMADataFetcher(self)
        # JMADataFetcherからのシグナルをメインアプリのメソッドに接続
        self.jma_fetcher.dataFetched.connect(self.onDataFetched)
        self.jma_fetcher.telopDataReceived.connect(self.onTelopDataReceived)  # テロップデータを受け取る
        self.jma_fetcher.errorOccurred.connect(self.onErrorOccurred)
        

    # タスクトレイアイコンを作成するメソッド
    def createTrayIcon(self):
        # タスクトレイアイコンのインスタンスを作成
        self.trayIcon = QSystemTrayIcon(self)
        # 作成したロゴを使用（materials/icon.svg が存在しない場合は、適切なパスに変更するか、一時的にコメントアウトしてください）
        self.trayIcon.setIcon(QIcon.fromTheme("applications-other", QIcon("materials/icon.svg")))

        # メニューを作成
        trayMenu = QMenu()

        # 終了アクションを作成し、メニューに追加
        quitAction = QAction("終了", self)
        quitAction.triggered.connect(QApplication.quit) # アプリケーション終了に接続
        trayMenu.addAction(quitAction)
        testAction = QAction("試験", self)
        testAction.triggered.connect(self.onTest)
        trayMenu.addAction(testAction)
        # タスクトレイアイコンにメニューを設定
        self.trayIcon.setContextMenu(trayMenu)

        # タスクトレイアイコンを表示
        self.trayIcon.show()

    @Slot(str)
    def onDataFetched(self, file_path):
        """
        JMADataFetcherからデータが取得されたときに呼び出されるスロット。
        """
        print(f"メインアプリ: 新しいデータが取得され、保存されました: {file_path}")
        # ここで取得したデータ（file_path）をQMLに表示したり、読み上げたりする処理を追加できます。
        # 例: QMLに通知するシグナルを発行するなど

    @Slot(dict)
    def onTelopDataReceived(self, telop_dict):
        self.telopDataReceived.emit(telop_dict)

    @Slot(str)
    def onErrorOccurred(self, message):
        """
        JMADataFetcherからエラーが発生したときに呼び出されるスロット。
        """
        print(f"メインアプリ: エラー発生: {message}")
        # ここでユーザーにエラーを通知する（例: メッセージボックス表示）などの処理を追加できます。

    @Slot()
    def onTest(self):
        #entry_data=R"jmaxml_20250710_Samples/15_12_02_161130_VPWW54.xml"
        entry_data=R"jmaxml_20250710_Samples/17_04_02_250630_VXWW50.xml"
        with open(entry_data,"rb") as f:
            dataname=entry_data[-10:-4]
            print(dataname)
            data=f.read()
            self.jma_fetcher.processReport(dataname,data,test=True, playtelop=True)
            
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
    # このインスタンス内でJMADataFetcherも初期化されます
    main_app_instance = MainApp()
    engine.rootContext().setContextProperty("mainApp", main_app_instance)

    engine.rootContext().setContextProperty("clockApp", clock_app)
    # QMLファイルをロード
    # QMLファイルはPythonスクリプトと同じディレクトリにあると仮定
    engine.load("main.qml")

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())