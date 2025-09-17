import QtQuick
import QtQuick.Controls

// 再利用可能な情報セクションコンポーネント
Rectangle {
    id: infoSection
    color: "#232427"
    radius: 3
    property var textColor: "#ffffff"
    property string dateTimeText: "2025/10/11 21:36:50"
    property string headTitleText: "震源・震度に関する情報"
    property string headlineText: "１１日２１時３４分ころ、地震がありました。"
    property string bodyText: ""
    property var logoTextModel: null
    property var logoListModel: null
    property bool expanded: false
    property var seisLogoListModel: null
    property var seisTextListModel: null
    width: parent ? parent.width : 400
    height: childrenRect.height
    visible: headTitleText !== ""
    
    function initInfo(){
        dateTimeText=""
        headTitleText=""
        headlineText=""
        bodyText=""
        logoListModel=null
        expanded=false
    }
    Column {
        id: infoColumn
        spacing: 2
        width: parent.width
        height: childrenRect.height
        visible: infoSection.visible
        Text {
            text: infoSection.dateTimeText
            font.pixelSize: 12
            font.bold: false
            color: infoSection.textColor
            visible: infoSection.visible
        }
        Text {
            text: infoSection.headTitleText
            font.pixelSize: 16
            font.bold: true
            width: parent.width
            wrapMode: Text.WrapAnywhere
            color: infoSection.textColor
            visible: infoSection.visible
        }
        Row {
            visible: infoSection.logoListModel && (infoSection.logoListModel.count > 0 || infoSection.headTitleText.text !=="")
            height: visible ? 22 : 0
            width: parent.width
            spacing: 4
            Repeater {
                model: infoSection.logoListModel
                Image {
                    height: parent.height
                    fillMode: Image.PreserveAspectFit
                    source: model.value
                    antialiasing: true
                }
            }
        }
        Column {
            width: parent.width
            height: infoSection.expanded ? childrenRect.height : 0
            clip: true

            Behavior on height {
                NumberAnimation {
                    duration: 300
                    easing.type: Easing.InOutQuad
                }
            }

            Rectangle {
                width: parent.width
                height: 1
                color: "gray"
            }
            Text {
                text: infoSection.headlineText
                width: parent.width
                wrapMode: Text.WrapAnywhere
                visible: infoSection.headlineText != ""
                color: infoSection.textColor
            }
            Text {
                text: infoSection.bodyText
                width: parent.width
                wrapMode: Text.WrapAnywhere
                visible: infoSection.bodyText != ""
                color: infoSection.textColor
            }
            //Repeater {
            //    
            //}
        }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: infoSection.expanded = !infoSection.expanded
    }
}