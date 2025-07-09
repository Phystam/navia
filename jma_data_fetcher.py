import zstd # zstd圧縮ライブラリ
import xml.etree.ElementTree as ET # XMLパース用
import os
import re # 正規表現用
from PySide6.QtCore import QObject, QTimer, Signal, Slot, QDateTime, QUrl, QByteArray
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply # QtNetwork関連のインポート

class JMADataFetcher(QObject):
    # 新しいデータが取得され、保存されたことを通知するシグナル
    # 引数として保存されたファイルのパスを渡します
    dataFetched = Signal(str)
    # エラーが発生したことを通知するシグナル
    # 引数としてエラーメッセージを渡します
    errorOccurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 対象とするAtomフィードのURL
        self.feed_url = "https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml"
        # 前回の取得時のLast-Modifiedヘッダー値を保存（If-Modified-Since用）
        self.last_modified = None
        # 圧縮データを保存するディレクトリ
        self.data_dir = "jmadata"

        # QNetworkAccessManagerのインスタンスを作成
        self.network_manager = QNetworkAccessManager(self)

        # データ保存ディレクトリが存在しない場合は作成
        os.makedirs(self.data_dir, exist_ok=True)

        # 定期的に更新をチェックするためのタイマーを設定
        self.fetch_timer = QTimer(self)
        self.fetch_timer.setInterval(20 * 1000) # 20秒ごとにタイムアウト
        self.fetch_timer.timeout.connect(self.checkForUpdates)
        self.fetch_timer.start()

        # アプリケーション起動時に一度更新をチェック
        self.checkForUpdates()

    @Slot()
    def checkForUpdates(self):
        """
        Atomフィードにアクセスし、更新があるかチェックします。
        更新があれば、新しいエントリのXMLデータを取得・処理します。
        """
        request = QNetworkRequest(QUrl(self.feed_url))

        # 前回取得時のLast-Modifiedがあれば、If-Modified-Sinceヘッダーに追加
        if self.last_modified:
            # QNetworkRequestのヘッダーはバイト配列で設定
            request.setRawHeader(QByteArray(b"If-Modified-Since"), QByteArray(self.last_modified.encode('utf-8')))

        # GETリクエストを送信し、返信が完了したらhandleFeedReplyスロットを呼び出す
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.handleFeedReply(reply))

    @Slot(QNetworkReply)
    def handleFeedReply(self, reply: QNetworkReply):
        """
        Atomフィードへのリクエストが完了したときに呼び出されるスロット。
        """
        try:
            if reply.error() != QNetworkReply.NoError:
                # ネットワークエラーが発生した場合
                self.errorOccurred.emit(f"フィード取得時のネットワークエラー {self.feed_url}: {reply.errorString()}")
                return

            # HTTPステータスコードを取得
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

            # ステータスコードが304 Not Modifiedの場合、更新がないので処理を終了
            if status_code == 304:
                print(f"フィードは更新されていません: {self.feed_url}")
                return

            # Last-Modifiedヘッダーを更新
            # rawHeaderの引数をQByteArrayからstrに変更
            last_modified_header = reply.rawHeader("Last-Modified").data().decode('utf-8')
            if last_modified_header:
                self.last_modified = last_modified_header
            else:
                self.last_modified = None # ヘッダーがない場合はリセット

            # AtomフィードのXMLコンテンツを読み込む
            feed_content = reply.readAll().data()

            # AtomフィードのXMLをパース
            feed_root = ET.fromstring(feed_content)
            # AtomフィードのXML名前空間を定義
            ATOM_NS = "{http://www.w3.org/2005/Atom}"

            # 新しいエントリを格納するリスト
            new_entries = []
            # feed > entry から新しいエントリを検索
            for entry in feed_root.findall(f"{ATOM_NS}entry"):
                entry_id = entry.find(f"{ATOM_NS}id").text
                entry_updated = entry.find(f"{ATOM_NS}updated").text # ISO 8601形式
                entry_title = entry.find(f"{ATOM_NS}title").text
                # JMAのAtomフィードでは、idタグが実際のレポートXMLへのリンクになっている
                report_url = entry_id

                new_entries.append({'id': entry_id, 'updated': entry_updated, 'title': entry_title, 'url': report_url})

            if new_entries:
                print(f"新しいエントリが {len(new_entries)} 件見つかりました。")
                for entry_data in new_entries:
                    self.fetchAndProcessReport(entry_data)

        except ET.ParseError as e:
            # XMLパースエラーを捕捉
            self.errorOccurred.emit(f"フィードXMLパースエラー {self.feed_url}: {e}")
        except Exception as e:
            # その他の予期せぬエラーを捕捉
            self.errorOccurred.emit(f"フィード処理中に予期せぬエラーが発生しました: {e}")
        finally:
            reply.deleteLater() # QNetworkReplyオブジェクトを解放

    def fetchAndProcessReport(self, entry_data):
        """
        個別のレポートXMLを取得し、パースして保存します。
        """
        report_url = entry_data['url']
        request = QNetworkRequest(QUrl(report_url))

        # GETリクエストを送信し、返信が完了したらhandleReportReplyスロットを呼び出す
        reply = self.network_manager.get(request)
        # lambdaを使ってentry_dataをスロットに渡す
        reply.finished.connect(lambda: self.handleReportReply(reply, entry_data))

    @Slot(QNetworkReply, dict)
    def handleReportReply(self, reply: QNetworkReply, entry_data: dict):
        """
        個別のレポートXMLへのリクエストが完了したときに呼び出されるスロット。
        """
        try:
            if reply.error() != QNetworkReply.NoError:
                self.errorOccurred.emit(f"レポート取得時のネットワークエラー {entry_data['url']}: {reply.errorString()}")
                return

            report_xml_content = reply.readAll().data()

            # 取得したXMLコンテンツをzstdで圧縮して保存
            # ファイル名はエントリIDとタイムスタンプから生成し、特殊文字を置換して安全にする
            filename_base = entry_data['id'].replace('https://www.data.jma.go.jp/developer/xml/data/', '')
            output_filename = os.path.join(self.data_dir, f"{filename_base}.zst")
            with open(output_filename, 'wb') as f:
                f.write(zstd.compress(report_xml_content))

            print(f"圧縮データを保存しました: {output_filename}")
            # データが取得・保存されたことをメインアプリケーションに通知
            self.dataFetched.emit(output_filename)

            # レポートXMLの基本的なパース（XSD検証は行いません）
            report_root = ET.fromstring(report_xml_content)
            root_tag = report_root.tag
            ns_match = re.match(r'\{([^}]+)\}(.*)', root_tag)
            report_ns = ns_match.group(1) if ns_match else '' # ルート要素の名前空間

            # 例: レポートのタイトルとヘッドラインを抽出
            title_element = report_root.find(f"{{{report_ns}}}Head/{{{report_ns}}}Title")
            headline_element = report_root.find(f"{{{report_ns}}}Head/{{{report_ns}}}Headline/{{{report_ns}}}Text")

            report_title = title_element.text if title_element is not None else "タイトルなし"
            report_headline = headline_element.text if headline_element is not None else "ヘッドラインなし"

            print(f"レポートをパースしました: タイトル='{report_title}', ヘッドライン='{report_headline}'")

        except ET.ParseError as e:
            self.errorOccurred.emit(f"レポートXMLパースエラー {entry_data['url']}: {e}")
        except Exception as e:
            self.errorOccurred.emit(f"レポート処理中に予期せぬエラーが発生しました: {e}")
        finally:
            reply.deleteLater() # QNetworkReplyオブジェクトを解放