import QtQuick
import QtQuick.Controls
import QtLocation
import QtPositioning

MapItemGroup {
    //台風中心
    MapQuickItem {
        visible: modelData.geometry.type==="Point"
        id: typhoon_center
        coordinate: QtPositioning.coordinate(modelData.geometry.coordinates[1],modelData.geometry.coordinates[0])
        anchorPoint.x:typhoon_center_image.width/2
        anchorPoint.y:typhoon_center_image.height/2
        sourceItem: Image{
            id: typhoon_center_image
            width: 15
            height:15
            source: "../materials/typhoon_center.svg"
        }
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            id:mouse
            onClicked: {
                console.log("typhoon clicked" + modelData.properties.event_id)
                if (modelData.properties.event_id) {
                    naviaWindow.handleTyphoonClick(modelData.properties.event_id)
                }
            }
            Rectangle {
                id: toolTip
                visible: parent.containsMouse
                x: mouse.x + 30
                y: mouse.y + 10
                width: 250
                height: 150
                color: "lightgray"
                border.color: "black"
                radius: 5
                Column {
                    id: toolTipColumn
                    anchors.fill: toolTip
                    Label{
                        font.pixelSize: 20
                        text: "<b>台風第"+modelData.properties.typhoon_number+"号 "+modelData.properties.name+"</b>"
                    }
                    Text{
                        text: modelData.properties.datetime_format
                    }
                    Rectangle{
                        height: 1
                        border.color: "black"
                        width: parent.width
                    }
                    Text{
                        visible: text !=""
                        text: modelData.properties.remark
                    }
                    Text{
                        visible: modelData.properties.area_class !=""
                        text: "大きさ:\t"+modelData.properties.area_class
                    }
                    Text{
                        visible: modelData.properties.intensity_class !=""
                        text: "強さ:\t"+modelData.properties.intensity_class
                    }
                    Text{
                        visible: modelData.properties.location !=""
                        text: "位置:\t"+modelData.properties.location
                    }
                    Text{
                        text: "中心気圧:\t"+modelData.properties.pressure +" hPa"
                    }
                    Text{
                        text: "速度:\t"+modelData.properties.direction +" "+ modelData.properties.speed +" km/h"
                    }
                    Text{
                        text: "最大風速:\t"+modelData.properties.maxwindspeed +" m/s"
                    }
                    Text{
                        text: "最大瞬間風速:\t"+modelData.properties.windspeed +" m/s"
                    }
                    
                }
            }
        }
    }
    MapCircle {
        visible: modelData.properties.probability_radius!=""
        border.color: "#36ffffff"
        border.width: 1
        center: typhoon_center.coordinate
        radius: Number(modelData.properties.probability_radius)*1000
    }
    //強風域
    MapCircle {
        visible:modelData.geometry.type==="Point"&& modelData.properties.strong_center!="" && modelData.properties.datetime_type=="推定　１時間後"
        border.color: "#ffffff"
        border.width: 0
        color:"#36f2e600"
        center: QtPositioning.coordinate(modelData.properties.strong_center[1],modelData.properties.strong_center[0])
        radius: Number(modelData.properties.strong_radius)*1000
    }
    MapCircle {
        visible: modelData.geometry.type==="Point"&&modelData.properties.storm_center!="" && modelData.properties.datetime_type=="推定　１時間後"
        border.color: "#ffffff"
        border.width: 0
        color:"#36FF2800"
        center: QtPositioning.coordinate(modelData.properties.storm_center[1],modelData.properties.storm_center[0])
        radius: Number(modelData.properties.storm_radius)*1000
        referenceSurface: QtLocation.ReferenceSurface.Globe
    }

    MapPolyline {
        visible: modelData.geometry.type==="LineString"
        line.color: "#36ffffff"
        line.width: 1
        path: {
            var linePath = []
            for (var i in modelData.geometry.coordinates) {
                console.log(modelData.geometry.coordinates[i])
                linePath.push(QtPositioning.coordinate(modelData.geometry.coordinates[i][1],modelData.geometry.coordinates[i][0]));
            }
            return linePath
        }
    }
    ////暴風域
    //MapCircle {
    //    visible: modelData.properties.probability_radius!=""
    //    border.color: "#ffffff"
    //    border.width: 1
    //    center: typhoon_center.coordinate
    //    radius: Number(modelData.properties.probability_radius)*1000
    //}
    //予報円
    
}
