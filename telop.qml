import QtQuick
import QtQuick.Controls
import QtMultimedia

Item{
  id: telop
  
  anchors.horizontalCenter: parent.horizontalCenter
  anchors.top: parent.top
  anchors.topMargin: parent.height*0.05
  width:parent.width*0.8
  height:parent.height*0.11
  property var soundList: []
  property var textList: []
  property var logoList: []
  ListModel {
    id: logoListModel1
  }
  ListModel {
    id: logoListModel2
  }
  //テキスト用: プロパティバインディングのため配列ではない
  property string text1 : "<b>テキスト1</b>"
  property string text2 : "<テキスト2>"
  //緊急地震速報テキスト用。他のテロップと被った時にしか使わない
  property string text3 : "<テキスト3>"
  property string text4 : "<テキスト4>"
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
    interval: 4000 // 4秒ごとにテキストを表示
    repeat: true
    running:false
    triggeredOnStart: true
    onTriggered: {
      repeat=true
      running=true
      //if (content_object !== null) {
      //  var end = content_object.nextText();
      //} else {
        repeat=false
        running=false
      //}
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
    text3=""
    text4=""
    telopTimer1.stop()
  }

  function playSound(filename) {
    sound.source=filename
    sound.play()
  }
  function push(_soundList, _logoList, _textList) {
    // 現在入っているリストが空であるか確認
    var is_first=false;
    if (telop.textList.length == 0) {
      // 既存のリストをクリア
      is_first=true;
    }
    for(var i=0;i<_soundList.length;i++){
      telop.soundList.push(_soundList[i])
    }
    for(var i=0;i<_logoList.length;i++){
      telop.logoList.push(_logoList[i])
    }
    for(var i=0;i<_textList.length;i++){
      telop.textList.push(_textList[i])
      console.log("telop.textList.push: " + _textList[i]) 
    }
    if (is_first) {
      //初期化時に何も表示されていない場合は、最初のテキストを表示する
      telopTimer1.start()
    }
  }

  function nextText(){
    //logoListModel1.clear()
    //logoListModel2.clear()
    if(soundList[index]!=""){
      playSound(soundList[index])
    }
    soundList.shift() // 音声も同様に削除
    // ロゴがない場合 → 上部全体を使ってテロップを表示する
    if (logoList[0][0]=="" && logoList[0][1]==""){
      text1=textList[0][0]
      text2=textList[0][1]
      console.log("telop.textList: " + text1 + ", " + text2)

    }
    // ロゴがある場合 → ロゴ(さらにリストになっている)を表示しながらテロップを表示する
    else {
      text1=textList[0][0]
      text2=textList[0][1]
      console.log("telop.textList: " + text1 + ", " + text2)
    }
    textList.shift() // テキストを表示したらリストから削除
    logoList.shift() 
    console.log("textList.length: " + textList.length)
  }
      // else {
      // text1=""
      // text2=""
      // var logo3=logoList[index]
      // text3=textList[index]
      // index++
      // var logo4=logoList[index]
      // text4=textList[index]
      // index++
      // var logo3array=logo3.split(",")
      // var logo4array=logo4.split(",")
      // //右から順に詰めていくので、左から順番通りにするためには逆順で入れる必要がある
      // for(var i=logo3array.length-1;i>=0;i--){
      //   if(logo3array[i]!="no"){
      //     logoListModel3.append({"value":logo3array[i]})
      //   }else {
      //     logoListModel3.append({"value":""})
      //   }
      // }
      // for(var i=logo4array.length-1;i>=0;i--){
      //   if(logo4array[i]!="no"){
      //     logoListModel4.append({"value":logo4array[i]})
      //   } else {
      //     logoListModel4.append({"value":""})
      //   }
      // }
      //
  Text {
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
    anchors.top: parent.top
    width:parent.width
    height:parent.height*5/11
    id: txt1
    text: parent.text1
    //font.family: "Neue Haas Grotesk"
    font.family: "Source Han Sans"
    //font.family: "HGS創英角ﾎﾟｯﾌﾟ体"
    font.pointSize: Screen.height*0.03
    color: "white"
    style: Text.Outline
    styleColor: "black"
    fontSizeMode:Text.Fit
  }
  Text {
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
    anchors.top: txt1.bottom
    width:parent.width
    height:parent.height*5/11
    id: txt2
    text: parent.text2
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
    anchors.right:txt3.left
    height:parent.height*5/11
    layoutDirection:Qt.RightToLeft
    id: logoA
    spacing:parent.width*0.005
    Repeater {
      model: logoListModel3
      Image {
        height:parent.height
        fillMode:Image.PreserveAspectFit
        source: model.value
      }
    }
  }
  Row{
    anchors.bottom:parent.bottom
    anchors.right:txt4.left
    height:parent.height*5/11
    layoutDirection:Qt.RightToLeft
    id: logoB
    spacing:parent.width*0.005
    Repeater {
      model: logoListModel4
      Image {
        height:parent.height
        fillMode:Image.PreserveAspectFit
        source: model.value
      }
    }
  }

}