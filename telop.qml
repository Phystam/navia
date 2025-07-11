import QtQuick
import QtQuick.Controls
import QtMultimedia

Item{
  id: news_content
  
  anchors.horizontalCenter: parent.horizontalCenter
  anchors.top: parent.top
  anchors.topMargin: parent.height*0.05
  width:parent.width*0.8
  height:parent.height*0.11
  property list<string> textList: []
  property list<string> logoList: []
  ListModel {
    id: logoListModel3
  }
  ListModel {
    id: logoListModel4
  }
  property string text1 : ""
  property string text2 : ""
  property string text3 : "テキスト1"
  property string text4 : "テキスト2"
  property int index:0
  signal readyNext
  //音声発出用
  SoundEffect {
    id: sound
    source: "sound/Grade3.wav"
  }

  function init(){
    text1=""
    text2=""
    text3=""
    text4=""
    index=0
    textList=[]
    logoList=[]
  }

  function playSound(filename) {
    sound.source=filename
    sound.play()
  }
  function nextText(){
    logoListModel3.clear()
    logoListModel4.clear()
    if(index<textList.length){
      if(logoList[index]=="" && logoList[index+1]==""){
        text1=textList[index]
        index++
        text2=textList[index]
        index++
        text3=""
        text4=""
      } else {
        text1=""
        text2=""
        var logo3=logoList[index]
        text3=textList[index]
        index++
        var logo4=logoList[index]
        text4=textList[index]
        index++
        var logo3array=logo3.split(",")
        var logo4array=logo4.split(",")
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
      }
    } else {
      init()
      readyNext()
      news_content.destroy()
      return true
    }
    return false
  }
  //onCompleted: {
  //  playSound.play()
  //}
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
    font.pointSize: 48
    color: "white"
    style: Text.Outline
    styleColor: "black"
    fontSizeMode:Text.Fit
  }
  Text {
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
    anchors.bottom:parent.bottom
    width:parent.width
    height:parent.height*5/11
    id: txt2
    text: parent.text2
    //font.family: "Neue Haas Grotesk"
    font.family: "Source Han Sans"
    font.pointSize: 48
    color: "white"
    style: Text.Outline
    styleColor: "black"
    fontSizeMode:Text.Fit
  }
  Text {
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignLeft
    anchors.top: parent.top
    anchors.right:parent.right
    width:parent.width*0.70
    height:parent.height*5/11
    id: txt3
    text: parent.text3
    //font.family: "Neue Haas Grotesk"
    font.family: "Source Han Sans"
    font.pointSize: 48
    color: "white"
    style: Text.Outline
    styleColor: "black"
    fontSizeMode:Text.Fit
  }
  Text {
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignLeft
    anchors.bottom:parent.bottom
    anchors.right:parent.right
    width:parent.width*0.60
    height:parent.height*5/11
    id: txt4
    text: parent.text4
    //font.family: "Neue Haas Grotesk"
    font.family: "Source Han Sans"
    font.pointSize: 48
    color: "white"
    style: Text.Outline
    styleColor: "black"
    fontSizeMode:Text.Fit
  }
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