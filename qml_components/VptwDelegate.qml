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
            width: 20
            height:20
            source: "../materials/typhoon_center.svg"
        }
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            id:mouse
            Rectangle {
                id: toolTip
                visible: parent.containsMouse
                x: mouse.x + 30
                y: mouse.y + 10
                width: 100
                height: 30
                color: "lightgray"
                border.color: "black"
                radius: 5
                Text {
                    anchors.centerIn: parent
                    text: modelData.properties.name
                    font.pixelSize: 12
                }
            }
        }
    }
    MapCircle {
        visible: modelData.properties.probability_radius!=""
        border.color: "#84ffffff"
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
    }

    MapPolyline {
        visible: modelData.geometry.type==="LineString"
        line.color: "#84ffffff"
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
