# jma_parsers/jma_base_parser.py
from PySide6.QtCore import QObject, Signal

class BaseJMAParser(QObject):
    # 解析されたデータを通知するシグナル (データタイプと解析済みデータ)
    parsedData = Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)

    def parse(self, xml_tree, namespaces, data_type_code):
        """
        XMLツリーと名前空間を受け取り、データを解析して辞書として返します。
        このメソッドは子クラスでオーバーライドされるべきです。
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _get_text(self, element, xpath, namespaces, default="N/A"):
        """XPathで要素のテキストを取得するヘルパー関数"""
        result = element.xpath(xpath, namespaces=namespaces)
        return result[0] if result else default

    def _get_attribute(self, element, xpath, namespaces, default="N/A"):
        """XPathで要素の属性を取得するヘルパー関数"""
        result = element.xpath(xpath, namespaces=namespaces)
        return result[0] if result else default