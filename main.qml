// main.qml (Updated)
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

    // clock.qml コンポーネントをロードして表示
    // clock.qml は main.qml と同じディレクトリにあると仮定
    Loader {
        source: "clock.qml"
        // 親ウィンドウの左上に配置
        anchors.top: parent.top
        anchors.left: parent.left
        //anchors.fill: parent // 親ウィンドウ全体に広げる（clock.qml内で位置が指定されているため、これは必須ではないが、コンポーネントの配置を柔軟にする）
    }

    // ウィンドウを移動可能にするためのMouseArea (開発用)
    MouseArea {
        anchors.fill: parent
        // Qt.WindowTransparentForInput が設定されていると、MouseAreaは機能しないため、
        // 開発中は一時的に WindowTransparentForInput をコメントアウトしてください。
        onPressed: { mouse.accepted = true; rootWindow.startSystemMove(); }
    }
}
