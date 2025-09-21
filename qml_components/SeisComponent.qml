import QtQuick
import QtQuick.Controls

// 再利用可能な情報セクションコンポーネント
Rectangle {
    id: seisSection
    color: "#232427"
    radius: 3
    property var textColor: "#ffffff"
    property string eventID: ""
    property string dateTimeText: "2025/10/11 21:34:50"
    property string headTitleText: "三重県南東沖 深さ30km"
    property string magUnitText: "Mj"
    property string magText: "3.0"
    property var logoListModel: null
    property bool expanded: false
    property string maxintensity: "1"
    width: parent ? parent.width : 400
    height: childrenRect.height
    
    function initInfo(){
        dateTimeText=""
        headTitleText=""
        headlineText=""
        magUnitText="Mj"
        magText=""
        logoListModel=null
        expanded=false
    }
    //Column {
    //    //width: parent.width
    //    //height: seisSection.expanded ? childrenRect.height : 0
    //    //clip: true
    Column {
        id: seisColumn
        spacing: 0
        width: parent.width
        height: childrenRect.height
        clip: true
        Item {
            width: parent.width
            height: childrenRect.height
            Row{
                id: titleRow
                spacing: 2
                width: parent.width
                height: childrenRect.height
                Image {
                    id: seisImage
                    height:titleColumn.height
                    width:height*0.8
                    source: "../materials/seis"+seisSection.maxintensity+".svg"
                }
                Column {
                    id: titleColumn
                    spacing: 1
                    width: parent.width - seisImage.width - titleRow.spacing*4 - magUnit.width - magValue.width
                    Text {
                        text: seisSection.dateTimeText
                        font.pixelSize: 12
                        font.bold: false
                        color: seisSection.textColor
                    }
                    Text {
                        text: seisSection.headTitleText
                        font.pixelSize: 20
                        font.bold: true
                        width: parent.width
                        wrapMode: Text.WrapAnywhere
                        color: seisSection.textColor
                    }
                }
                Text {
                    id: magUnit
                    color: seisSection.textColor
                    font.pixelSize: 18
                    text: magUnitText
                }
                Text {
                    id: magValue
                    color: seisSection.textColor
                    font.bold: true
                    font.pixelSize: 30
                    text: magText
                }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    seisSection.expanded = !seisSection.expanded
                    //seisInfoColumn.expanded = false
                }
            }
        }
        Rectangle {
                width: parent.width
                height: seisSection.expanded ? 2 : 0
                color: "gray"
        }
        Column {
            id: seisInfoColumn
            width: parent.width
            height: seisSection.expanded ? childrenRect.height : 0
            clip: true
            Behavior on height {
                NumberAnimation {
                    duration: 300
                    easing.type: Easing.InOutQuad
                }
            }
            Repeater {
                model: timelineManager.getSeisEventIDIDList(eventID)
                delegate: SeisInfoText {
                    required property var modelData
                    infoID: modelData
                    dateTimeText: timelineManager.getSeisTimelineReportTime(modelData)
                    headTitleText: timelineManager.getSeisTimelineData(modelData,"head_title")
                    headlineText: timelineManager.getSeisTimelineData(modelData,"headline_text")+timelineManager.getSeisTimelineData(modelData,"forecast_comment")
                    height: seisSection.expanded ? childrenRect.height : 0
                }
            }
        }
    }
}