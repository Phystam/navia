import QtQuick
import QtQuick.Controls
import QtMultimedia

Item{
  id: telop
  
  anchors.horizontalCenter: parent.horizontalCenter
  anchors.top: parent.top
  anchors.topMargin: parent.height*0.05
  width:parent.width*0.85
  height:parent.height*0.11
  /* Rectangle {
      anchors.fill: parent
      color: "transparent"
      border.color: "blue"
  } */
  property var soundList: []
  property var textList: []
  property var logoList: []

  property var soundList_emergency: []
  property var textList_emergency: []
  property var logoList_emergency: []
  ListModel {
    id: logoListModel1
  }
  ListModel {
    id: logoListModel2
  }
  ListModel {
    id: logoListModel3
  }
  ListModel {
    id: logoListModel4
  }
  //テキスト用: プロパティバインディングのため配列ではない
  property string text1 : ""
  property string text2 : ""
  //緊急地震速報テキスト用。他のテロップと被った時にしか使わない
  property string text3 : ""
  property string text4 : ""
  property int index: 0

  Timer {
    id: telopTimer1
    interval: 4000 // 4秒ごとにテキストを表示
    repeat: true
    running:false
    triggeredOnStart: true
    onTriggered: {
      if (parent.textList.length > 0) {
        nextText()
      } else {
        init()
        running=false
      }
    }
  }
  //緊急地震速報用のタイマー
  Timer {
    id: telopTimer2
    interval: 30000 // 4秒ごとにテキストを表示
    repeat: true
    running:false
    triggeredOnStart: true
    onTriggered: {
      if (parent.textList_emergency.length > 0) {
        nextText_emergency()
      } else {
        init_emergency()
        running=false
      }
    }
  }
  //音声発出用
  SoundEffect {
    id: sound
    source: "sounds/Grade3.wav"
  }

  function init(){
    text1=""
    text2=""
    logoListModel1.clear()
    logoListModel2.clear()
    telopTimer1.stop()
  }
  function init_emergency(){
    text3=""
    text4=""
    logoListModel3.clear()
    logoListModel4.clear()
    telopTimer2.stop()
  }

  function playSound(filename) {
    sound.source=filename
    sound.play()
  }
  function push(_soundList, _logoList, _textList, emergency) {
    // 現在入っているリストが空であるか確認
    var is_first=false;
    if (telop.textList.length == 0) {
      // 既存のリストをクリア
      is_first=true;
    }
    //表示中にEEWが入ったときはこっち。
    if (emergency){
      for(var i=0;i<_soundList.length;i++){
      telop.soundList_emergency.push(_soundList[i])
      }
      for(var i=0;i<_logoList.length;i++){
        telop.logoList_emergency.push(_logoList[i])
      }
      for(var i=0;i<_textList.length;i++){
        telop.textList_emergency.push(_textList[i])
        //console.log("telop.textList.push: " + _textList[i]) 
      }
    }
    for(var i=0;i<_soundList.length;i++){
      telop.soundList.push(_soundList[i])
    }
    for(var i=0;i<_logoList.length;i++){
      telop.logoList.push(_logoList[i])
    }
    for(var i=0;i<_textList.length;i++){
      telop.textList.push(_textList[i])
      //console.log("telop.textList.push: " + _textList[i]) 
    }
    if (is_first) {
      //初期化時に何も表示されていない場合は、最初のテキストを表示する
      telopTimer1.start()
    }
    //緊急地震速報用
    if (emergency) {
      telopTimer2.start()
    }
  }

  function nextText(){
    logoListModel1.clear()
    logoListModel2.clear()
    if(soundList[index]!=""){
      playSound(soundList[index])
    }
    soundList.shift() // 音声も同様に削除
    // ロゴがない場合 → 上部全体を使ってテロップを表示する
    if (logoList[0][0]=="" && logoList[0][1]==""){
      text1=textList[0][0]
      text2=textList[0][1]
      //console.log("telop.textList: " + text1 + ", " + text2)
      txt1.horizontalAlignment=Text.AlignHCenter
      txt1.anchors.left=telop.left
      txt1.anchors.right=telop.right
      txt2.horizontalAlignment=Text.AlignHCenter
      txt2.anchors.left=telop.left
      txt2.anchors.right=telop.right
      txt2.x=0
      txt1.anchors.leftMargin=0
      txt2.anchors.leftMargin=0
    }
    // ロゴがある場合 → ロゴ(さらにリストになっている)を表示しながらテロップを表示する
    else {
      var logo1=logoList[0][0]
      var logo2=logoList[0][1]
      var logo1array=logo1.split(",")
      var logo2array=logo2.split(",")
      
      //console.log(logo1array)
      //右から順に詰めていくので、左から順番通りにするためには逆順で入れる必要がある
      for(var i=logo1array.length-1;i>=0;i--){
        if(logo1array[i]!="no"){
          logoListModel1.append({"value":logo1array[i]})
        }else {
          logoListModel1.append({"value":""})
        }
      }
      for(var i=logo2array.length-1;i>=0;i--){
        if(logo2array[i]!="no"){
          logoListModel2.append({"value":logo2array[i]})
        } else {
          logoListModel2.append({"value":""})
        }
      }
      text1=textList[0][0]
      text2=textList[0][1]
      //txt1.width=telop.width*0.6
      txt1.horizontalAlignment=Text.AlignLeft
      txt1.anchors.left=telop.horizontalCenter
      txt1.anchors.leftMargin=-telop.width*0.1
      txt1.anchors.right=telop.right
      //txt2.width=telop.width*0.6
      txt2.horizontalAlignment=Text.AlignLeft
      txt2.anchors.left=telop.horizontalCenter
      txt2.anchors.leftMargin=-telop.width*0.1
      //console.log("telop.textList: " + text1 + ", " + text2)
    }
    textList.shift() // テキストを表示したらリストから削除
    logoList.shift() 
    //console.log("textList.length: " + textList.length)
  }

  function nextText_emergency(){
    logoListModel3.clear()
    logoListModel4.clear()
    if(soundList[index]!=""){
      playSound(soundList[index])
    }
    soundList.shift() // 音声も同様に削除
    // ロゴがない場合 → 上部全体を使ってテロップを表示する
    if (logoList[0][0]=="" && logoList[0][1]==""){
      text3=textList_emergency[0][0]
      text4=textList_emergency[0][1]
      //console.log("telop.textList: " + text1 + ", " + text2)
      txt3.horizontalAlignment=Text.AlignHCenter
      txt3.anchors.left=telop.left
      txt3.anchors.right=telop.right
      txt4.horizontalAlignment=Text.AlignHCenter
      txt4.anchors.left=telop.left
      txt4.anchors.right=telop.right
      txt4.x=0
      txt3.anchors.leftMargin=0
      txt4.anchors.leftMargin=0
    }
    // ロゴがある場合 → ロゴ(さらにリストになっている)を表示しながらテロップを表示する
    else {
      var logo3=logoList_emergency[0][0]
      var logo4=logoList_emergency[0][1]
      var logo3array=logo3.split(",")
      var logo4array=logo4.split(",")
      
      //console.log(logo1array)
      //右から順に詰めていくので、左から順番通りにするためには逆順で入れる必要がある
      for(var i=logo3array.length-1;i>=0;i--){
        if(logo3array[i]!="no"){
          logoListModel3.append({"value":logo3array[i]})
        }else {
          logoListModel3.append({"value":""})
        }
      }
      for(var i=logo4array.length-1;i>=0;i--){
        if(logo4array[i]!="no"){
          logoListModel4.append({"value":logo4array[i]})
        } else {
          logoListModel4.append({"value":""})
        }
      }
      text3=textList_emergency[0][0]
      text4=textList_emergency[0][1]
      //txt1.width=telop.width*0.6
      txt3.horizontalAlignment=Text.AlignLeft
      txt3.anchors.left=telop.horizontalCenter
      txt3.anchors.leftMargin=-telop.width*0.1
      txt3.anchors.right=telop.right
      //txt2.width=telop.width*0.6
      txt4.horizontalAlignment=Text.AlignLeft
      txt4.anchors.left=telop.horizontalCenter
      txt4.anchors.leftMargin=-telop.width*0.1
      //console.log("telop.textList: " + text1 + ", " + text2)
    }
    textList_emergency.shift() // テキストを表示したらリストから削除
    logoList_emergency.shift() 
    //console.log("textList.length: " + textList.length)
  }

  Text {
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    width:parent.width
    height:parent.height*5/11
    id: txt1
    text: parent.text1
    //font.family: "Neue Haas Grotesk"
    font.family: "Source Han Sans"
    //font.family: "HGS創英角ﾎﾟｯﾌﾟ体"
    font.pointSize: parent.height*0.5
    color: "white"
    style: Text.Outline
    styleColor: "black"
    fontSizeMode:Text.Fit
    /* Rectangle {
      anchors.fill: parent
      color: "transparent"
      border.color: "red"
    } */
  }
  Text {
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
    anchors.bottom: parent.bottom
    anchors.left: parent.left
    anchors.right: parent.right
    width:parent.width
    height:parent.height*5/11
    id: txt2
    text: parent.text2
    //font.family: "Neue Haas Grotesk"
    font.family: "Source Han Sans"
    font.pointSize: parent.height*0.5
    color: "white"
    style: Text.Outline
    styleColor: "black"
    fontSizeMode:Text.Fit
    /* Rectangle {
      anchors.fill: parent
      color: "transparent"
      border.color: "red"
    } */
  }
  Text {
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
    anchors.top: txt2.bottom
    //anchors.right:parent.right
    width:parent.width
    height:parent.height*5/11
    id: txt3
    text: parent.text3
    //font.family: "Neue Haas Grotesk"
    font.family: "Source Han Sans"
    font.pointSize: Screen.height*0.03
    color: "white"
    style: Text.Outline
    styleColor: "black"
    fontSizeMode:Text.Fit
  }
  Text {
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
    anchors.top: txt3.bottom
    //anchors.right:parent.right
    width:parent.width
    height:parent.height*5/11
    id: txt4
    text: parent.text4
    //font.family: "Neue Haas Grotesk"
    font.family: "Source Han Sans"
    font.pointSize: Screen.height*0.03
    color: "white"
    style: Text.Outline
    styleColor: "black"
    fontSizeMode:Text.Fit
  }
  // 震度や警報・注意報のロゴを表示する部分
  Row{
    anchors.top: parent.top
    anchors.right:txt1.left
    anchors.rightMargin: parent.width*0.01
    height:parent.height*5/11
    layoutDirection:Qt.RightToLeft
    id: logoA
    spacing:parent.width*0.005
    Repeater {
      model: logoListModel1
      Image {
        height:parent.height
        fillMode:Image.PreserveAspectFit
        source: model.value
      }
    }
  }
  Row{
    anchors.bottom:parent.bottom
    anchors.right:txt2.left
    anchors.rightMargin: parent.width*0.01
    height:parent.height*5/11
    layoutDirection:Qt.RightToLeft
    id: logoB
    spacing:parent.width*0.005
    Repeater {
      model: logoListModel2
      Image {
        height:parent.height
        fillMode:Image.PreserveAspectFit
        source: model.value
      }
    }
  }

}