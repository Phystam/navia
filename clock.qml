// clock.qml
import QtQuick
import QtQuick.Controls

// 時刻表示部分のコンポーネント
Rectangle {
    id: clockDisplay
    width: Screen.width*0.075
    height: Screen.height*0.075
    x: 0 // 左からのマージン
    y: Screen.height*0.025 // 上からのマージン
    color: "#80808080" // 半透明の黒背景 (rgba(0, 0, 0, 0.7) と同等)
    // 角を丸くする
    topRightRadius:height*0.1
    bottomRightRadius:height*0.1
    Text {
            id: timeText
            anchors.top: clockDisplay.top
            anchors.horizontalCenter: clockDisplay.horizontalCenter
            anchors.topMargin: clockDisplay.height*0.05
            font.family: "Neue Haas Grotesk"
            style: Text.Outline // テキストにアウトラインを追加
            styleColor: "black" // アウトラインの色
            renderType: Text.NativeRendering
            
            text: clockApp.currentTimeStr // Pythonから渡される時刻プロパティ
            color: "white"
            font.pixelSize: Screen.height*0.03 // 時刻のフォントサイズを大きく
            //font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignTop
    }
    // 日付を表示するテキスト
    Text {
        id: dateText
        anchors.bottom: clockDisplay.bottom
        anchors.horizontalCenter: clockDisplay.horizontalCenter
        anchors.bottomMargin: clockDisplay.height*0.1
        style: Text.Outline // テキストにアウトラインを追加
        styleColor: "black" // アウトラインの色
        text: clockApp.currentDateStr // Pythonから渡される日付プロパティ
        color: "white"
        font.family: "Neue Haas Grotesk"
        font.pixelSize: Screen.height*0.0125 // 日付のフォントサイズを小さく
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    
}