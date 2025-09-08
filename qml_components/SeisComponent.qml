import QtQuick
import QtQuick.Controls

// 再利用可能な情報セクションコンポーネント
Rectangle {
    id: seisSection
    color: "#232427"
    radius: 3
    property var textColor: "#ffffff"
    property string dateTimeText: "2025/10/11 21:34:50"
    property string headTitleText: "三重県南東沖"
    property string headTitleText2: "深さ30km M4.2"
    property string headlineText: "aaa"
    property string bodyText: "aaa"
    property var logoListModel: null
    property bool expanded: false
    property string maxintensity: "1"
    width: parent ? parent.width : 400
    height: seisColumn.height
    visible: headTitleText !== ""
    
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
    Row{
        id: titleRow
        spacing: 2
        Image {
            id: seisImage
            height:45*1.5
            width:40*1.5
            source: "../materials/seis"+seisSection.maxintensity+".svg"
        }
        Column {
            id: seisColumn
            spacing: 1
            width: parent.width-seisImage.width-titleRow.spacing
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
            Text {
                text: seisSection.headTitleText2
                font.pixelSize: 20
                font.bold: true
                width: parent.width
                wrapMode: Text.WrapAnywhere
                color: seisSection.textColor
            }
        }
    }

    //}

    MouseArea {
        anchors.fill: parent
        onClicked: seisSection.expanded = !seisSection.expanded
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