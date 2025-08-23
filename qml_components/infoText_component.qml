import QtQuick
import QtQuick.Controls

// 再利用可能な情報セクションコンポーネント
Rectangle {
    id: infoSection
    color: "transparent"
    property string dateTimeText: ""
    property string headTitleText: ""
    property string headlineText: ""
    property string bodyText: ""
    property var logoListModel: null
    width: parent ? parent.width : 400
    height: infoColumn.height
    visible: headTitleText !== ""
    //Rectangle{
    //    anchors.fill: parent
        border.color:"blue"
        border.width: 1
    //    color: "transparent"
    //}
    Column {
        id: infoColumn
        spacing: 2
        width: parent.width
        visible: infoSection.visible
        Text {
            text: infoSection.dateTimeText
            font.pixelSize: 12
            font.bold: false
            visible: infoSection.visible
        }
        Text {
            text: infoSection.headTitleText
            font.pixelSize: 16
            font.bold: true
            width: parent.width
            wrapMode: Text.WrapAnywhere
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
        Rectangle {
            width: parent.width
            height: 2
            color: "gray"
            visible: infoSection.visible
        }
        Text {
            text: infoSection.headlineText
            width: parent.width
            wrapMode: Text.WrapAnywhere
            visible: infoSection.visible && infoSection.headlineText != ""
        }
        Text {
            text: infoSection.bodyText
            width: parent.width
            wrapMode: Text.WrapAnywhere
            visible: infoSection.visible && infoSection.bodyText != ""
        }
    }
}