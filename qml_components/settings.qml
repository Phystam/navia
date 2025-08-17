// qml_components/settings.qml
import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Basic
Window {
    id: settingsWindow
    width: 800
    height: 600
    visible: true // 初期状態では非表示
    title: "設定"
    modality: Qt.ApplicationModal // 他のウィンドウ操作をブロック
    flags: Qt.Window | Qt.WindowStaysOnTopHint // 通常のウィンドウとして表示し、常に最前面に

    // 設定マネージャーへの参照 (main.pyから設定される)
    property var settingsManager: null

    // 現在表示している設定パネルのインデックス
    property int currentPanelIndex: 0

    // OKボタンが押されたときに呼ばれるシグナル
    signal settingsApplied()

    Rectangle {
        anchors.fill: parent
        color: "#222222" // 暗めの背景色

        RowLayout {
            anchors.fill: parent
            spacing: 10
            //padding: 10

            // 左側のメニューパネル
            Rectangle {
                Layout.preferredWidth: 150
                Layout.fillHeight: true
                color: "#333333"
                radius: 5

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 5
                    //padding: 10

                    Button {
                        text: "全般"
                        Layout.fillWidth: true
                        onClicked: settingsWindow.currentPanelIndex = 0
                        background: Rectangle { color: settingsWindow.currentPanelIndex === 0 ? "#555555" : "#444444"; radius: 5 }
                        contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 18; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                    Button {
                        text: "気象"
                        Layout.fillWidth: true
                        onClicked: settingsWindow.currentPanelIndex = 1
                        background: Rectangle { color: settingsWindow.currentPanelIndex === 1 ? "#555555" : "#444444"; radius: 5 }
                        contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 18; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                    Button {
                        text: "地震"
                        Layout.fillWidth: true
                        onClicked: settingsWindow.currentPanelIndex = 2
                        background: Rectangle { color: settingsWindow.currentPanelIndex === 2 ? "#555555" : "#444444"; radius: 5 }
                        contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 18; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                    Button {
                        text: "火山"
                        Layout.fillWidth: true
                        onClicked: settingsWindow.currentPanelIndex = 3
                        background: Rectangle { color: settingsWindow.currentPanelIndex === 3 ? "#555555" : "#444444"; radius: 5 }
                        contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 18; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                    // 他のメニュー項目もここに追加
                }
            }

            // 右側のコンテンツパネル (StackLayoutで切り替え)
            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: settingsWindow.currentPanelIndex

                // パネル 0: 全般設定
                Rectangle {
                    color: "#444444"
                    radius: 5
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10
                        //padding: 20
                        Label { text: "全般設定"; color: "white"; font.pixelSize: 24; Layout.alignment: Qt.AlignHCenter }
                        // ここに全般設定項目を追加
                        RowLayout {
                            Label { text: "データ保持期間 (日):"; color: "white"; font.pixelSize: 18 }
                            TextField {
                                Layout.fillWidth: true
                                text: settingsWindow.settingsManager.settings.general.data_retention_days
                                validator: IntValidator { bottom: 1 }
                                onEditingFinished: settingsWindow.settingsManager.updateNumberSetting("general", "data_retention_days", parseInt(text))
                            }
                        }
                    }
                }

                // パネル 1: 気象設定
                Rectangle {
                    color: "#444444"
                    radius: 5
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10
                        //padding: 20
                        Label { text: "気象設定"; color: "white"; font.pixelSize: 24; Layout.alignment: Qt.AlignHCenter }

                        Label { text: "通知する気象台 (注意報以上):"; color: "white"; font.pixelSize: 18 }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Repeater {
                                model: Object.keys(settingsWindow.settingsManager.settings.meteorology.notify_observatories_warning)
                                CheckBox {
                                    text: modelData
                                    checked: settingsWindow.settingsManager.settings.meteorology.notify_observatories_warning[modelData]
                                    onCheckedChanged: settingsWindow.settingsManager.updateBooleanSetting("meteorology", "notify_observatories_warning", modelData, checked)
                                    contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 16 }
                                    indicator: Rectangle { width: 20; height: 20; radius: 3; border.color: "white"; color: parent.checked ? "green" : "transparent" }
                                }
                            }
                        }

                        Label { text: "通知する気象台 (警報以上):"; color: "white"; font.pixelSize: 18; Layout.topMargin: 15 }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Repeater {
                                model: Object.keys(settingsWindow.settingsManager.settings.meteorology.notify_observatories_alert)
                                CheckBox {
                                    text: modelData
                                    checked: settingsWindow.settingsManager.settings.meteorology.notify_observatories_alert[modelData]
                                    onCheckedChanged: settingsWindow.settingsManager.updateBooleanSetting("meteorology", "notify_observatories_alert", modelData, checked)
                                    contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 16 }
                                    indicator: Rectangle { width: 20; height: 20; radius: 3; border.color: "white"; color: parent.checked ? "green" : "transparent" }
                                }
                            }
                        }
                        
                        Label { text: "地域区分:"; color: "white"; font.pixelSize: 18; Layout.topMargin: 15 }
                        ComboBox {
                            Layout.fillWidth: true
                            model: ["都道府県", "細分区域", "市町村等"] // 地域区分の選択肢
                            currentIndex: model.indexOf(settingsWindow.settingsManager.settings.meteorology.display_region_level)
                            onActivated: settingsWindow.settingsManager.updateStringSetting("meteorology", "display_region_level", model[currentIndex])
                            contentItem: Text { text: parent.displayText; color: "white"; font.pixelSize: 16 }
                            //indicator: Canvas {
                            //    id: arrow
                            //    width: 12
                            //    height: 8
                            //    context.clearRect(0, 0, arrow.width, arrow.height);
                            //    context.beginPath();
                            //    context.moveTo(0, 0);
                            //    context.lineTo(arrow.width / 2, arrow.height);
                            //    context.lineTo(arrow.width, 0);
                            //    context.closePath();
                            //    context.fill();
                            //}
                            background: Rectangle { color: "#555555"; radius: 3; border.color: "#777777" }
                            popup: Popup {
                                implicitWidth: parent.width
                                implicitHeight: contentItem.implicitHeight
                                contentItem: ListView {
                                    implicitHeight: contentHeight
                                    model: parent.parent.model
                                    delegate: ItemDelegate {
                                        text: modelData
                                        width: parent.width
                                        onClicked: function() {
                                            parent.parent.close(); 
                                            parent.parent.parent.currentIndex = index;
                                        }
                                        contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 16 }
                                    }
                                }
                            }
                        }
                    }
                }

                // パネル 2: 地震設定
                Rectangle {
                    color: "#444444"
                    radius: 5
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10
                        //padding: 20
                        Label { text: "地震設定"; color: "white"; font.pixelSize: 24; Layout.alignment: Qt.AlignHCenter }

                        Label { text: "通知する地域:"; color: "white"; font.pixelSize: 18 }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Repeater {
                                model: Object.keys(settingsManager.settings.seismology.notify_regions)
                                CheckBox {
                                    text: modelData
                                    checked: settingsWindow.settingsManager.settings.seismology.notify_regions[modelData]
                                    onCheckedChanged: settingsWindow.settingsManager.updateBooleanSetting("seismology", "notify_regions", modelData, checked)
                                    contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 16 }
                                    indicator: Rectangle { width: 20; height: 20; radius: 3; border.color: "white"; color: parent.checked ? "green" : "transparent" }
                                }
                            }
                        }

                        Label { text: "最小マグニチュード:"; color: "white"; font.pixelSize: 18; Layout.topMargin: 15 }
                        TextField {
                            Layout.fillWidth: true
                            text: settingsWindow.settingsManager.settings.seismology.min_magnitude
                            validator: DoubleValidator { bottom: 0.0; decimals: 1 }
                            onEditingFinished: settingsWindow.settingsManager.updateNumberSetting("seismology", "min_magnitude", parseFloat(text))
                        }
                    }
                }

                // パネル 3: 火山設定
                Rectangle {
                    color: "#444444"
                    radius: 5
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10
                        //padding: 20
                        Label { text: "火山設定"; color: "white"; font.pixelSize: 24; Layout.alignment: Qt.AlignHCenter }

                        Label { text: "通知する火山:"; color: "white"; font.pixelSize: 18 }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Repeater {
                                model: Object.keys(settingsManager.settings.volcanology.notify_volcanoes)
                                CheckBox {
                                    text: modelData
                                    checked: settingsWindow.settingsManager.settings.volcanology.notify_volcanoes[modelData]
                                    onCheckedChanged: settingsWindow.settingsManager.updateBooleanSetting("volcanology", "notify_volcanoes", modelData, checked)
                                    contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 16 }
                                    indicator: Rectangle { width: 20; height: 20; radius: 3; border.color: "white"; color: parent.checked ? "green" : "transparent" }
                                }
                            }
                        }
                    }
                }
            }
        }

        // OKボタン
        Button {
            id: okButton
            text: "OK"
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: 20
            anchors.bottomMargin: 20
            width: 80
            height: 40
            onClicked: {
                settingsWindow.settingsManager.savesettings; // 設定を保存
                settingsWindow.settingsApplied(); // シグナルを発行
                settingsWindow.hide(); // ウィンドウを閉じる
            }
            background: Rectangle {
                color: "#007bff" // 青色の背景
                radius: 5
            }
            contentItem: Text {
                text: parent.text
                color: "white"
                font.pixelSize: 18
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    // settingsManagerのsettingsChangedシグナルを監視し、UIを更新（必要に応じて）
    Connections {
        target: settingsWindow.settingsManager
        function onSettingsChanged() {
            // 設定が変更されたら、UIを強制的に再評価する
            // 例えば、Repeaterのモデルをリフレッシュするなど
            // 現状のRepeaterはObject.keys()を使っているので、自動的に更新されるはずだが、
            // 複雑なUIでは明示的な更新が必要な場合がある
            console.log("QML: Settings updated from Python.");
        }
    }
}