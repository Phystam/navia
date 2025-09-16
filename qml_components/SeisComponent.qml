import QtQuick
import QtQuick.Controls

// 再利用可能な情報セクションコンポーネント
Rectangle {
    id: seisSection
    color: "#232427"
    radius: 3
    property var textColor: "#ffffff"
    property string dateTimeText: "2025/10/11 21:34:50"
    property string headTitleText: "三重県南東沖 深さ30km"
    property string headlineText: "aaa"
    property string bodyText: "aaa"
    property var logoListModel: null
    property bool expanded: false
    property string maxintensity: "1"
    width: parent ? parent.width : 400
    height: childrenRect.height
    
    function initInfo(){
        dateTimeText=""
        headTitleText=""
        headlineText=""
        bodyText=""
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
                    //anchors.right: magValue.left
                    //anchors.bottom: parent.bottom
                    //anchors.margins: 2
                    text: "Mj"
                }
                Text {
                    id: magValue
                    color: seisSection.textColor
                    font.bold: true
                    font.pixelSize: 30
                    //anchors.right: parent.right
                    //anchors.bottom: parent.bottom
                    //anchors.margins: 2

                    text: "2.5"
                }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    seisSection.expanded = !seisSection.expanded
                    seisInfo.expanded = false
                }
            }
        }
        Column {
            width: parent.width
            height: seisSection.expanded ? childrenRect.height : 0
            clip: true
            Behavior on height {
                NumberAnimation {
                    duration: 300
                    easing.type: Easing.InOutQuad
                }
            }
            Rectangle {
                //visible: seisSection.expanded
                width: parent.width
                height: seisSection.expanded ? 2 : 0
                color: "gray"
            }
            SeisInfoText {
                id: seisInfo
                height: seisSection.expanded ? childrenRect.height : 0
            }
        }
    }
    
}
    //    Behavior on height {
    //        NumberAnimation {
    //            duration: 300
    //            easing.type: Easing.InOutQuad
    //        }
    //    }
//
    //    Rectangle {
    //        width: parent.width
    //        height: 2
    //        color: "gray"
    //    }
    //    Text {
    //        text: seisSection.headlineText
    //        width: parent.width
    //        wrapMode: Text.WrapAnywhere
    //        visible: seisSection.headlineText != ""
    //        color: seisSection.textColor
    //    }
    //    Text {
    //        text: seisSection.bodyText
    //        width: parent.width
    //        wrapMode: Text.WrapAnywhere
    //        visible: seisSection.bodyText != ""
    //        color: seisSection.textColor
    //    }


        //Row {
        //    visible: infoSection.logoListModel && (infoSection.logoListModel.count > 0 || infoSection.headTitleText.text !=="")
        //    height: visible ? 22 : 0
        //    width: parent.width
        //    spacing: 4
        //    Repeater {
        //        model: infoSection.logoListModel
        //        Image {
        //            height: parent.height
        //            fillMode: Image.PreserveAspectFit
        //            source: model.value
        //            antialiasing: true
        //        }
        //    }
        //}