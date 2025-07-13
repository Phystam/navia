import zstd
import os
import re
from PySide6.QtCore import QObject, QTimer, Signal, Slot, QDateTime, QUrl, QByteArray
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from lxml import etree
from lxml.etree import XMLSchema, XMLParser, parse, Resolver

# パーサーをインポート
from jma_parsers.VPZJ50 import VPZJ50
from jma_parsers.VPOA50 import VPOA50
from jma_parsers.VGSK50 import VGSK50
from jma_parsers.VPWW54 import VPWW54
from jma_parsers.VXSE51 import VXSE51
from jma_parsers.VXSE53 import VXSE53
from jma_parsers.VFVO52 import VFVO52
from jma_parsers.VFVO53 import VFVO53
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
            "http://xml.kishou.go.jp/jmaxml1/body/seismology1/": os.path.join("jmaxml1", "body", "seismology1", "jma_seis.xsd"), # バージョン付きURIの場合
            "http://xml.kishou.go.jp/jmaxml1/body/volcanology1/": os.path.join("jmaxml1", "body", "volcanology1", "jma_volc.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/body/meteorology1/": os.path.join("jmaxml1", "body", "meteorology1", "jma_mete.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/elementBasis1/": os.path.join("jmaxml1", "elementBasis1", "jma_eb.xsd"),
            "http://xml.kishou.go.jp/jmaxml1/body/additional1/": os.path.join("jmaxml1", "body", "additional1", "jma_add.xsd"),
            # 他のスキーマもここに追加
        }
        #print(f"LocalXSDResolver initialized with xsd_base_dir: {self.xsd_base_dir}")

    def resolve(self, url, public_id, context):

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
    telopDataReceived = Signal(dict) # テロップ情報を受け取るためのシグナル
    def __init__(self, parent=None):
        super().__init__(parent)
        self.feed_urls = [
            "https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml",
            "https://www.data.jma.go.jp/developer/xml/feed/regular.xml",
            "https://www.data.jma.go.jp/developer/xml/feed/extra.xml"]
        self.last_modifieds = [None, None, None]
        self.data_dir = "jmadata"
        self.xsd_dir = "xsdschema" # XSDファイルが置かれているルートディレクトリ
        self.downloaded_ids = set()
        self.network_manager = QNetworkAccessManager(self)

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.xsd_dir, exist_ok=True) # XSDディレクトリも存在確認

        self.xsd_schemas = {} # ロードしたXSDスキーマをキャッシュする辞書

        # パーサーのインスタンスを辞書に登録
        self.parsers = {
            "VGSK50": VGSK50(self), # 季節観測
            "VGSK55": VGSK50(self), # 季節観測
            "VGSK60": VGSK50(self), # 季節観測
            "VPZJ50": VPZJ50(self), # 全般気象情報 一般報
            "VPZJ51": VPZJ50(self), # 全般気象解説情報 一般報
            "VPCJ50": VPZJ50(self), # 地方気象情報 一般報
            "VPCJ51": VPZJ50(self), # 地方気象解説情報 一般報
            "VPFJ50": VPZJ50(self), # 府県気象情報 一般報
            "VPFJ51": VPZJ50(self), # 府県気象解説情報 一般報
            "VPTI50": VPZJ50(self), # 全般台風情報報（総合情報、上陸等情報），発達する熱帯低気圧に関する情報 一般報
            "VPTI51": VPZJ50(self), # 全般台風情報 （位置、発生情報），発達する熱帯低気圧に関する情報 一般報
            "VPTI52": VPZJ50(self), # 全般台風情報 （位置詳細）一般報
            "VPFG50": VPZJ50(self), # 府県天気概況
            "VMCJ50": VPZJ50(self), # 全般潮位情報 一般報
            "VMCJ51": VPZJ50(self), # 地方潮位情報 一般報
            "VMCJ52": VPZJ50(self), # 府県潮位情報 一般報
            "VPOA50": VPOA50(self), # 記録的短時間大雨情報
            
            "VPWW54": VPWW54(self), # 気象警報
            "VXSE51": VXSE51(self), # 震度速報
            "VXSE53": VXSE53(self), # 震源・震度情報
            "VFVO52": VFVO52(self), # 噴火に関する火山観測報
            "VFVO53": VFVO53(self), # 降灰予報 (定時) (仮)
            "VFVO54": VFVO53(self), # 降灰予報 (速報) 
            "VFVO55": VFVO53(self), # 降灰予報 (詳細)
            #"VFVO53": VolcanoParser(self),    # 火山情報 (仮)
            # 他のデータタイプもここに追加
        }

        self._load_existing_ids(first=True)

        # 定期的に更新をチェックするためのタイマーを設定
        self.fetch_timers = [QTimer(self), QTimer(self), QTimer(self)]
        for j, fetch_timer in enumerate(self.fetch_timers):
            fetch_timer.timeout.connect(lambda i=j: self._on_fetch_timer_triggered(i)) # 新しいスロットに接続

        # 毎分20秒にタイマーをトリガーするための初期遅延を計算
        for i in range(len(self.feed_urls)):
            self._set_initial_fetch_timer(i)

        # アプリケーション起動時に一度更新をチェック
            self.checkForUpdates(i)

    def _load_existing_ids(self, first=False):
        #print(f"既存のダウンロード済みデータをロード中... {self.data_dir}")
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".zst"):
                extracted_id_part = filename[:-4]
                with open(os.path.join(self.data_dir, filename), 'rb') as f:
                    try:
                        filedata=zstd.decompress(f.read())  # Zstandard圧縮を解凍
                    except:
                        print(f"Zstandard解凍エラー")
                        continue
                    self.processReport({'id': extracted_id_part}, filedata,test=False, playtelop=not first) 
                full_id = f"https://www.data.jma.go.jp/developer/xml/data/{extracted_id_part}"
                self.downloaded_ids.add(full_id)
        print(f"ロード完了。ダウンロード済みID数: {len(self.downloaded_ids)}")

    def _set_initial_fetch_timer(self,i):
        current_time = QDateTime.currentDateTime()
        current_second = current_time.time().second()
        
        target_second = 20+i
        if current_second < target_second:
            delay_seconds = target_second - current_second
        else:
            delay_seconds = (60 - current_second) + target_second
        
        initial_delay_ms = delay_seconds * 1000
        
        print(f"現在の秒: {current_second}秒. 次の取得まで {initial_delay_ms}ms 待ちます。")
        self.fetch_timers[i].setSingleShot(True)
        self.fetch_timers[i].setInterval(initial_delay_ms)
        self.fetch_timers[i].start()

    @Slot()
    def _on_fetch_timer_triggered(self, i):
        if self.fetch_timers[i].isSingleShot():
            self.fetch_timers[i].setSingleShot(False)
            self.fetch_timers[i].setInterval(60 * 1000)
            self.fetch_timers[i].start()
            print("タイマー間隔を毎分に設定しました。")

        self.checkForUpdates(i)

    @Slot()
    def checkForUpdates(self, i):
        request = QNetworkRequest(QUrl(self.feed_urls[i]))
        if self.last_modifieds[i]:
            request.setRawHeader(QByteArray(b"If-Modified-Since"), QByteArray(self.last_modifieds[i].encode('utf-8')))

        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.handleFeedReply(i,reply))

    @Slot(QNetworkReply)
    def handleFeedReply(self, i, reply: QNetworkReply):
        try:
            if reply.error() != QNetworkReply.NoError:
                self.errorOccurred.emit(f"フィード取得時のネットワークエラー {self.feed_urls[i]}: {reply.errorString()}")
                return

            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            if status_code == 304:
                print(f"フィードは更新されていません: {self.feed_urls[i]}")
                return

            last_modified_header = reply.rawHeader("Last-Modified").data().decode('utf-8')
            if last_modified_header:
                self.last_modifieds[i] = last_modified_header
            else:
                self.last_modifieds[i] = None

            feed_content = reply.readAll().data()
            feed_root = etree.fromstring(feed_content)
            ATOM_NS = "{http://www.w3.org/2005/Atom}"

            new_entries = []
            for entry in feed_root.findall(f"{ATOM_NS}entry"):
                entry_id = entry.find(f"{ATOM_NS}id").text

                if entry_id in self.downloaded_ids:
                    #print(f"ID '{entry_id}' のデータはすでにダウンロード済みです。スキップします。")
                    continue

                new_entries.append({'id': entry_id}) # 必要な情報だけを渡す

            if new_entries:
                print(f"新しいエントリが {len(new_entries)} 件見つかりました。")
                for entry_data in new_entries:
                    self.fetchAndProcessReport(entry_data)
            else:
                print("新しい未ダウンロードのエントリは見つかりませんでした。")

        except etree.ParseError as e:
            self.errorOccurred.emit(f"フィードXMLパースエラー {self.feed_urls[i]}: {e}")
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
                dtd_validation=False
                #schema_validation=False
            )
            parser.resolvers.add(LocalXSDResolver(self.xsd_dir))

            schema_doc = etree.parse(xsd_path, parser=parser, base_url=f"file://{os.path.abspath(self.xsd_dir)}/")
            schema = etree.XMLSchema(schema_doc)
            self.xsd_schemas[xsd_filename] = schema
            #print(f"XSDスキーマをロードしました: {xsd_filename}")
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
            self.processReport(entry_data, report_xml_content, test=False, playtelop=True)
        except etree.XMLSyntaxError as e:
            self.errorOccurred.emit(f"レポートXML構文エラー {entry_data['id']}: {e}")
        except Exception as e:
            self.errorOccurred.emit(f"レポート処理中に予期せぬエラーが発生しました: {e}")
        finally:
            reply.deleteLater()

    def processReport(self, entry_data, report_xml_content, test=False, playtelop=False):
        parser = etree.XMLParser()
        parser.resolvers.add(LocalXSDResolver(self.xsd_dir))
        report_tree = etree.fromstring(report_xml_content, parser)
        # IDからデータタイプコードを抽出
        if test:
            data_type_code=entry_data
        else:
            id_parts = entry_data['id'].split('/')
            filename_with_timestamp = id_parts[-1]
            data_type_code = filename_with_timestamp.split('_')[2]

        # ルート要素からxmlns属性を取得し、XSDファイル名を特定
        #print(f"ルート要素: {report_tree.text}, 属性: {report_tree.attrib}")
        #schema_location_attr = report_tree.get('xmlns')
        #print(f"取得したXMLのルート要素: {report_tree}, xmlns属性: {report_tree.attrib}")
        #xsd_filename = None
        #if schema_location_attr:
        #    parts = schema_location_attr.split()
        #    if len(parts) % 2 == 0:
        #        xsd_filename = parts[-1] 
        #        if not xsd_filename.endswith(".xsd"):
        #            xsd_filename = None
        #xsd_filename = "http://xml.kishou.go.jp/jmaxml1/"
        xsd_filename="jmx.xsd"
        schema = None
        if xsd_filename:
            schema = self._get_xsd_schema(xsd_filename)
        else:
            pass #print("xsi:schemaLocation属性からXSDファイル名を特定できませんでした。スキーマ検証なしでパースします。")

        # XSDスキーマ検証
        if schema:
            if not schema.validate(report_tree):
                #print(f"XMLスキーマ検証エラー: {entry_data['id']}")
                for error in schema.error_log:
                    pass
                    print(f"  - {error.message} (Line: {error.line}, Column: {error.column})")
            else:
                pass
                #print(f"XMLスキーマ検証成功: {entry_data['id']}")
        else:
            pass #print("XSDスキーマがロードされていないため、スキーマ検証をスキップします。", end="\n\n")

        # 取得したXMLコンテンツをzstdで圧縮して保存
        # ここを修正: ファイル名をデータタイプコードではなく、元のIDの末尾部分を使用
        if not test:
            filename_base = entry_data['id'].replace('https://www.data.jma.go.jp/developer/xml/data/', '')
            output_filename = os.path.join(self.data_dir, f"{filename_base}.zst")
        
            if playtelop:
                with open(output_filename, 'wb') as f:
                    f.write(zstd.compress(report_xml_content))
    
                print(f"圧縮データを保存しました: {output_filename}")
                self.downloaded_ids.add(entry_data['id'])

        # データタイプに基づいて適切なパーサーに処理を振り分け
        parsed_data = {}
        telop_dict = {}
        if data_type_code in self.parsers:
            parser_instance = self.parsers[data_type_code]
            # JMA XMLの共通名前空間をパーサーに渡す
            namespaces = {
                'jmx': "http://xml.kishou.go.jp/jmaxml1/",
                'jmx_ib': "http://xml.kishou.go.jp/jmaxml1/informationBasis1/",
                'jmx_seis': "http://xml.kishou.go.jp/jmaxml1/body/seismology1/",
                'jmx_volc': "http://xml.kishou.go.jp/jmaxml1/body/volcanology1/",
                'jmx_mete': "http://xml.kishou.go.jp/jmaxml1/body/meteorology1/",
                'jmx_add': "http://xml.kishou.go.jp/jmaxml1/addition1/",
                'jmx_eb': "http://xml.kishou.go.jp/jmaxml1/elementBasis1/",
                'xsi': "http://www.w3.org/2001/XMLSchema" # xsi名前空間も必要
            }
            #parsed_data = parser_instance.parse(report_tree, namespaces, data_type_code)
            # 解析済みデータをメインアプリケーションに通知
            #self.dataFetched.emit(output_filename, data_type_code, parsed_data)
            telop_dict = parser_instance.content(report_tree, namespaces, data_type_code)
            #print(f"テロップ情報: {telop_dict}")
            if playtelop:
                #telop_dict = parser_instance.content(report_tree, namespaces, data_type_code)
                
                self.telopDataReceived.emit(telop_dict)
        else:
            pass
            #print(f"データタイプ '{data_type_code}' に対応するパーサーが見つかりません。")
            #parsed_data = {"error": f"未対応のデータタイプ: {data_type_code}"}

        

        
