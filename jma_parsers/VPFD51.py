from .jma_base_parser import BaseJMAParser

class VPFD51(BaseJMAParser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_type = "VPZJ50" # このパーサーが扱うデータタイプ
        self.area=["",]

    def parse(self, xml_tree, namespaces, data_type_code, test=False):
        """
        府県天気予報 (VPFD51) のXMLを解析します。
        """
        print(f"府県天気予報 ({self.data_type}) を解析中...")
        parsed_data = {}
        parsed_data['category']="meteorology"
        parsed_data["data_type"]=data_type_code
        # Control/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        parsed_data['report_datetime'] = self._get_datetime(xml_tree, '//jmx_ib:ReportDateTime/text()', namespaces)
        parsed_data['area'] = "全般"
        

        hier="pref"
        #地域名→コードの対応を作る
        parsed_data["hier"]=hier
        if data_type_code == "VPFG50":
            parsed_data["areacode"] = self._get_text(xml_tree, '//jmx_mete:TargetArea[@codeType="気象情報／府県予報区・細分区域等"]/jmx_mete:Code/text()', namespaces)
            print(f'hehe{parsed_data["areacode"]}')
        parsed_data['publishing_office'] = self._get_text(xml_tree, '//jmx:PublishingOffice/text()', namespaces)
        # Head/Title
        parsed_data['head_title'] = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        # Head/Headline/Text
        parsed_data['headline_text'] = self._get_text(xml_tree, '//jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        # Body/Comment/Text
        parsed_data['body_text'] = self._get_text(xml_tree,'//jmx_mete:Comment/jmx_mete:Text[@type="本文"]/text()', namespaces)
        # body_textは改行などで整形されている。
        return parsed_data
    
    def content(self, xml_tree, namespaces, data_type):
        """
        XMLツリーと名前空間を受け取り、地震情報の内容を解析して辞書として返します。
        telop_dict: テロップ情報の辞書, logoとtextのペアをリストとして持つ。
        """
        logo_list = []
        text_list = []
        sound_list = []
        publishing_office = self._get_text(xml_tree, '//jmx:PublishingOffice/text()', namespaces)
        title = self._get_text(xml_tree, '//jmx_ib:Title/text()', namespaces)
        if data_type=="VPFG50": #天気概況
            targetarea=self._get_text(xml_tree, '//jmx_mete:TargetArea/jmx_mete:Name/text()', namespaces)
        else:
            targetarea=""
        notify_level=0
        headline = self._get_text(xml_tree, '//jmx_ib:Headline/jmx_ib:Text/text()', namespaces)
        
        logo_list.append(["", ""])
        text_list.append([f"<b>{publishing_office}発表 {targetarea}{title}</b>",""])  
        sound_list.append("")
                # headlineを句点で分割
        headline=headline.replace("\n","")
        tlist=headline.split("。")
        # 最後。で終わるので、最後尾の要素を削除する
        tlist=tlist[:-1]
        # 要素数が奇数の場合、空文字を追加して偶数にする
        if len(tlist) %2 != 0:
            tlist.append("")
        for i in range(len(tlist)):
            # 消された句点を復元
            if tlist[i] !="":
                tlist[i] = f"{tlist[i]}。"
            # 奇数番目のとき、2行分のリストを追加
            if i % 2 == 1:
                sound_list.append("")
                logo_list.append(["", ""])
                text_list.append(tlist[i-1:i+1])
        
        
        telop_dict = {
            'logo_list': logo_list,
            'text_list': text_list,
            'sound_list': sound_list
        }
        return telop_dict, {publishing_office: notify_level}
