import QtQuick
import QtQuick.Controls
import QtMultimedia
import QtLocation
import QtPositioning
  
Rectangle {
  anchors.bottom: parent.bottom
  anchors.horizontalCenter: parent.horizontalCenter
  anchors.bottomMargin:parent.height*0.1
  width:parent.width*0.6
  height:parent.height*0.4
  id: eew_content
  color: "white"
  radius:height*0.01
  border.color:"black"
  border.width: 2
  property string warningRegion: ""
  property string areas: ""
  property var hypocenter: QtPositioning.coordinate(35,135)
  property string currentDir: mainApp.getCurrentDir()
  SoundEffect {
    id: sound
    source: "sounds/EEW1.wav"
  }
  function playSound(filename) {
    //sound.source=filename
    sound.play()
  }
  function showMap(model,j){
    var paths=[];
    var path=[];
    if(model[j].type=="Polygon"){
      var c=model[j].data.perimeter;
      for (var i=0;i<c.length;i++){
        path.push(QtPositioning.coordinate(c[i].latitude,c[i].longitude));
      }
      paths.push(path);
    }
    if(model[j].type=="MultiPolygon"){
      var polys=model[j].data;
      for(var k=0;k<polys.length;k++){
        var c=model[j].data[k].data.perimeter;
        for (var i=0;i<c.length;i++){
          path.push(QtPositioning.coordinate(c[i].latitude,c[i].longitude));
        }
        paths.push(path);
        path=[];
      }
    }
    return paths;
  }

  Rectangle {
    id: eewmap
    anchors.left: parent.left
    anchors.top: parent.top
    anchors.leftMargin: 10
    anchors.topMargin:10
    height: parent.height - 20
    width: parent.width*0.25
    gradient: Gradient{
      GradientStop { position: 0.0; color: "#585B8E"}
      GradientStop { position: 1.0; color: "#41456E"}
    }

    Map {
      id:view
      anchors.fill:parent
      plugin: Plugin { name: "itemsoverlay" }
      center: eew_content.hypocenter
      zoomLevel:8
      color:"transparent"
      GeoJsonData {
        id: fuken
        sourceUrl: "file:///" + currentDir + "/geo/緊急地震速報／地方予報区.geojson"
      }
      MapItemView{
        id: miv
        model: fuken.model[0].data
        delegate: MapItemGroup{ 
          id: mapgroup
          required property int index
          property var polys: showMap(miv.model,index)
          Repeater{
            model: polys
            delegate: MapPolygon{
              path: modelData
              color: "#838383"
              border.width:5
              border.color:"#525252"
            }
          }
        }
        MapQuickItem {
          coordinate: hypocenter
          z:100
          sourceItem: Image {
            id: centerimage
            source: "materials/centermark.svg"
          }
        }
      }
    }
  }

  Rectangle {
    id: eewtitle
    anchors.right: parent.right
    anchors.top: parent.top
    anchors.rightMargin: 10
    anchors.topMargin:10
    height: parent.height*0.25 - 20
    width: parent.width*0.75 - 25
    gradient: Gradient{
      GradientStop { position: 0.0; color: "#CF6F80"}
      GradientStop { position: 1.0; color: "#955B6C"}
    }
    Text{
      anchors.centerIn: parent
      width: parent.width*0.95
      height: parent.height*0.95
      verticalAlignment: Text.AlignVCenter
      horizontalAlignment: Text.AlignHCenter
      text: "<b>緊急地震速報（気象庁）</b>"
      //font.family: "Neue Haas Grotesk"
      font.family: "Source Han Sans"
      minimumPointSize:10
      font.pointSize:130
      fontSizeMode: Text.Fit
      color: "white"
      style: Text.Outline
      styleColor: "black"
    }
  }
  Rectangle {
    id: eewcontent
    anchors.right: parent.right
    anchors.top: eewtitle.bottom
    anchors.rightMargin: 10
    anchors.bottomMargin:10
    height: parent.height*0.75 
    width: parent.width*0.75 - 25
    gradient: Gradient{
      GradientStop { position: 0.0; color: "#466EC0"}
      GradientStop { position: 1.0; color: "#345493"}
    }
    Text{
      anchors.left: parent.left
      anchors.top: parent.top
      anchors.topMargin: 10
      anchors.leftMargin:10
      width: parent.width
      height: parent.height*0.175
      text: warningRegion+"で地震 強い揺れに警戒"
      //font.family: "Neue Haas Grotesk"
      font.family: "源柔ゴシックXP Normal"
      font.pointSize: 100
      fontSizeMode: Text.Fit
      color: "yellow"
    }
    Text{
      anchors.left: parent.left
      anchors.bottom: parent.bottom
      anchors.topMargin: 80
      anchors.leftMargin:10
      height:parent.height*0.8
      width:parent.width
      //Layout.fillWidth: true
      text: areas
      //font.family: "Neue Haas Grotesk"
      font.family: "Source Han Sans"
      font.pointSize: 72
      color: "white"
      wrapMode: Text.Wrap
    }
  }
}