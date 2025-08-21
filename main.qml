// main.qml (Updated)
import QtQuick
import QtQuick.Window
import QtQuick.Controls

Window {
    onScreenChanged: {
        rootWindow.width = rootWindow.screen.width;
        rootWindow.height = rootWindow.screen.height;
    }
    onWidthChanged: {
        telopLoader.source = "";
        telopLoader.source = "telop.qml";
    }

    id: rootWindow
    width: Screen.width // 画面の幅に合わせる
    height: Screen.height // 画面の高さに合わせる
    visible: true
    visibility: Window.AutomaticVisibility
    title: "NAVIA"

    // 全画面オーバーレイにするための設定
    flags: Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.WindowTransparentForInput
    color: "transparent" // 背景を透明にする

    onVisibilityChanged: {
        // 画面復帰時にWindowサイズとcolorを再設定
        rootWindow.color = "transparent";
        rootWindow.width = Screen.width;
        rootWindow.height = Screen.height;
        telopLoader.source = "";
        telopLoader.source = "telop.qml";
    }

    onActiveChanged: {
        if (active) {
            // 必要なら再描画や再初期化処理
            rootWindow.width = Screen.width;
            rootWindow.height = Screen.height;
            telopLoader.source = "";
            telopLoader.source = "telop.qml";
        }
    }
    // 津波と緊急地震速報用のオブジェクト
    property Component tsunami_component: null
    property QtObject tsunami_object    : null
    property Component eew_component    : null
    property QtObject eew_object        : null
    // clock.qml コンポーネントをロードして表示
    // clock.qml は main.qml と同じディレクトリにあると仮定
    Loader {
        source: "clock.qml"
        // 親ウィンドウの左上に配置
        anchors.top: parent.top
        anchors.left: parent.left
    }

    Loader {
        id: telopLoader
        source: "telop.qml" // テロップコンポーネントをロード
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: parent.height * 0.025 // 上からのマージン
        width: parent.width * 0.9 // 親ウィンドウの90%の幅
        height: parent.height * 0.1 // 親ウィンドウの25%の高さ
    }

    // ウィンドウを移動可能にするためのMouseArea (開発用)
    //MouseArea {
    //    anchors.fill: parent
    //    // Qt.WindowTransparentForInput が設定されていると、MouseAreaは機能しないため、
    //    // 開発中は一時的に WindowTransparentForInput をコメントアウトしてください。
    //    onPressed: { mouse.accepted = true; rootWindow.startSystemMove(); }
    //}

    Component.onCompleted: {
        // 初期化処理
        telopLoader.item.init();
        // 必要に応じて他の初期化処理を追加
        mainApp.telopDataReceived.connect(onTelopReceived);
        mainApp.tsunamiReceived.connect(onTsunamiReceived);
    }
    function onTelopReceived(data,emergency) {
        console.log(emergency)
        telopLoader.item.push(data["sound_list"], data["logo_list"], data["text_list"],emergency); // ロゴとテキストを設定
    }
    function onTsunamiReceived(data) {
        telopLoader.item.push(data["sound_list"], data["logo_list"], data["text_list"],emergency); // ロゴとテキストを設定
    }

}
