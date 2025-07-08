import QtQuick
import QtQuick.Window
import QtQuick.Controls

Window {
    id: rootWindow
    width: Screen.width // 画面の幅に合わせる
    height: Screen.height // 画面の高さに合わせる
    visible: true
    title: "気象情報システム"

    // 全画面オーバーレイにするための設定
    flags: Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.WindowTransparentForInput
    color: "transparent" // 背景を透明にする

    // 時刻表示部分
    Rectangle {
        id: clockDisplay
        width: 200
        height: 100
        x: 20 // 左からのマージン
        y: 20 // 上からのマージン
        //color: "rgba(0, 0, 0, 0.7)" // 半透明の黒背景
        color: "#B2000000"
        radius: 10 // 角を丸くする

        // 時刻と日付を表示するテキスト
        Text {
            id: timeText
            text: clockApp.currentTime // Pythonから渡される時刻プロパティ
            anchors.centerIn: parent
            color: "white"
            font.pixelSize: 36
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            lineHeight: 1.2 // 行間を調整
        }

        // 1秒ごとにQML側で時刻を更新するタイマー（Python側でも更新しているが、QML側で表示を更新するため）
        Timer {
            interval: 1000
            running: true
            repeat: true
            onTriggered: {
                // Pythonオブジェクトのプロパティが更新されたときにQMLも更新される
                // ここでは明示的な更新処理は不要だが、QML側で何か処理をしたい場合に使える
            }
        }
    }

    // ウィンドウを移動可能にするためのMouseArea (開発用)
    MouseArea {
        anchors.fill: parent
        // Qt.WindowTransparentForInput が設定されていると、MouseAreaは機能しないため、
        // 開発中は一時的に WindowTransparentForInput をコメントアウトしてください。
        onPressed: { mouse.accepted = true; rootWindow.startSystemMove(); }
    }
}
