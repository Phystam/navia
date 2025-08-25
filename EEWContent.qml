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
  property var areacode: {}
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
  function getColorByWarningLevel(level) {
    switch (level) {
      case "4": return "#fae696"; // 平常
      case "5弱": return "#ffe600"; // レベル1・早期注意情報
      case "5強": return "#f29900"; // レベル2・注意報
      case "6弱": return "#ff2800"; // レベル3・警報
      case "6強": return "#a50021"; // レベル4・その他の特別警報・危険警報・土砂災害警戒情報等
      case "7": return "#b40068"; // レベル5・大雨特別警報
      default: return "#838383";
    }
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
      zoomLevel:6.5
      color:"transparent"
      GeoJsonData {
        id: fuken
        sourceUrl: "file:///" + currentDir + "/geo/緊急地震速報／府県予報区.geojson"
      }
      MapItemView{
        id: miv
        model: fuken.model[0].data
        delegate: MapItemGroup{ 
          id: mapgroup
          required property int index
          property int item_index: index
          property var item_model: mapgroup.parent.model
          property var polys: showMap(miv.model,index)
          property var polycolor: getColorForItem()
          Repeater{
            model: polys
            delegate: MapPolygon{
              path: modelData
              color: polycolor//"#838383"
              border.width:5
              border.color:"#525252"
            }
          }
          function getColorForItem(){
            console.log("getColor")
            var feature = item_model[item_index];
            //return "#838383";
            //return "#ffef10";
            if (feature && feature.properties) {
              var code = feature.properties.code;
              console.log("code="+code)
              var intensity=eew_content.areacode[code]
              return getColorByWarningLevel(intensity);
              //var check = timelineManager.checkVPHW51("pref",code);
              //var level = timelineManager.getMeteWarningLevel("pref", code);
              //return getColorByWarningLevel(level);
            } else {
              return "#c8c8cb";
            }
          }
        }
        MapQuickItem {
          coordinate: hypocenter
          anchorPoint.x: centerimage.width/2
          anchorPoint.y: centerimage.height/2
          z:eew_content.height*0.04
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