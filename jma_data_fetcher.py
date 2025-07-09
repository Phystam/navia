import zstd
import os
import re
from PySide6.QtCore import QObject, QTimer, Signal, Slot, QDateTime, QUrl, QByteArray
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from lxml import etree # lxmlをインポート
from lxml.etree import XMLSchema, XMLParser, parse, Resolver # Resolverをインポート

# カスタムResolverクラス
class LocalXSDResolver(Resolver):
    def __init__(self, xsd_dir):
        super().__init__()
        self.xsd_dir = xsd_dir
        print(f"LocalXSDResolver initialized with xsd_dir: {self.xsd_dir}")

    def resolve(self, url, public_id, context):
        """
        スキーマロケーションのURLをローカルファイルパスに解決します。
        JMAのスキーマロケーションの例:
        "http://xml.kishou.go.jp/jmaxml1/body/seismology1/1.0 Vxse50_10_00_Earthquake.xsd"
        この場合、urlは "http://xml.kishou.go.jp/jmaxml1/body/seismology1/1.0"
        または "Vxse50_10_00_Earthquake.xsd" になります。
        """
        print(f"Resolving URL: {url}, Public ID: {public_id}")

        # URLがファイル名（.xsdで終わる）の場合、ローカルのxsd_dirから探す
        if url.endswith(".xsd"):
            local_path = os.path.join(self.xsd_dir, os.path.basename(url))
            if os.path.exists(local_path):
                print(f"Resolved to local file: {local_path}")
                return self.resolve_filename(local_path, context)
        
        # JMAのXML名前空間URIをローカルのjmx.xsdにマッピングする例
        # ただし、JMAのXMLはschemaLocationで直接ファイル名を指定することが多いため、
        # この部分は主にスキーマが外部URIをインポートしている場合に役立つ
        if "http://xml.kishou.go.jp/jmaxml1/" in url:
            # ここでは一般的なjmx.xsdにマッピングするが、
            # 実際にはURIとXSDファイルの対応関係を正確に把握する必要がある
            # 例: jmaxml1/jmx.xsd
            # informationBasis1/jma_ib.xsd
            # body/seismology1/jma_seis.xsd
            # body/meteorology1/jma_mete.xsd
            
            # URLから対応するローカルXSDパスを推測するロジックを実装
            # 例: http://xml.kishou.go.jp/jmaxml1/body/seismology1/1.0 -> xsd/jmaxml1/body/seismology1/jma_seis.xsd
            # JMAのXSDの構造に合わせて調整が必要
            
            # 簡単な例として、URLの最後の部分からファイル名を推測
            # ただし、これは非常に単純なマッピングであり、すべてのJMA XSDに適用できるわけではない
            # 正しいマッピングは、JMAのスキーマ構造を理解して実装する必要がある
            
            # 例: http://xml.kishou.go.jp/jmaxml1/ -> jmaxml1/jmx.xsd
            # http://xml.kishou.go.jp/jmaxml1/informationBasis1/ -> jmaxml1/informationBasis1/jma_ib.xsd
            # http://xml.kishou.go.jp/jmaxml1/body/seismology1/ -> jmaxml1/body/seismology1/jma_seis.xsd
            
            # URLをファイルパスに変換するロジック
            relative_path = url.replace("http://xml.kishou.go.jp/", "")
            if relative_path.endswith("/"):
                relative_path = relative_path[:-1] # 末尾のスラッシュを削除
            
            # JMAのXSDファイル名がURIの最後のセグメントに 'jmx.xsd', 'jma_ib.xsd' などのパターンで対応している場合
            # ここでは仮に 'jmx.xsd' にマッピングするが、これは正確ではない可能性がある
            if "jmaxml1" in relative_path and "informationBasis1" not in relative_path and "body" not in relative_path:
                local_path = os.path.join(self.xsd_dir, "jmaxml1", "jmx.xsd")
            elif "informationBasis1" in relative_path:
                local_path = os.path.join(self.xsd_dir, "jmaxml1", "informationBasis1", "jma_ib.xsd")
            elif "body/seismology1" in relative_path:
                local_path = os.path.join(self.xsd_dir, "jmaxml1", "body", "seismology1", "jma_seis.xsd")
            # 他のスキーマパスも同様に追加
            else:
                local_path = None # マッピングできない場合

            if local_path and os.path.exists(local_path):
                print(f"Resolved JMA URI to local file: {local_path}")
                return self.resolve_filename(local_path, context)

        # デフォルトの解決方法にフォールバック
        return super().resolve(url, public_id, context)


class JMADataFetcher(QObject):
    dataFetched = Signal(str)
    errorOccurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.feed_url = "https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml"
        self.last_modified = None
        self.data_dir = "jmadata"
        self.xsd_dir = "jmaxml1" # XSDファイルが置かれているディレクトリ
        self.downloaded_ids = set()
        self.network_manager = QNetworkAccessManager(self)

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.xsd_dir, exist_ok=True) # XSDディレクトリも存在確認

        self.xsd_schemas = {} # ロードしたXSDスキーマをキャッシュする辞書

        self._load_existing_ids()

        # 定期的に更新をチェックするためのタイマーを設定
        self.fetch_timer = QTimer(self)
        self.fetch_timer.timeout.connect(self._on_fetch_timer_triggered) # 新しいスロットに接続

        # 毎分20秒にタイマーをトリガーするための初期遅延を計算
        self._set_initial_fetch_timer()

        # アプリケーション起動時に一度更新をチェック
        self.checkForUpdates()

    def _load_existing_ids(self):
        """
        'jmadata'ディレクトリ内の既存のファイルから、ダウンロード済みのデータIDをロードします。
        """
        print(f"既存のダウンロード済みデータをロード中... {self.data_dir}")
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".zst"):
                extracted_id_part = filename[:-4] # '.zst' を削除
                full_id = f"https://www.data.jma.go.jp/developer/xml/data/{extracted_id_part}"
                self.downloaded_ids.add(full_id)
        print(f"ロード完了。ダウンロード済みID数: {len(self.downloaded_ids)}")

    def _set_initial_fetch_timer(self):
        """
        毎分20秒にタイマーがトリガーされるように初期遅延を設定します。
        """
        current_time = QDateTime.currentDateTime()
        current_second = current_time.time().second()
        
        target_second = 20 # 毎分20秒に取得したい

        if current_second < target_second:
            delay_seconds = target_second - current_second
        else:
            delay_seconds = (60 - current_second) + target_second
        
        initial_delay_ms = delay_seconds * 1000
        
        print(f"現在の秒: {current_second}秒. 次の取得まで {delay_seconds}秒 ({initial_delay_ms}ms) 待ちます。")
        self.fetch_timer.setSingleShot(True)
        self.fetch_timer.setInterval(initial_delay_ms)
        self.fetch_timer.start()

    @Slot()
    def _on_fetch_timer_triggered(self):
        """
        タイマーがトリガーされたときに呼び出されるスロット。
        初回実行後、タイマーを毎分実行に設定し直します。
        """
        if self.fetch_timer.isSingleShot():
            self.fetch_timer.setSingleShot(False)
            self.fetch_timer.setInterval(60 * 1000) # 60秒（1分）ごとにタイムアウト
            self.fetch_timer.start()
            print("タイマー間隔を毎分に設定しました。")

        self.checkForUpdates()

    @Slot()
    def checkForUpdates(self):
        """
        Atomフィードにアクセスし、更新があるかチェックします。
        更新があれば、新しいエントリのXMLデータを取得・処理します。
        """
        request = QNetworkRequest(QUrl(self.feed_url))
        if self.last_modified:
            request.setRawHeader(QByteArray(b"If-Modified-Since"), QByteArray(self.last_modified.encode('utf-8')))

        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.handleFeedReply(reply))

    @Slot(QNetworkReply)
    def handleFeedReply(self, reply: QNetworkReply):
        """
        Atomフィードへのリクエストが完了したときに呼び出されるスロット。
        """
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
            feed_root = etree.fromstring(feed_content) # lxmlでパース
            ATOM_NS = "{http://www.w3.org/2005/Atom}"

            new_entries = []
            for entry in feed_root.findall(f"{ATOM_NS}entry"):
                entry_id = entry.find(f"{ATOM_NS}id").text
                entry_updated = entry.find(f"{ATOM_NS}updated").text
                entry_title = entry.find(f"{ATOM_NS}title").text
                report_url = entry_id

                if entry_id in self.downloaded_ids:
                    print(f"ID '{entry_id}' のデータはすでにダウンロード済みです。スキップします。")
                    continue

                new_entries.append({'id': entry_id, 'updated': entry_updated, 'title': entry_title, 'url': report_url})

            if new_entries:
                print(f"新しいエントリが {len(new_entries)} 件見つかりました。")
                for entry_data in new_entries:
                    self.fetchAndProcessReport(entry_data)
            else:
                print("新しい未ダウンロードのエントリは見つかりませんでした。")

        except etree.ParseError as e: # lxmlのパースエラーを捕捉
            self.errorOccurred.emit(f"フィードXMLパースエラー {self.feed_url}: {e}")
        except Exception as e:
            self.errorOccurred.emit(f"フィード処理中に予期せぬエラーが発生しました: {e}")
        finally:
            reply.deleteLater()

    def _get_xsd_schema(self, xsd_filename):
        """
        指定されたXSDファイルをロードし、キャッシュします。
        """
        if xsd_filename in self.xsd_schemas:
            return self.xsd_schemas[xsd_filename]

        xsd_path = os.path.join(self.xsd_dir, xsd_filename)
        if not os.path.exists(xsd_path):
            self.errorOccurred.emit(f"XSDファイルが見つかりません: {xsd_path}")
            return None

        try:
            # カスタムResolverを設定
            parser = etree.XMLParser(
                load_dtd=True,
                no_network=False, # ネットワークアクセスを許可（参照先のXSDが外部にある場合）
                resolve_entities=True,
                attribute_defaults=True,
                dtd_validation=False,
                schema_validation=False
            )
            parser.resolvers.add(LocalXSDResolver(self.xsd_dir)) # カスタムResolverを追加

            # etree.parse()にbase_urlを指定することで、相対パスのXSD参照を解決できる
            # ただし、Resolverが優先される
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
        """
        個別のレポートXMLを取得し、パースして保存します。
        """
        report_url = entry_data['url']
        request = QNetworkRequest(QUrl(report_url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.handleReportReply(reply, entry_data))

    @Slot(QNetworkReply, dict)
    def handleReportReply(self, reply: QNetworkReply, entry_data: dict):
        """
        個別のレポートXMLへのリクエストが完了したときに呼び出されるスロット。
        lxmlとXSDを使ってパース・検証を行います。
        """
        try:
            if reply.error() != QNetworkReply.NoError:
                self.errorOccurred.emit(f"レポート取得時のネットワークエラー {entry_data['url']}: {reply.errorString()}")
                return

            report_xml_content = reply.readAll().data()

            # カスタムResolverを設定したXMLParserを使用
            parser = etree.XMLParser()
            parser.resolvers.add(LocalXSDResolver(self.xsd_dir)) # カスタムResolverを追加
            report_tree = etree.fromstring(report_xml_content, parser) # lxmlでパース

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
                    print(f"XMLスキーマ検証エラー: {entry_data['url']}")
                    for error in schema.error_log:
                        print(f"  - {error.message} (Line: {error.line}, Column: {error.column})")
                    # エラーがあっても処理は続行（必要に応じて中断）
                else:
                    print(f"XMLスキーマ検証成功: {entry_data['url']}")
            else:
                print("XSDスキーマがロードされていないため、スキーマ検証をスキップします。")

            # 取得したXMLコンテンツをzstdで圧縮して保存
            filename_base = entry_data['id'].replace('https://www.data.jma.go.jp/developer/xml/data/', '')
            output_filename = os.path.join(self.data_dir, f"{filename_base}.zst")
            
            with open(output_filename, 'wb') as f:
                f.write(zstd.compress(report_xml_content))

            print(f"圧縮データを保存しました: {output_filename}")
            self.dataFetched.emit(output_filename)
            self.downloaded_ids.add(entry_data['id'])

            # データ抽出 (XPathを使用)
            # JMAのXML構造は多様なため、一般的なパスを試みます。
            # 実際のレポートタイプに応じてXPathを調整する必要があります。
            
            # 名前空間を辞書で定義 (JMA XMLの共通名前空間)
            # JMAのXMLは、ルート要素のxmlnsと、Head/Bodyなどの子要素のxmlnsで異なるURIを使用することが多い
            # そのため、XPathで要素を検索する際には、その要素が属する名前空間を正確に指定する必要がある
            # uploaded:20250708162708_0_VXSE53_270000.xml の例から名前空間を定義
            namespaces = {
                'jmx': "http://xml.kishou.go.jp/jmaxml1/", # ルートのxmlns
                'jmx_ib': "http://xml.kishou.go.jp/jmaxml1/informationBasis1/", # Headのxmlns
                'jmx_seis': "http://xml.kishou.go.jp/jmaxml1/body/seismology1/", # Bodyのxmlns
                'jmx_seis': "http://xml.kishou.go.jp/jmaxml1/body/volcanology1/",
                'jmx_mete': "http://xml.kishou.go.jp/jmaxml1/body/meteorology1/", # Bodyのxmlns
                'jmx_add': "http://xml.kishou.go.jp/jmaxml1/body/additional1/", # Bodyの追加情報用
                'jmx_eb': "http://xml.kishou.go.jp/jmaxml1/elementBasis1/", # jmx_eb:Coordinate など
                'xsi': "http://www.w3.org/2001/XMLSchema"
            }

            # 例: 震源・震度情報 (VXSE53) の場合
            # Control/Title
            control_title = report_tree.xpath('/jmx:Report/jmx:Control/jmx:Title/text()', namespaces=namespaces)
            # Head/Title
            head_title = report_tree.xpath('/jmx:Report/jmx_ib:Head/jmx_ib:Title/text()', namespaces=namespaces)
            # Head/Headline/Text
            headline_text = report_tree.xpath('/jmx:Report/jmx_ib:Head/jmx_ib:Headline/jmx_ib:Text/text()', namespaces=namespaces)
            # Body/Earthquake/Hypocenter/Area/Name (震央地名)
            hypocenter_name = report_tree.xpath('/jmx:Report/jmx_seis:Body/jmx_seis:Earthquake/jmx_seis:Hypocenter/jmx_seis:Area/jmx_seis:Name/text()', namespaces=namespaces)
            # Body/Earthquake/Magnitude/@description (マグニチュードの説明)
            magnitude_description = report_tree.xpath('/jmx:Report/jmx_seis:Body/jmx_seis:Earthquake/jmx_eb:Magnitude/@description', namespaces=namespaces)
            # Body/Earthquake/Magnitude/Value (マグニチュードの値)
            magnitude_value = report_tree.xpath('/jmx:Report/jmx_seis:Body/jmx_seis:Earthquake/jmx_eb:Magnitude/text()', namespaces=namespaces)
            # Body/Intensity/Observation/MaxInt (最大震度)
            max_intensity = report_tree.xpath('/jmx:Report/jmx_seis:Body/jmx_seis:Intensity/jmx_seis:Observation/jmx_seis:MaxInt/text()', namespaces=namespaces)
            # Body/Comments/ForecastComment/Text (津波の心配など)
            forecast_comment = report_tree.xpath('/jmx:Report/jmx_seis:Body/jmx_seis:Comments/jmx_seis:ForecastComment/jmx_seis:Text/text()', namespaces=namespaces)


            parsed_control_title = control_title[0] if control_title else "Control Titleなし"
            parsed_head_title = head_title[0] if head_title else "Head Titleなし"
            parsed_headline_text = headline_text[0] if headline_text else "Headline Textなし"
            parsed_hypocenter_name = hypocenter_name[0] if hypocenter_name else "震央地名なし"
            parsed_magnitude_description = magnitude_description[0] if magnitude_description else "マグニチュード説明なし"
            parsed_magnitude_value = magnitude_value[0] if magnitude_value else "マグニチュード値なし"
            parsed_max_intensity = max_intensity[0] if max_intensity else "最大震度なし"
            parsed_forecast_comment = forecast_comment[0] if forecast_comment else "予報コメントなし"


            print(f"--- レポート詳細 ({entry_data['id']}) ---")
            print(f"Control Title: {parsed_control_title}")
            print(f"Head Title: {parsed_head_title}")
            print(f"Headline: {parsed_headline_text}")
            print(f"震央地名: {parsed_hypocenter_name}")
            print(f"マグニチュード: {parsed_magnitude_description} ({parsed_magnitude_value})")
            print(f"最大震度: {parsed_max_intensity}")
            print(f"予報コメント: {parsed_forecast_comment}")
            print(f"------------------------------------")

        except etree.XMLSyntaxError as e: # lxmlの構文エラーを捕捉
            self.errorOccurred.emit(f"レポートXML構文エラー {entry_data['url']}: {e}")
        except Exception as e:
            self.errorOccurred.emit(f"レポート処理中に予期せぬエラーが発生しました: {e}")
        finally:
            reply.deleteLater()
