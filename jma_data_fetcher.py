import zstd
import os
import re
from PySide6.QtCore import QObject, QTimer, Signal, Slot, QDateTime, QUrl, QByteArray
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from lxml import etree
from lxml.etree import XMLSchema, XMLParser, parse, Resolver

# パーサーをインポート
from jma_parsers.VXSE53 import VXSE53
#from jma_parsers.jma_volcano_parser import VolcanoParser # 仮のパーサー

# カスタムResolverクラス (変更なし、ただしxsd_dirのパスが適切であることを確認)
class LocalXSDResolver(Resolver):
    def __init__(self, xsd_base_dir):
        super().__init__()
        self.xsd_base_dir = xsd_base_dir
        # JMAの共通名前空間URIとローカルXSDパスの明示的なマッピング
        self.uri_to_local_map = {
            "http://xml.kishou.go.jp/jmaxml1/": os.path.join("jmaxml1", "jmx.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/informationBasis1/": os.path.join("jmaxml1", "informationBasis1", "jma_ib.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/body/seismology1/": os.path.join("jmaxml1", "body", "seismology1", "jma_seis.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/body/seismology1/1.0": os.path.join("jmaxml1", "body", "seismology1", "jma_seis.xsd"), # バージョン付きURIの場合
            "http://xml.kishou.go.jp/jmaxml1/body/volcanology1/": os.path.join("jmaxml1", "body", "volcanology1", "jma_volc.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/body/meteorology1/": os.path.join("jmaxml1", "body", "meteorology1", "jma_mete.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/elementBasis1/": os.path.join("jmaxml1", "elementBasis1", "jma_eb.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/body/additional1/": os.path.join("jmaxml1", "body", "additional1", "jma_add.xsd"),
            # 他のスキーマもここに追加
        }
        print(f"LocalXSDResolver initialized with xsd_base_dir: {self.xsd_base_dir}")

    def resolve(self, url, public_id, context):
        # URLが直接XSDファイル名の場合 (xsi:schemaLocationから)
        if url.endswith(".xsd"):
            local_path = os.path.join(self.xsd_base_dir, os.path.basename(url))
            if os.path.exists(local_path):
                print(f"Resolved direct XSD filename to local file: {local_path}")
                return self.resolve_filename(local_path, context)

        # URLがJMAの名前空間URIで、ローカルXSDにマッピングされている場合
        for uri_prefix, relative_path in self.uri_to_local_map.items():
            if url.startswith(uri_prefix):
                local_path = os.path.join(self.xsd_base_dir, relative_path)
                if os.path.exists(local_path):
                    print(f"Resolved JMA URI '{url}' to local file: {local_path}")
                    return self.resolve_filename(local_path, context)
        
        # それ以外の場合はデフォルトのリゾルバーにフォールバック
        return super().resolve(url, public_id, context)


class JMADataFetcher(QObject):
    # 新しいデータが取得され、保存されたことを通知するシグナル
    # 引数として保存されたファイルのパスと、解析済みデータを渡します
    dataFetched = Signal(str, str, dict) # file_path, data_type, parsed_data
    errorOccurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.feed_url = "https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml"
        self.last_modified = None
        self.data_dir = "jmadata"
        self.xsd_dir = "jmaxml1" # XSDファイルが置かれているルートディレクトリ
        self.downloaded_ids = set()
        self.network_manager = QNetworkAccessManager(self)

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.xsd_dir, exist_ok=True) # XSDディレクトリも存在確認

        self.xsd_schemas = {} # ロードしたXSDスキーマをキャッシュする辞書

        # パーサーのインスタンスを辞書に登録
        self.parsers = {
            "VXSE53": VXSE53(self) # 地震情報
            #"VFVO53": VolcanoParser(self),    # 火山情報 (仮)
            # 他のデータタイプもここに追加
        }

        self._load_existing_ids()

        # 定期的に更新をチェックするためのタイマーを設定
        self.fetch_timer = QTimer(self)
        self.fetch_timer.timeout.connect(self._on_fetch_timer_triggered) # 新しいスロットに接続

        # 毎分20秒にタイマーをトリガーするための初期遅延を計算
        self._set_initial_fetch_timer()

        # アプリケーション起動時に一度更新をチェック
        self.checkForUpdates()

    def _load_existing_ids(self):
        print(f"既存のダウンロード済みデータをロード中... {self.data_dir}")
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".zst"):
                extracted_id_part = filename[:-4]
                full_id = f"https://www.data.jma.go.jp/developer/xml/data/{extracted_id_part}"
                self.downloaded_ids.add(full_id)
        print(f"ロード完了。ダウンロード済みID数: {len(self.downloaded_ids)}")

    def _set_initial_fetch_timer(self):
        current_time = QDateTime.currentDateTime()
        current_second = current_time.time().second()
        
        target_second = 20
        if current_second < target_second:
            delay_seconds = target_second - current_second
        else:
            delay_seconds = (60 - current_second) + target_second
        
        initial_delay_ms = delay_seconds * 1000
        
        print(f"現在の秒: {current_second}秒. 次の取得まで {initial_delay_ms}ms 待ちます。")
        self.fetch_timer.setSingleShot(True)
        self.fetch_timer.setInterval(initial_delay_ms)
        self.fetch_timer.start()

    @Slot()
    def _on_fetch_timer_triggered(self):
        if self.fetch_timer.isSingleShot():
            self.fetch_timer.setSingleShot(False)
            self.fetch_timer.setInterval(60 * 1000)
            self.fetch_timer.start()
            print("タイマー間隔を毎分に設定しました。")

        self.checkForUpdates()

    @Slot()
    def checkForUpdates(self):
        request = QNetworkRequest(QUrl(self.feed_url))
        if self.last_modified:
            request.setRawHeader(QByteArray(b"If-Modified-Since"), QByteArray(self.last_modified.encode('utf-8')))

        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.handleFeedReply(reply))

    @Slot(QNetworkReply)
    def handleFeedReply(self, reply: QNetworkReply):
        try:
            if reply.error() != QNetworkReply.NoError:
                self.errorOccurred.emit(f"フィード取得時のネットワークエラー {self.feed_url}: {reply.errorString()}")
                return

            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            if status_code == 304:
                print(f"フィードは更新されていません: {self.feed_url}")
                return

            last_modified_header = reply.rawHeader("Last-Modified").data().decode('utf-8')
            if last_modified_header:
                self.last_modified = last_modified_header
            else:
                self.last_modified = None

            feed_content = reply.readAll().data()
            feed_root = etree.fromstring(feed_content)
            ATOM_NS = "{http://www.w3.org/2005/Atom}"

            new_entries = []
            for entry in feed_root.findall(f"{ATOM_NS}entry"):
                entry_id = entry.find(f"{ATOM_NS}id").text
                # entry_updated = entry.find(f"{ATOM_NS}updated").text # 今回は未使用だが残しておく
                # entry_title = entry.find(f"{ATOM_NS}title").text # 今回は未使用だが残しておく
                # report_url = entry_id # 今回は未使用だが残しておく

                if entry_id in self.downloaded_ids:
                    print(f"ID '{entry_id}' のデータはすでにダウンロード済みです。スキップします。")
                    continue

                new_entries.append({'id': entry_id}) # 必要な情報だけを渡す

            if new_entries:
                print(f"新しいエントリが {len(new_entries)} 件見つかりました。")
                for entry_data in new_entries:
                    self.fetchAndProcessReport(entry_data)
            else:
                print("新しい未ダウンロードのエントリは見つかりませんでした。")

        except etree.ParseError as e:
            self.errorOccurred.emit(f"フィードXMLパースエラー {self.feed_url}: {e}")
        except Exception as e:
            self.errorOccurred.emit(f"フィード処理中に予期せぬエラーが発生しました: {e}")
        finally:
            reply.deleteLater()

    def _get_xsd_schema(self, xsd_filename):
        if xsd_filename in self.xsd_schemas:
            return self.xsd_schemas[xsd_filename]

        xsd_path = os.path.join(self.xsd_dir, xsd_filename)
        if not os.path.exists(xsd_path):
            self.errorOccurred.emit(f"XSDファイルが見つかりません: {xsd_path}")
            return None

        try:
            parser = etree.XMLParser(
                load_dtd=True,
                no_network=False,
                resolve_entities=True,
                attribute_defaults=True,
                dtd_validation=False,
                schema_validation=False
            )
            parser.resolvers.add(LocalXSDResolver(self.xsd_dir))

            schema_doc = etree.parse(xsd_path, parser=parser, base_url=f"file://{os.path.abspath(self.xsd_dir)}/")
            schema = etree.XMLSchema(schema_doc)
            self.xsd_schemas[xsd_filename] = schema
            print(f"XSDスキーマをロードしました: {xsd_filename}")
            return schema
        except etree.XMLSchemaParseError as e:
            self.errorOccurred.emit(f"XSDスキーマのパースエラー {xsd_filename}: {e}")
            return None
        except Exception as e:
            self.errorOccurred.emit(f"XSDスキーマのロード中に予期せぬエラーが発生しました: {e}")
            return None

    def fetchAndProcessReport(self, entry_data):
        report_url = entry_data['id']
        request = QNetworkRequest(QUrl(report_url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.handleReportReply(reply, entry_data))

    @Slot(QNetworkReply, dict)
    def handleReportReply(self, reply: QNetworkReply, entry_data: dict):
        try:
            if reply.error() != QNetworkReply.NoError:
                self.errorOccurred.emit(f"レポート取得時のネットワークエラー {entry_data['id']}: {reply.errorString()}")
                return

            report_xml_content = reply.readAll().data()

            parser = etree.XMLParser()
            parser.resolvers.add(LocalXSDResolver(self.xsd_dir))
            report_tree = etree.fromstring(report_xml_content, parser)

            # IDからデータタイプコードを抽出
            id_parts = entry_data['id'].split('/')
            filename_with_timestamp = id_parts[-1]
            data_type_code = filename_with_timestamp.split('_')[2]

            # ルート要素からxsi:schemaLocation属性を取得し、XSDファイル名を特定
            xsi_namespace = "{http://www.w3.org/2001/XMLSchema-instance}"
            schema_location_attr = report_tree.get(f"{xsi_namespace}schemaLocation")

            xsd_filename = None
            if schema_location_attr:
                parts = schema_location_attr.split()
                if len(parts) % 2 == 0:
                    xsd_filename = parts[-1] 
                    if not xsd_filename.endswith(".xsd"):
                        xsd_filename = None

            schema = None
            if xsd_filename:
                schema = self._get_xsd_schema(xsd_filename)
            else:
                print("xsi:schemaLocation属性からXSDファイル名を特定できませんでした。スキーマ検証なしでパースします。")

            # XSDスキーマ検証
            if schema:
                if not schema.validate(report_tree):
                    print(f"XMLスキーマ検証エラー: {entry_data['id']}")
                    for error in schema.error_log:
                        print(f"  - {error.message} (Line: {error.line}, Column: {error.column})")
                else:
                    print(f"XMLスキーマ検証成功: {entry_data['id']}")
            else:
                print("XSDスキーマがロードされていないため、スキーマ検証をスキップします。", end="\n\n")

            # 取得したXMLコンテンツをzstdで圧縮して保存
            # ここを修正: ファイル名をデータタイプコードではなく、元のIDの末尾部分を使用
            filename_base = entry_data['id'].replace('https://www.data.jma.go.jp/developer/xml/data/', '')
            output_filename = os.path.join(self.data_dir, f"{filename_base}.zst")
            
            with open(output_filename, 'wb') as f:
                f.write(zstd.compress(report_xml_content))

            print(f"圧縮データを保存しました: {output_filename}")
            self.downloaded_ids.add(entry_data['id'])

            # データタイプに基づいて適切なパーサーに処理を振り分け
            parsed_data = {}
            if data_type_code in self.parsers:
                parser_instance = self.parsers[data_type_code]
                # JMA XMLの共通名前空間をパーサーに渡す
                namespaces = {
                    'jmx': "http://xml.kishou.go.jp/jmaxml1/",
                    'jmx_ib': "http://xml.kishou.go.jp/jmaxml1/informationBasis1/",
                    'jmx_seis': "http://xml.kishou.go.jp/jmaxml1/body/seismology1/",
                    'jmx_volc': "http://xml.kishou.go.jp/jmaxml1/body/volcanology1/",
                    'jmx_mete': "http://xml.kishou.go.jp/jmaxml1/body/meteorology1/",
                    'jmx_add': "http://xml.kishou.go.jp/jmaxml1/body/additional1/",
                    'jmx_eb': "http://xml.kishou.go.jp/jmaxml1/elementBasis1/",
                    'xsi': "http://www.w3.org/2001/XMLSchema-instance" # xsi名前空間も必要
                }
                parsed_data = parser_instance.parse(report_tree, namespaces, data_type_code)
                print(f"パーサー ({data_type_code}) による解析結果: {parsed_data}")
            else:
                print(f"データタイプ '{data_type_code}' に対応するパーサーが見つかりません。")
                parsed_data = {"error": f"未対応のデータタイプ: {data_type_code}"}

            # 解析済みデータをメインアプリケーションに通知
            self.dataFetched.emit(output_filename, data_type_code, parsed_data)

        except etree.XMLSyntaxError as e:
            self.errorOccurred.emit(f"レポートXML構文エラー {entry_data['id']}: {e}")
        except Exception as e:
            self.errorOccurred.emit(f"レポート処理中に予期せぬエラーが発生しました: {e}")
        finally:
            reply.deleteLater()
