import QtQuick
import QtQuick.Controls
import QtMultimedia
import QtLocation
import QtPositioning

Rectangle {
    anchors.bottom: parent.bottom
    anchors.right: parent.right
    anchors.bottomMargin:parent.height*0.1
    anchors.rightMargin:parent.height*0.1
    width:parent.height*0.4
    height:parent.height*0.43
    id: tsunami_content
    color: "#80000000" //50% alpha 黒色
    property var bigtsunamiWarningCodes: []
    property var tsunamiWarningCodes: []
    property var tsunamiCautionCodes: []
    property var tsunamiInfoCodes: []
    SoundEffect {
        id: sound
        source: "sound/Grade3.wav"
    }
    function playSound(filename) {
        sound.source=filename
        sound.play()
    }

    Map {
      id:view
      anchors.fill:parent
      plugin: Plugin { name: "itemsoverlay" }
      center: QtPositioning.coordinate(35,135.6)
      zoomLevel:5.5
      color:"transparent"
      //GeoJsonData {
      //  id: fuken
      //  sourceUrl: "file:///" + applicationDirPath + "/kinkyuu_fuken.geojson"
      //  //sourceUrl: "file:///g:/マイドライブ/NAVIA/kinkyuu_fuken.geojson"
      //}
      GeoJsonData {
        id: tsunami
        sourceUrl: "file:///" + applicationDirPath + "/geo/津波予報区.geojson"
        //sourceUrl: "file:///g:/マイドライブ/NAVIA/tsunami.geojson"
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
              color: "#888888"
              border.width:0
              border.color:"#888888"
            }
          }
        }
      }

      MapItemView{
        id: miv2
        model: tsunami.model[0].data
        delegate: MapItemGroup{ 
          id: mapgroup2
          required property int index
          property var polys: showTsunami(miv2.model,index)
          property var col: tsunamiLineColor(miv2.model,index)
          property var wid: tsunamiLineWidth(miv2.model,index)
          Repeater{
            model: polys
            delegate: MapPolyline{
              path: modelData
              line.color: col
              line.width: wid
            }
          }
        }
      }
    }
    Rectangle {
      id: tsunami_caution_rect
      anchors.bottom: parent.bottom
      anchors.right: parent.right
      anchors.bottomMargin: parent.height*0.5
      anchors.rightMargin: parent.width*0.05
      width:parent.width*0.08
      height:parent.width*0.03
      color: "#FAF500"
      border.color:"black"
      border.width: 2
    }
    //Text {
    //  id: tsunami_caution_text
    //  anchors.right: tsunami_caution_rect.right
    //  anchors.top: tsunami_caution_rect.bottom
    //  width: tsunami_caution_rect.width
    //  height: parent.height*0.3
    //  fontSizeMode: Text.HorizontalFit
    //  text:"津\n波\n注\n意\n報"
    //}
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
    function showTsunami(model,j){
      var paths=[];
      var path=[];
      //print(Object.entries(tsunami.model[0].data[0].type))
      //print(Object.entries(model[j].properties.code))
      //print(tsunamiWarningCodes[0])
      if(model[j].type=="LineString"){
        
        var c=model[j].data.path;
        for (var i=0;i<c.length;i++){
          path.push(QtPositioning.coordinate(c[i].latitude,c[i].longitude));
        }
        paths.push(path);
      }
      if(model[j].type=="MultiLineString"){
        var polys=model[j].data;
        for(var k=0;k<polys.length;k++){
          var c=model[j].data[k].data.path;
          for (var i=0;i<c.length;i++){
            path.push(QtPositioning.coordinate(c[i].latitude,c[i].longitude));
          }
          paths.push(path);
          path=[];
        }
      }
      return paths;
    }
    function tsunamiLineColor(model,j){
      //print(Object.entries(tsunami.model[0].data[0].type))
      var color="black"
      //print(typeof model[j].properties.code);
      //print(typeof tsunamiWarningCodes);
      if(tsunamiWarningCodes.includes(model[j].properties.code)){
        color="#F30000";
      }
      if(bigtsunamiWarningCodes.includes(model[j].properties.code)){
        color="#C800FF";
      }
      if(tsunamiCautionCodes.includes(model[j].properties.code)){
        color="#F2E700";
      }
      if(tsunamiInfoCodes.includes(model[j].properties.code)){
        color="#F2F2FF";
      }
      return color;
    }
    function tsunamiLineWidth(model,j){
      //print(Object.entries(tsunami.model[0].data[0].type))
      var width=1;
      //print(typeof model[j].properties.code);
      //print(typeof tsunamiWarningCodes);
      if(tsunamiWarningCodes.includes(model[j].properties.code)){
        width=2;
      }
      if(bigtsunamiWarningCodes.includes(model[j].properties.code)){
        width=4;
      }
      if(tsunamiCautionCodes.includes(model[j].properties.code)){
        width=2;
      }
      if(tsunamiInfoCodes.includes(model[j].properties.code)){
        width=1;
      }
      return width;
    }
}