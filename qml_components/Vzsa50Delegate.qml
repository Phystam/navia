import QtQuick
import QtQuick.Controls
import QtLocation
import QtPositioning

MapItemGroup {
    //前線
    MapPolyline {
        visible: {modelData.geometry.type==="LineString" && modelData.properties.type !=="停滞前線"}
        path: {
            var linePath = []
            var coords = modelData.geometry.coordinates;
            for (var i in coords) {
                linePath.push(QtPositioning.coordinate(coords[i][1],coords[i][0]));
            }
            return linePath
        }
        line.color: {
            switch(modelData.properties.type) {
            case "寒冷前線": return "#0101FF";
            case "温暖前線": return "#FF0101";
            case "閉塞前線": return "#FE02FE";
            case "等圧線": 
                var col=modelData.properties.pressure %4 == 0 ? "#999999" : "#747474";
                return col
            default: "transparent"
            }
        }
        line.width: {
            switch(modelData.properties.type) {
            case "寒冷前線": return 3;
            case "温暖前線": return 3;
            case "閉塞前線": return 3;
            case "等圧線": 
                return modelData.properties.pressure %20 ==0 ? 2 : 1
            default: return 0
            }
        }
    }
    Repeater {
        model: modelData.properties.type ==="停滞前線" ? modelData.geometry.coordinates.length - 1 : 0
        id: rep1
        property var featureData: modelData.geometry.coordinates
        MapPolyline {
            
            path: {
                var coords = rep1.featureData;
                return [QtPositioning.coordinate(coords[index][1],     coords[index][0]),
                        QtPositioning.coordinate(coords[index + 1][1], coords[index + 1][0])]
            }
            line.color: (Math.floor(index / 10) % 2 === 0) ? "#0101FF" : "#FF0101"
            line.width: 3
        }
    }
    //低気圧・高気圧の記号
    MapQuickItem {
        visible: {
            modelData.properties.type ==="低気圧" 
            || modelData.properties.type ==="高気圧"
            || modelData.properties.type ==="低圧部"
            || modelData.properties.type ==="熱帯低気圧"
            || modelData.properties.type ==="台風"}
        coordinate: QtPositioning.coordinate(modelData.geometry.coordinates[1],modelData.geometry.coordinates[0])
        anchorPoint.x: image.width/2
        anchorPoint.y: image.width/2
        sourceItem: Image {
            id: image
            property var type: modelData.properties.type
            antialiasing: true
            source: {
                if(type==="低気圧" || type==="低圧部"){
                    console.log(type)
                    return "../materials/Low.svg";
                }
                if(type==="高気圧"){
                    return "../materials/High.svg";
                }
                if(type==="台風"){
                    return "../materials/Typhoon.svg";
                }
                if(type==="熱帯低気圧"){
                    return "../materials/TropicalLow.svg";
                }
                return "";
            }
            width: 30
            height: 30
        }
    }
    //中心気圧
    MapQuickItem {
        visible: {
            modelData.properties.type ==="低気圧" 
            || modelData.properties.type ==="高気圧"
            || modelData.properties.type ==="低圧部"
            || modelData.properties.type ==="熱帯低気圧"
            || modelData.properties.type ==="台風"} 
        coordinate: QtPositioning.coordinate(modelData.geometry.coordinates[1],modelData.geometry.coordinates[0])
        anchorPoint.x: image.width/2
        anchorPoint.y: {
            if(modelData.properties.direction<=90 || modelData.properties.direction>=270){
                return image.height/2-35
            }else{
                return image.height/2+35
            }
        }
        sourceItem: Label {
            id: pressureLabel
            text: {
                if(modelData.properties.pressure){
                    return modelData.properties.pressure;
                }else {
                    return "";
                }
            }
            font.pointSize: 12
            color: "#f7f8f8"
            style: Text.Outline
            styleColor: "#161616"
        }
    }
    //移動方向の矢印
    MapQuickItem {
        visible: {
            (modelData.properties.type ==="低気圧" 
            || modelData.properties.type ==="高気圧"
            || modelData.properties.type ==="低圧部"
            || modelData.properties.type ==="熱帯低気圧"
            || modelData.properties.type ==="台風")
            && modelData.properties.speed !=="ほとんど停滞" }
        id: arrowItem
        coordinate: QtPositioning.coordinate(modelData.geometry.coordinates[1],modelData.geometry.coordinates[0])
        anchorPoint.x: directionArrow.width/2  - 40*Math.sin(Math.PI/180*directionArrow.angle)
        anchorPoint.y: directionArrow.height/2 + 40*Math.cos(Math.PI/180*directionArrow.angle)
        sourceItem: Image {
            id: directionArrow
            property var type: modelData.properties.type
            antialiasing: true
            source: "../materials/DirectionArrow.svg"
            width: 30
            height: 40
            property int angle: {
                var speed=modelData.properties.speed;
                if( modelData.properties.direction !=="" ){
                    return Number(modelData.properties.direction)
                }else {
                    return 0
                }
            }
            transform: Rotation {
                origin.x: directionArrow.width/2
                origin.y: directionArrow.height/2
                angle: directionArrow.angle
            }
        }
    }
////
    //ほとんど停滞
    MapQuickItem {
        visible: {
            (modelData.properties.type ==="低気圧" 
            || modelData.properties.type ==="高気圧"
            || modelData.properties.type ==="低圧部"
            || modelData.properties.type ==="熱帯低気圧"
            || modelData.properties.type ==="台風")
            && (modelData.properties.speed ==="ほとんど停滞" )}
        coordinate: QtPositioning.coordinate(modelData.geometry.coordinates[1],modelData.geometry.coordinates[0])
        anchorPoint.x: -20
        anchorPoint.y: slowDirectionLabel.height/2 
        sourceItem: Label {
            id: slowDirectionLabel
            text: {
                if(modelData.properties.speed){
                    return modelData.properties.speed;
                }else {
                    return "";
                }
            }
            font.pointSize: 14
            color: "#f7f8f8"
            style: Text.Outline
            styleColor: "#161616"
        }
    }
    //その他
    MapQuickItem {
        visible: {
            (modelData.properties.type ==="低気圧" 
            || modelData.properties.type ==="高気圧"
            || modelData.properties.type ==="低圧部"
            || modelData.properties.type ==="熱帯低気圧"
            || modelData.properties.type ==="台風")
            && (modelData.properties.speed !=="ほとんど停滞" )}
        coordinate: QtPositioning.coordinate(modelData.geometry.coordinates[1],modelData.geometry.coordinates[0])
        anchorPoint.x: arrowItem.anchorPoint.x
        anchorPoint.y: {
            if (directionArrow.angle<=90 || directionArrow.angle>=270){
                return arrowItem.anchorPoint.y+20
            } else {
                return arrowItem.anchorPoint.y-20
            }
        }
        sourceItem: Label {
            text: {
                if(modelData.properties.speed==="ゆっくり"){
                    return "ゆっくり"
                }else{
                    return modelData.properties.speed+"km/h"
                }
            }
            font.pointSize: 14
            color: "#f7f8f8"
            style: Text.Outline
            styleColor: "#161616"
        }
    }
    //MapQuickItem {
    //    visible: {modelData.properties.type ==="低気圧" || modelData.properties.type ==="高気圧"}
    //    coordinate: QtPositioning.coordinate(modelData.geometry.coordinates[1],modelData.geometry.coordinates[0])
    //    anchorPoint.x: image.width/2
    //    anchorPoint.y: image.width/2
    //    sourceItem: Image {
    //        id: center
    //        property var type: modelData.properties.type
    //        source: {
    //            if(type==="低気圧" || type==="低圧部"){
    //                return "../materials/Low.svg";
    //            }
    //            if(type==="高気圧" || type==="高圧部"){
    //                return "../materials/High.svg";
    //            }
    //        }
    //        width: 30
    //        height: 30
    //    }
    //}
}
