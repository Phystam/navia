from PySide6.QtWebSockets import QWebSocket
from PySide6.QtCore import QThread, QMutex, QObject, Qt, Signal, Slot, QUrl, QByteArray, QTimerEvent, QFile, QIODevice, QStringEncoder, QTimer
from PySide6.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
import time
import ssl
import json
import os
import zstd
from dateutil.parser import parse
import datetime,re

class AxisManager(QObject):
    access_token = None
    #json受信時用シグナル
    jsonReceived = Signal(str)
    eewReceived = Signal(dict)
    eewreportReceived = Signal(list,list,str,bool)
    telopDataReceived = Signal(dict,bool)
    jsondir=R"axisjsondata"
    def __init__(self,parent=None):
        super().__init__(parent=None)
        
        #self.getAccessToken()
        self.file_path="settings/token.json"
        with open(self.file_path) as tokenfile:
            tjson=json.load(tokenfile)
            self.access_token=tjson["token"]

        self.ws = QWebSocket()
        self.url_token = QUrl("https://axis.prioris.jp/api/token/refresh")
        url=QUrl("wss://ws.axis.prioris.jp/socket")
        self.req=QNetworkRequest()
        self.req.setUrl(url)
        self.req.setRawHeader(QByteArray("Authorization"), QByteArray("bearer "+self.access_token))
        self.ws.connected.connect(self.onOpen)
        self.ws.error.connect(self.onError)
        self.ws.textMessageReceived.connect(self.onMessage)
        
        self.ws.pong.connect(self.onPong)
        self.ws.open(self.req)
        self.timer_id=self.startTimer(30000)
        self.jsondir=R"./axisjsondata"
        with open(R"settings/seis_area.json","rb") as f:
            self.areadecoder=json.load(f)
        
    def showSettings(self):
        pass
        
    def sendData(self):
        with open(R"axisjsondata\eew20240101-161217.json.zst", "rb") as f:
            data=f.read()
            text=zstd.decompress(data)
            result1=text.decode('shift_jis')
            #print(result1)
            self.onMessage(result1)
    def sendData2(self):
        with open(R"axisjsondata/breaking-news20231231-001759.json.zst", "rb") as f:
            data=f.read()
            text=zstd.decompress(data)
            result1=text.decode('shift_jis')
            #print(result1)
            self.onMessage(result1)
    def sendDataNews(self):
        with open(R"json\20240826060605_0_VXKO54_130000.json", encoding="shift_jis") as f:
            text=f.read()
            self.onMessage(text)
    def sendDataEEW(self):
        with open(R"json\eew20250107-060800.json", encoding="shift_jis") as f:
            text=f.read()
            self.onMessage(text)

    @Slot(str)
    def onMessage(self, message):
        if message=="hello":
            print("AXIS by Priorisに接続しました。")
            return
        print("a message received")
        self.Classification(message)
        #self.jsonReceived.emit(json_data)

    def onError(self, error):
        print(error)
        try:
            self.ws.open(self.req)
        except:
            self.ws.close()

    def onClose(self):
        print("### closed ###")

    def onOpen(self):
        print("### open ###")
        
    def timerEvent(self, event: QTimerEvent):
        if event.timerId()==self.timer_id:
            self.ws.ping()
            
    def onPong(self):
        pass
        #print("pong")
        
    def Classification(self,message):
        #取得したデータの分類を行う
        json_data=json.loads(message)
        channel=json_data["channel"]
        #print(channel)
        #チャンネル分類
        info=""
        if channel=="breaking-news" or channel=="quake-one" or channel=="eew":
            info=channel
        else:
            info= json_data["message"]["uuid_"]
        print(f"received message type: {info}")
        if channel=="jmx-meteorology":
            pass

        if channel=="breaking-news":
            #ニュース速報
            texttime=json_data['message']['ReportDateTime']
            time=parse(texttime)
            try:
                with open(Rf"{self.jsondir}\{json_data['channel']}{time.strftime('%Y%m%d-%H%M%S')}.json.zst","wb") as f:
                    f.write(zstd.compress(message.encode(encoding='shift-jis')))
            except:
                pass
            texts=json_data["message"]["Text"]
            textlist=[]
            logolist=[]
            soundlist=[]
            textlist.append(["<i><b>NHK</b></i><b> ニュース速報</b>",""])
            logolist.append(["",""])
            soundlist.append("./sounds/BreakingNews_sample.wav")
            len_texts=len(texts)
            print(len_texts)
            if len_texts % 2 == 1:
                texts.append("")
            for i in range(int(len(texts)/2)):
                textlist.append([texts[2*i],texts[2*i+1]])
                logolist.append(["",""])
                soundlist.append("")
            telop_dict = {
                'sound_list': soundlist,
                'logo_list': logolist,
                'text_list': textlist
            }
            self.telopDataReceived.emit(telop_dict,False)
            

        if channel=="eew":
            self.EEW(json_data)
            texttime=json_data['message']['ReportDateTime']
            time=parse(texttime)
            try:
                with open(Rf"{self.jsondir}\{json_data['channel']}{time.strftime('%Y%m%d-%H%M%S')}.json.zst","wb") as f:
                    f.write(zstd.compress(message.encode(encoding='shift-jis')))
            except:
                pass
            
        if channel=="quake-one":
            pass
        
    def EEW(self,json_data: dict):
        logo_list = []
        text_list = []
        sound_list = []
        is_final=False
        title=f"<b>気象庁発表 {json_data['message']['Title']} "
        if json_data["message"]["Flag"]["is_final"]:
            is_final=True
            title=title+"最終報"
        elif json_data["message"]["Flag"]["is_cancel"]:
            title=title+"キャンセル報"
        elif json_data["message"]["Flag"]["is_training"]:
            title=title+"訓練報"
        else:
            title=title+f"第{json_data['message']['Serial']}報"
        title=title+"</b>"
        intensity=json_data["message"]["Intensity"]
        hypocenter_name=json_data["message"]["Hypocenter"]["Name"]
        is_emergency= intensity in ["5弱","5強","6弱","6強","7"]
        
        if not is_emergency:
            text=f"震源は{hypocenter_name} 深さ {json_data['message']['Hypocenter']['Depth']} マグニチュード{json_data['message']['Magnitude']}"
            
            text_list=[[title, text]]
            logo_list=[["",f"materials/grade{intensity}.svg"]]
            sound_list=[f"sounds/Grade{intensity}.wav"]
            telop_dict = {
                'sound_list': sound_list,
                'logo_list': logo_list,
                'text_list': text_list
            }
            print(telop_dict)
            self.telopDataReceived.emit(telop_dict,True)
        else:
            text=""
            forecast={}
            
            forecast["hypocenter"]=json_data["message"]["Hypocenter"]["Coordinate"]
            forecast["hypocenter_name"]=hypocenter_name
            forecast["text"]=f"緊急地震速報(警報) {hypocenter_name} 深さ{json_data['message']['Hypocenter']['Depth']} M{json_data['message']['Magnitude']}"
            
            areaarray=[]
            forecast["intensity"]={}
            forecast["area"]={}
            strong_shindo_list=["4","5弱","5強","6弱","6強","7"]
            for data in json_data["message"]["Forecast"]:
                forecast["intensity"][data["Intensity"]["To"]]=[]
                if data["Intensity"]["To"] in strong_shindo_list:
                    areaarray.append(data["Name"])
                pass
            for data in json_data["message"]["Forecast"]:
                forecast["intensity"][data["Intensity"]["To"]].append(data["Code"])
                print(data["Code"])
                pref=self.areadecoder["class10s"][str(data["Code"])]["parent"]
                try:
                    if strong_shindo_list.index(data["Intensity"]["To"]) > strong_shindo_list.index(forecast["area"][pref]):
                        forecast["area"][pref]=data["Intensity"]["To"]
                except:
                    forecast["area"][pref]=data["Intensity"]["To"]
                        
            text=""
            areaarray=self.EEWAreaFormat(areaarray)
            for a in areaarray:
                text=text+" "+a
            forecast["areatext"]=text
            soundfile="sounds/EEW1.wav"
            forecast["soundfile"]=soundfile
            
            print(forecast["areatext"])
            self.eewReceived.emit(forecast)#hypocenter,hypocenter_name,text,soundfile)
        pass
    
    
    def NetchuSummary(self):
        textarray=[]
        logoarray=[]
        title=f"<b>環境省 気象庁発表 熱中症警戒アラート</b>"
        textarray.append(title)
        textarray.append("")
        logoarray.append("")
        logoarray.append("")
        text=f"気温が著しく高くなることにより熱中症による人の健康に係る被害が生ずるおそれがあります。"
        textarray.append(text)
        logoarray.append("")
        text=f"室内等のエアコン等により涼しい環境にして過ごすなど熱中症予防のための行動をとってください。"
        textarray.append(text)
        logoarray.append("")
        text=""
        count=0
        for pref in self.netchu_keikai_prefs:
            text=text+f" {pref}"
            count=count+1
            if count%6==0:
                textarray.append(text)
                text=""
                if len(textarray)%2==1:
                    logoarray.append("icons/netchusho.svg")
                else:
                    logoarray.append("no")
        textarray.append(text)
        if len(textarray)%2==1:
            logoarray.append("icons/netchusho.svg")
        else:
            logoarray.append("no")
        if len(textarray)%2==1:
            textarray.append("")
            logoarray.append("")   
        sound_path="sound/BreakingNews_sample.wav"
        self.newsReceived.emit(textarray,logoarray,sound_path)
        self.netchu_keikai_prefs=[]
        self.timer_netchu.stop()
        
    def EEWAreaFormat(self,l):
        list1=[]
        for a in l:
            if "石狩" in a or "後志" in a or "空知" in a:
                list1.append("北海道道央")
            if "渡島" in a or "檜山" in a or "奥尻" in a or "胆振" in a or "日高" in a:
                list1.append("北海道道南")
            if "上川" in a or "留萌" in a or "宗谷" in a or "利尻礼文" in a:
                list1.append("北海道道北")
            if "網走" in a or "北見" in a or "紋別" in a or "十勝" in a or "釧路" in a or "根室" in a:
                list1.append("北海道道東")
                
            if "青森" in a:
                list1.append("青森")
            if "岩手" in a:
                list1.append("岩手")
            if "宮城" in a:
                list1.append("宮城")
            if "秋田" in a:
                list1.append("秋田")
            if "山形" in a:
                list1.append("山形")
            if "福島" in a:
                list1.append("福島")
            if "茨城" in a:
                list1.append("茨城")
            if "栃木" in a:
                list1.append("栃木")
            if "群馬" in a:
                list1.append("群馬")
            if "埼玉" in a:
                list1.append("埼玉")
            if "千葉" in a:
                list1.append("千葉")
            if "東京" in a:
                list1.append("東京")
            izu=["伊豆大島","新島","神津島","三宅島","八丈島"]
            if a in izu:
                list1.append("伊豆諸島")
            if "小笠原" in a:
                list1.append("小笠原")
            if "神奈川" in a:
                list1.append("神奈川")
            if "新潟" in a:
                list1.append("新潟")
            if "富山" in a:
                list1.append("富山")
            if "石川" in a:
                list1.append("石川")
            if "福井" in a:
                list1.append("福井")
            if "山梨" in a:
                list1.append("長野")
            if "岐阜" in a:
                list1.append("岐阜")
            if "静岡" in a:
                list1.append("静岡")
            if "愛知" in a:
                list1.append("愛知")
            if "三重" in a:
                list1.append("三重")
            if "滋賀" in a:
                list1.append("滋賀")
            if "京都" in a:
                list1.append("京都")
            if "大阪" in a:
                list1.append("大阪")
            if "兵庫" in a:
                list1.append("兵庫")
            if "奈良" in a:
                list1.append("奈良")
            if "和歌山" in a:
                list1.append("和歌山")
            if "鳥取" in a:
                list1.append("鳥取")
            if "島根" in a:
                list1.append("島根")
            if "岡山" in a:
                list1.append("岡山")
            if "広島" in a:
                list1.append("広島")
            if "山口" in a:
                list1.append("山口")
            if "徳島" in a:
                list1.append("徳島")
            if "香川" in a:
                list1.append("香川")
            if "愛媛" in a:
                list1.append("愛媛")
            if "高知" in a:
                list1.append("高知")
            if "福岡" in a:
                list1.append("福岡")
            if "佐賀" in a:
                list1.append("佐賀")
            if "長崎" in a:
                list1.append("長崎")
            if "熊本" in a:
                list1.append("熊本")
            if "大分" in a:
                list1.append("大分")
            if "宮崎" in a:
                list1.append("宮崎")
            if "鹿児島" in a and "奄美" not in a:
                list1.append("鹿児島")
            if "奄美" in a:
                list1.append("奄美群島")
            if "沖縄県本島" in a or "久米島" in a:
                list1.append("沖縄本島")
            if "大東島" in a:
                list1.append("大東島")
            if "宮古島" in a:
                list1.append("宮古島")
            if "石垣島" in a or "与那国島" in a or "西表島" in a:
                list1.append("八重山")
        #重複削除
        l2=list(dict.fromkeys(list1))
        if len(l2)<9:
            return l2
        #対象地域が多い場合は地方名で表示
        l3=[]
        tohoku=[
            "青森","岩手","宮城","秋田","山形","福島"
        ]
        count=0
        for i,item in enumerate(l2):
            if item in tohoku:
                count=count+1
        if count>2:
            for i,item in enumerate(l2):
                if item in tohoku:
                    l2[i]="東北"
            
        kanto=[
            "茨城","栃木","群馬","埼玉","東京","千葉"
        ]
        count=0
        for i,item in enumerate(l2):
            if item in kanto:
                count=count+1
        if count>2:
            for i,item in enumerate(l2):
                if item in kanto:
                    l2[i]="関東"
        koshin=[
            "山梨","長野"
        ]
        for i,item in enumerate(l2):
            if item in koshin:
                count=count+1
        if count>1:
            for i,item in enumerate(l2):
                if item in koshin:
                    l2[i]="甲信"
        niigata=[
            "新潟"
        ]
        hokuriku=[
            "富山","石川","福井"
        ]
        for i,item in enumerate(l2):
            if item in hokuriku:
                count=count+1
        if count>1:
            for i,item in enumerate(l2):
                if item in hokuriku:
                    l2[i]="北陸"
        tokai=[
            "静岡","愛知","岐阜","三重"
        ]
        for i,item in enumerate(l2):
            if item in tokai:
                count=count+1
        if count>1:
            for i,item in enumerate(l2):
                if item in tokai:
                    l2[i]="東海"
        kinki=[
            "滋賀","京都","大阪","兵庫","奈良","和歌山"
        ]
        for i,item in enumerate(l2):
            if item in kinki:
                count=count+1
        if count>2:
            for i,item in enumerate(l2):
                if item in kinki:
                    l2[i]="近畿"
        chugoku=[
            "鳥取","島根","岡山","広島","山口"
        ]
        for i,item in enumerate(l2):
            if item in chugoku:
                count=count+1
        if count>2:
            for i,item in enumerate(l2):
                if item in chugoku:
                    l2[i]="中国"
        shikoku=[
            "香川","愛媛","徳島","高知"
        ]
        for i,item in enumerate(l2):
            if item in shikoku:
                count=count+1
        if count>1:
            for i,item in enumerate(l2):
                if item in shikoku:
                    l2[i]="四国"
        kyushu=[
            "福岡","佐賀","長崎","大分","熊本","宮崎","鹿児島"
        ]
        for i,item in enumerate(l2):
            if item in kyushu:
                count=count+1
        if count>2:
            for i,item in enumerate(l2):
                if item in kyushu:
                    l2[i]="九州"
        l3=list(dict.fromkeys(l2))
        return l3
    
    def textformat(self,text):
        text2=text
        #すべての数値を半角に置き換える
        text2=text2.replace('０','0')
        text2=text2.replace('１','1')
        text2=text2.replace('２','2')
        text2=text2.replace('３','3')
        text2=text2.replace('４','4')
        text2=text2.replace('５','5')
        text2=text2.replace('６','6')
        text2=text2.replace('７','7')
        text2=text2.replace('８','8')
        text2=text2.replace('９','9')
        text2=text2.replace('．','.')
        text2=text2.replace('ａ','a')
        text2=text2.replace('ｂ','b')
        text2=text2.replace('ｃ','c')
        text2=text2.replace('ｄ','d')
        text2=text2.replace('ｅ','e')
        text2=text2.replace('ｆ','f')
        text2=text2.replace('ｇ','g')
        text2=text2.replace('ｈ','h')
        text2=text2.replace('ｉ','i')
        text2=text2.replace('ｊ','j')
        text2=text2.replace('ｋ','k')
        text2=text2.replace('ｌ','l')
        text2=text2.replace('ｍ','m')
        text2=text2.replace('ｎ','n')
        text2=text2.replace('ｏ','o')
        text2=text2.replace('ｐ','p')
        text2=text2.replace('ｑ','q')
        text2=text2.replace('ｒ','r')
        text2=text2.replace('ｓ','s')
        text2=text2.replace('ｔ','t')
        text2=text2.replace('ｕ','u')
        text2=text2.replace('ｖ','v')
        text2=text2.replace('ｗ','w')
        text2=text2.replace('ｘ','x')
        text2=text2.replace('ｙ','y')
        text2=text2.replace('ｚ','z')
        
        
        #text2=text2.replace('［台風の現況と予想］','台風の現況と予想についてお伝えします。')
        text2=text2.replace('ヘクトパスカル','ヘクトパスカル、')
        #text2=re.sub(r'　*([.*])　*([0-9]*)メートル（([0-9]*)メートル）',r'\1で、\2メートル、最大\3メートル、',text2)
        #text2=re.sub(r'　*([.*])　*([0-9]*)ミリ',r'\1で、\2ミリ、',text2)
        #text2=re.sub(r'　*([0-9\.]*)m',r'\1メートル',text2)
        #text2=text2.replace('＜概況＞','概況についてお伝えします。')
        #text2=text2.replace('〈概況〉','概況についてお伝えします。')
        #text2=text2.replace('《全警戒解除》','全警戒解除の情報です。')
        #text2=text2.replace('＜全警戒解除＞','全警戒解除の情報です。')
        #text2=re.sub(r'【警戒レベル([0-9])相当情報［(.*)］】',r'\2の警戒レベル\1に相当する情報です。',text2)
        #text2=re.sub(r'【警戒レベル([0-9])相当情報［(.*)］】',rf'<font color="{self.warning_color[}\1{]}">【警戒レベル\1相当情報［\2］】</font>',text2)
        #text2=text2.replace('＜とるべき措置＞','とるべき措置についてお伝えします。')
        #text2=text2.replace('［補足事項］','補足事項です。')
        text2=text2.replace('（活火山であることに留意）','、活火山であることに留意')
        text2=text2.replace('（火口周辺規制）','、火口周辺規制')
        text2=text2.replace('（入山規制）','、入山規制')
        text2=text2.replace('（高齢者等避難）','、高齢者等避難')
        text2=text2.replace('（避難）','、避難')
        text2=text2.replace('火山ガス（二酸化硫黄）','火山ガス')
        text2=text2.replace('降灰予報（定時）','定時降灰予報')
        text2=text2.replace('火山名','')

        #text2=text2.replace(r'【(.*)地方】','')
        #text2=re.sub(r'［(.*)］',r'\1です。',text2)
        #空白や改行を置換
        text2=text2.replace('\n','')
        text2=text2.replace(' ','')
        text2=text2.replace('　','')

        #カッコ付きの見出しを平文に置き換える
        #震度の置換
        text2=text2.replace('5-','5弱')
        text2=text2.replace('6-','6弱')
        text2=text2.replace('5+','5強')
        text2=text2.replace('6+','6強')
        #時間単位の整形
        units=['日','時','分','秒']
        for unit in units:
            text2=text2.replace('00'+unit,'0'+unit)
            text2=text2.replace('01'+unit,'1'+unit)
            text2=text2.replace('02'+unit,'2'+unit)
            text2=text2.replace('03'+unit,'3'+unit)
            text2=text2.replace('04'+unit,'4'+unit)
            text2=text2.replace('05'+unit,'5'+unit)
            text2=text2.replace('06'+unit,'6'+unit)
            text2=text2.replace('07'+unit,'7'+unit)
            text2=text2.replace('08'+unit,'8'+unit)
            text2=text2.replace('09'+unit,'9'+unit)
        return text2
    