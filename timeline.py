# timeline.py
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot

class TimelineManager(QObject):
    def __init__(self,parent=None):
        super().__init__(self)
        """タイムラインデータを管理するクラス"""
        self.timeline = []  # タイムラインデータを格納するリスト
        
    def add_entry(self, data):
        """
        パースされたデータをタイムラインに追加
        
        Args:
            data: パース結果の辞書（jma_base_parserの出力形式）
        """
        entry = {
            'data_type': data["data_type"],
            'timestamp': datetime.fromisoformat(data['datetime']),  # ISOフォーマットの日時
            'valid_to': datetime.fromisoformat(data['valid_datetime']),
            'title': data['title'],
            'publishing_office': data['publishing_office'],
            'area': data.get('area', '未指定'),
            'headline': data.get('headline_text', ''),
            'content': self._format_content(data),
            'source_type': data.get('data_type', 'unknown'),
            'raw_data': data  # 元データの保持（詳細分析用）
        }
        self.timeline.append(entry)
        self.timeline.sort(key=lambda x: x['timestamp'])  # 日時順にソート
        
    def _format_content(self, data):
        """コンテンツの整形（ヘッドライン＋本文の統合）"""
        return f"{data.get('headline_text', '')}\n\n{data.get('body_text', '')}"
    
    def get_all_entries(self):
        """すべてのタイムラインエントリを取得"""
        return self.timeline
    
    def find_by_area(self, area):
        """指定されたエリアのエントリをフィルタリング"""
        return [entry for entry in self.timeline if entry['area'] == area]
    
    def find_by_date(self, date):
        """指定された日付のエントリをフィルタリング"""
        target_date = datetime(date.year, date.month, date.day)
        return [entry for entry in self.timeline 
                if entry['timestamp'].date() == target_date.date()]

# サンプルデータ構造（テスト用）
sample_entry = {
    'title': '地震情報',
    'datetime': '2025-07-25T10:00:00',
    'publishing_office': '気象庁',
    'area': '関東地方',
    'headline_text': '最大級の警戒',
    'body_text': '東京湾を震源とする地震が発生しました。',
    'data_type': 'VPZJ50'
}