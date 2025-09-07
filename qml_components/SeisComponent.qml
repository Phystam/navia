import QtQuick
import QtQuick.Controls

// 再利用可能な情報セクションコンポーネント
Rectangle {
    id: seisSection
    color: "#232427"
    radius: 3
    property var textColor: "#ffffff"
    property string dateTimeText: ""
    property string headTitleText: ""
    property string headlineText: ""
    property string bodyText: ""
    property var logoListModel: null
    property bool expanded: false
    width: parent ? parent.width : 400
    height: infoColumn.height
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
                height: 2
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
        }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: infoSection.expanded = !infoSection.expanded
    }
}