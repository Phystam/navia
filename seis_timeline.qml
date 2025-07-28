import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: root
    visible: true
    width: 1200
    height: 800
    title: "地震情報タイムライン"
    color: "#1e1e1e"

    RowLayout {
        anchors.fill: parent
        spacing: 10

        // 左：日本地図（TopoJSON→パス配列をCanvasで描画）
        Rectangle {
            Layout.preferredWidth: parent.width * 0.6
            Layout.fillHeight: true
            color: "#2d2d2d"

            // 地図のズーム・ドラッグ用
            Flickable {
                id: mapFlick
                anchors.fill: parent
                contentWidth: mapCanvas.width
                contentHeight: mapCanvas.height
                interactive: true
                clip: true

                property real zoom: 1.0
                property real offsetX: 0
                property real offsetY: 0

                Canvas {
                    id: mapCanvas
                    width: 1000
                    height: 1200
                    anchors.centerIn: parent

                    property var geoPaths: [] // PythonからSVGパス配列をセット

                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();
                        ctx.save();
                        ctx.scale(mapFlick.zoom, mapFlick.zoom);
                        ctx.translate(mapFlick.offsetX, mapFlick.offsetY);
                        ctx.strokeStyle = "#cccccc";
                        ctx.lineWidth = 1.5;
                        for (var i = 0; i < geoPaths.length; ++i) {
                            ctx.beginPath();
                            ctx.moveTo(geoPaths[i][0].x, geoPaths[i][0].y);
                            for (var j = 1; j < geoPaths[i].length; ++j) {
                                ctx.lineTo(geoPaths[i][j].x, geoPaths[i][j].y);
                            }
                            ctx.closePath();
                            ctx.stroke();
                        }
                        ctx.restore();
                    }
                }

                // ズーム操作
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    property real lastX
                    property real lastY
                    onPressed: {
                        lastX = mouse.x;
                        lastY = mouse.y;
                    }
                    onPositionChanged: {
                        if (mouse.buttons & Qt.LeftButton) {
                            mapFlick.offsetX += (mouse.x - lastX) / mapFlick.zoom;
                            mapFlick.offsetY += (mouse.y - lastY) / mapFlick.zoom;
                            lastX = mouse.x;
                            lastY = mouse.y;
                            mapCanvas.requestPaint();
                        }
                    }
                    onWheel: {
                        var oldZoom = mapFlick.zoom;
                        if (wheel.angleDelta.y > 0)
                            mapFlick.zoom *= 1.1;
                        else
                            mapFlick.zoom /= 1.1;
                        mapCanvas.requestPaint();
                    }
                }
            }
        }

        // 右：タイムライン
        Rectangle {
            Layout.preferredWidth: parent.width * 0.4
            Layout.fillHeight: true
            color: "#2d2d2d"

            ListView {
                id: timelineList
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10
                verticalLayoutDirection: ListView.BottomToTop

                model: ListModel {
                    // Pythonから地震情報を追加
                }

                delegate: Rectangle {
                    width: timelineList.width
                    height: 100
                    color: "#3d3d3d"
                    radius: 5

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 5

                        Text { text: model.time; color: "white"; font.pixelSize: 14 }
                        Text { text: model.magnitude; color: "#ffd700"; font.pixelSize: 18; font.bold: true }
                        Text { text: model.location; color: "white"; font.pixelSize: 16; Layout.fillWidth: true }
                    }
                }
                ScrollBar.vertical: ScrollBar { active: true }
            }
        }
    }
}