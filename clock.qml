// clock.qml
import QtQuick
import QtQuick.Controls

// 時刻表示部分のコンポーネント
Rectangle {
    id: clockDisplay
    width: Screen.width*0.075
    height: Screen.height*0.075
    x: -10 // 左からのマージン
    y: Screen.height*0.025 // 上からのマージン
    color: "#55B2B2B2" // 半透明の黒背景 (rgba(0, 0, 0, 0.7) と同等)
    radius: 10 // 角を丸くする

    // 時刻と日付を縦に並べるためのColumn
    Column {
        anchors.centerIn: parent // 親の中央に配置
        //anchors.top: parent.top // 親の上に配置
        //anchors.left: parent.left // 親の左に配置
        width: parent.width // 親の幅に合わせる
        height: parent.height // 親の高さに合わせる
        spacing: 5 // 時刻と日付の間のスペース

        // 時刻を表示するテキスト
        Text {
            id: timeText
            style: Text.Outline // テキストにアウトラインを追加
            styleColor: "black" // アウトラインの色
            renderType: Text.NativeRendering

            text: clockApp.currentTimeStr // Pythonから渡される時刻プロパティ
            color: "white"
            font.pixelSize: Screen.height*0.03 // 時刻のフォントサイズを大きく
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignTop
            Rectangle {
                anchors.fill: parent // 親の幅と高さに合わせる
                color: "red" // 背景を透明にする
            }
        }

        // 日付を表示するテキスト
        Text {
            id: dateText
            style: Text.Outline // テキストにアウトラインを追加
            styleColor: "black" // アウトラインの色
            text: clockApp.currentDateStr // Pythonから渡される日付プロパティ
            color: "white"
            font.pixelSize: Screen.height*0.01 // 日付のフォントサイズを小さく
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
}
