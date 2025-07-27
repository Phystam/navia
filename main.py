# main.py (Updated with Data Fetcher)
import sys
from PySide6.QtCore import QObject, QUrl, Slot, Signal # アプリ部分を移動させても忘れずにimport
from PySide6.QtGui import QIcon, QAction
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

# clock.py から ClockApp をインポート
from clock import ClockApp
# jma_data_fetcher.py から JMADataFetcher をインポート
from jma_data_fetcher import JMADataFetcher
from settings_manager import SettingsManager
from navia_broadcast import Broadcaster
from seis_timeline import SeisTimeline
# メインアプリケーションクラス
class MainApp(QObject):
    
    telopDataReceived= Signal(dict)  # テロップ情報を受け取るためのシグナル
    onSettingsApplied = Signal(dict)
    
    def __init__(self, engine_instance, parent=None):
        super().__init__(parent)
        self.engine = engine_instance
        self.createTrayIcon() # タスクトレイアイコンを作成

        # JMADataFetcher のインスタンスを作成
        # JMADataFetcherは内部でQTimerを持っており、定期的にデータ取得を行います
        self.jma_fetcher = JMADataFetcher(self)
        # 設定用インスタンス
        self.settings_manager = SettingsManager(self)
        self.settings_manager._load_settings()
        self.settings_window_qml_object = None
        
        self.seis_timeline = SeisTimeline(self)
        self.seis_timeline._load_data()
        self.seismology_window_qml_object = None
        # ラジオ用インスタンス
        self.broadcaster = Broadcaster(self)
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

        # 設定メニューを追加
        settingsAction = QAction("設定", self)
        settingsAction.triggered.connect(self.showSettings)
        trayMenu.addAction(settingsAction)

        # 区切り線
        trayMenu.addSeparator()

        # 情報表示メニュー（仮）
        infoMenu = trayMenu.addMenu("情報")
        infoMenu.addAction(QAction("気象情報", self))
        infoMenu.addAction(QAction("地震情報", self))
        infoMenu.addAction(QAction("火山情報", self))
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
    def showSettings(self):
        print("設定メニューがクリックされました。")
        if not self.engine:
            print("QMLエンジンが初期化されていません。")
            return

        if not self.settings_window_qml_object:
            # settings.qmlをロードし、QMLオブジェクトとして保持
            # Loaderを使う代わりに、直接Windowをロードして表示する
            component = QQmlComponent(self.engine, QUrl.fromLocalFile("qml_components/settings.qml"))
            if component.status() == QQmlComponent.Ready:
                self.settings_window_qml_object = component.create()
                if self.settings_window_qml_object:
                    # QMLのsettingsManagerプロパティにPythonのインスタンスをセット
                    self.settings_window_qml_object.setProperty("settingsManager", self.settings_manager)
                    # QMLのsettingsAppliedシグナルをPythonのスロットに接続
                    self.settings_window_qml_object.settingsApplied.connect(self.onSettingsApplied)
                    self.settings_window_qml_object.show()
                    print("設定ウィンドウを表示しました。")
                else:
                    print("設定ウィンドウの作成に失敗しました。")
            else:
                print(f"設定QMLファイルのロードに失敗しました: {component.errorString()}")
        else:
            # 既にウィンドウが存在する場合は表示するだけ
            self.settings_window_qml_object.show()
            self.settings_manager.reloadSettings() # 設定を再読み込みして最新の状態を反映
            print("既存の設定ウィンドウを表示しました。")
        # ここに設定画面を表示するロジックを追加
        
    @Slot()
    def showSeismology(self):
        print("地震情報メニューがクリックされました。")
        if not self.engine:
            print("QMLエンジンが初期化されていません。")
            return

        if not self.seismology_window_qml_object:
            # settings.qmlをロードし、QMLオブジェクトとして保持
            # Loaderを使う代わりに、直接Windowをロードして表示する
            component = QQmlComponent(self.engine, QUrl.fromLocalFile("seis_timeline.qml"))
            if component.status() == QQmlComponent.Ready:
                self.seismology_window_qml_object = component.create()
                if self.seismology_window_qml_object:
                    # QMLのsettingsManagerプロパティにPythonのインスタンスをセット
                    self.seismology_window_qml_object.setProperty("seisTimeline", self.settings_manager)
                    self.seismology_window_qml_object.show()
                    print("設定ウィンドウを表示しました。")
                else:
                    print("設定ウィンドウの作成に失敗しました。")
            else:
                print(f"設定QMLファイルのロードに失敗しました: {component.errorString()}")
        else:
            # 既にウィンドウが存在する場合は表示するだけ
            self.settings_window_qml_object.show()
            self.settings_manager.reloadSettings() # 設定を再読み込みして最新の状態を反映
            print("既存の設定ウィンドウを表示しました。")
        # ここに設定画面を表示するロジックを追加

    @Slot()
    def onTest(self):
        #entry_data=R"jmaxml_20250710_Samples/15_12_02_161130_VPWW54.xml"
        entry_data=R"jmaxml_20250710_Samples/45_02_01_200522_VFVO50.xml"
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
    main_app_instance = MainApp(engine)
    engine.rootContext().setContextProperty("clockApp", clock_app)
    engine.rootContext().setContextProperty("mainApp", main_app_instance)
    engine.rootContext().setContextProperty("settingsManager", main_app_instance.settings_manager)
    # MainAppのインスタンスを作成し、QMLに公開（タスクトレイアイコン用）
    # このインスタンス内でJMADataFetcherも初期化されます
    
    
    # QMLファイルをロード
    # QMLファイルはPythonスクリプトと同じディレクトリにあると仮定
    engine.load("main.qml")

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
    