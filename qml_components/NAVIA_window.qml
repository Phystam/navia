import QtQuick
import QtQuick.Controls
import QtLocation
import QtPositioning
Window {
    id: naviaWindow
    width: 1200
    height: 800
    visible: true // 初期状態では非表示
    title: "NAVIA情報"
    property string currentDir: mainApp.getCurrentDir()
    // 地図コンポーネント (GeoJSONポリゴンのみ表示)
    Component.onCompleted: {
        // 必要に応じて他の初期化処理を追加
        timelineManager.meteStatusChanged.connect(onStatusChanged);
    }
    ListModel {
        id: logoListModel_VPWW54
    }
    ListModel {
        id: logoListModel_VXWW50
    }

    function getColorByWarningLevel(level) {
        switch (level) {
            case 0: return "#c8c8cb"; // 平常
            case 1: return "#ffffff"; // レベル1・早期注意情報
            case 2: return "#f2e700"; // レベル2・注意報
            case 3: return "#ff2800"; // レベル3・警報
            case 4: return "#aa00aa"; // レベル4・その他の特別警報・危険警報・土砂災害警戒情報等
            case 5: return "#0c000c"; // レベル5・大雨特別警報
            default: return "#c8c8cb";
        }
    }

    function onStatusChanged() {
        //console.log("statuschanged: received")
        //表示されているMapItemViewのみを強制的に再描画する
        if (pref.model.length > 0) {
            //mapComponent.mapgroup.getColorForItem(pref_miv.model)
            pref_miv.model=[]; pref_miv.model = pref.model[0].data;
        }
        if (class10.model.length > 0) {
            //mapComponent.mapgroup.getColorForItem(class10_miv.model)
            class10_miv.model=[]; class10_miv.model = class10.model[0].data;
        }
        if (class15.model.length > 0) {
            //mapComponent.mapgroup.getColorForItem(class15_miv.model)
            class15_miv.model=[]; class15_miv.model = class15.model[0].data;
        }
        if (class20.model.length > 0) {
            //mapComponent.mapgroup.getColorForItem(class20_miv.model)
            class20_miv.model=[]; class20_miv.model = class20.model[0].data;
        }
    }


    function handleRegionClick(hierarchy, code, name) {
        // VPWW54 気象警報用
        var codes = timelineManager.getMeteWarningCode(hierarchy, code);
        var pref = timelineManager.getPrefName(hierarchy, code);
        if( name==pref){
            infoTitle.text = pref;
        }else{
            infoTitle.text = pref + " " + name; // Use getMeteWarningName for region name
        }
        logoListModel_VPWW54.clear()
        logoListModel_VXWW50.clear()
        if (codes.length > 0) {

            headlineText.text = timelineManager.getHeadlineText(hierarchy,code);
            infoHeadTitle.text = timelineManager.getTitle(hierarchy,code);
            var dt = timelineManager.getUpdated(hierarchy,code);
            if (dt=="2000/01/01 00:00:00"){
                infoDateTime.text = ""
            }else{
                infoDateTime.text = timelineManager.getUpdated(hierarchy,code);
            }
            var logolist=timelineManager.getMeteWarningLogoPath(hierarchy,code);
            for (var i=0;i<logolist.length;i++){
                logoListModel_VPWW54.append({"value":logolist[i]}); // Load SVG based on code
            }   
        } else {
            infoTitle.text = "No warnings";
            infoHeadline.text = "";
        }
        // VXWW50 土砂災害警戒情報用
        var codes_VXWW50 = timelineManager.getVXWW50WarningCode(hierarchy, code);
        if (codes_VXWW50.length > 0) {
            headlineText_VXWW50.text = timelineManager.getVXWW50HeadlineText(hierarchy,code);
            infoHeadTitle_VXWW50.text = timelineManager.getVXWW50Title(hierarchy,code);
            var dt = timelineManager.getUpdated(hierarchy,code);
            if (dt=="2000/01/01 00:00:00"){
                infoDateTime_VXWW50.text = ""
                infoImage_VXWW50.source = "";
            }else{
                infoDateTime_VXWW50.text = timelineManager.getVXWW50Updated(hierarchy,code);
            }
            var logolist_VXWW50=timelineManager.getVXWW50LogoPath(hierarchy,code);
            for (var i=0;i<logolist_VXWW50.length;i++){
                logoListModel_VXWW50.append({"value":logolist_VXWW50[i]}); // Load SVG based on code
            }   
        } else {
            infoTitle_VXWW50.text = "No warnings";
            infoHeadline_VXWW50.text = "";
        }
    }

    Item {
        id: mapComponent
        anchors.left: parent.left
        anchors.right: infoPanel.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: 5
        
        // GeoJSONポリゴンを描画するコンポーネント
        Rectangle {
            anchors.fill: parent
            color: "lightblue"
            border.color: "gray"
            border.width: 1
            
            Map {
                id:view
                anchors.fill:parent
                plugin: Plugin { name: "itemsoverlay" }
                //plugin: Plugin { name: "osm" }
                center: QtPositioning.coordinate(35,135)
                zoomLevel:5
                color:"transparent"
                antialiasing: true
                
                GeoJsonData {
                    id: pref
                    //sourceUrl: "file:///f:/navia/geo/府県予報区等.geojson"
                    sourceUrl: "file:///"+naviaWindow.currentDir+"/geo/府県予報区等.geojson"
                }
                GeoJsonData {
                    id: class10
                    sourceUrl: "file:///"+naviaWindow.currentDir+"/geo/一次細分区域等.geojson"
                }
                GeoJsonData {
                    id: class15
                    sourceUrl: "file:///"+naviaWindow.currentDir+"/geo/市町村等をまとめた地域等.geojson"
                }
                GeoJsonData {
                    id: class20
                    sourceUrl: "file:///"+naviaWindow.currentDir+"/geo/市町村等（気象警報等）.geojson"
                }
                GeoJsonData {
                    id: tsunami
                    sourceUrl: "file:///"+naviaWindow.currentDir+"/geo/津波予報区.geojson"
                }
                GeoJsonData {
                    id: world
                    sourceUrl: "file:///"+naviaWindow.currentDir+"/geo/world.geojson"
                }
                WheelHandler {
                    id: wheel
                    acceptedDevices: Qt.platform.pluginName === "cocoa" || Qt.platform.pluginName === "wayland"
                                     ? PointerDevice.Mouse | PointerDevice.TouchPad
                                     : PointerDevice.Mouse
                    rotationScale: 1/120
                    property: "zoomLevel"
                }
                DragHandler {
                    id: drag
                    target: null
                    onTranslationChanged: (delta) => view.pan(-delta.x, -delta.y)
                }
                
                Component {
                    id: mapDelegate
                    MapItemGroup {
                        id: mapgroup
                        required property int index
                        property int item_index: index
                        property var item_model: mapgroup.parent.model
                        property string hierarchy: mapgroup.parent.hierarchy
                        property var polys: showMap(item_model, index)
                        Repeater {
                            model: polys
                            delegate: MapPolygon {
                                id: polygon
                                path: modelData
                                color: getColorForItem(item_model)
                                border.width: 1
                                border.color: "#111111"
                                antialiasing: true
                                MouseArea {
                                    id: mouseArea
                                    anchors.fill: parent
                                    propagateComposedEvents: true
                                    hoverEnabled: true
                                    onClicked: (mouse) => {
                                        // マウス座標を地図の地理座標に変換
                                        var pointInMap = mouseArea.mapToItem(view, mouse.x, mouse.y);
                                        var coordinate = view.toCoordinate(pointInMap, false);

                                        if (isPointInPolygon(coordinate, modelData)) {
                                            mouse.accepted = true
                                            var feature = item_model[item_index];
                                            handleRegionClick(hierarchy, feature.properties.code, feature.properties.name) // Example hierarchy and code
                                        } else {
                                            mouse.accepted = false
                                        }
                                    }
                                }
                                function isPointInPolygon(point, polygon) {
                                    let x = point.longitude;
                                    let y = point.latitude;
                                    let inside = false;

                                    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
                                        let xi = polygon[i].longitude, yi = polygon[i].latitude;
                                        let xj = polygon[j].longitude, yj = polygon[j].latitude;

                                        let intersect = ((yi > y) !== (yj > y)) &&
                                            (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
                                        if (intersect) inside = !inside;
                                    }

                                    return inside;
                                }
                            }
                        }
                        function getColorForItem(model){
                            var feature = item_model[item_index];
                            if (feature && feature.properties) {
                                var code = feature.properties.code;
                                var level = timelineManager.getMeteWarningLevel(hierarchy, code);
                                return getColorByWarningLevel(level);
                            } else {
                                return "#c8c8cb";
                            }
                        }
                        function showMap(model, j) {
                            var paths = [];
                            var path = [];
                            // console.log("index="+ j +", areaname: " + model[j].properties.name)
                            if (model[j].type == "Polygon") {
                                var c = model[j].data.perimeter;
                                for (var i = 0; i < c.length; i++) {
                                    path.push(QtPositioning.coordinate(c[i].latitude, c[i].longitude));
                                }
                                paths.push(path);
                            }
                            if (model[j].type == "MultiPolygon") {
                                var polygons = model[j].data;
                                for (var k = 0; k < polygons.length; k++) {
                                    var c = model[j].data[k].data.perimeter;
                                    for (var i = 0; i < c.length; i++) {
                                        path.push(QtPositioning.coordinate(c[i].latitude, c[i].longitude));
                                    }
                                    paths.push(path);
                                    path = [];
                                }
                            }
                            return paths;
                        }
                    }
                }

                MapItemView {
                    id: pref_miv
                    model: pref.model.length > 0 ? pref.model[0].data : []
                    delegate: mapDelegate
                    visible: view.zoomLevel < 6
                    property string hierarchy: "pref"
                }
                MapItemView {
                    id: class10_miv
                    model: class10.model.length >0 ? class10.model[0].data : []
                    delegate: mapDelegate
                    visible: view.zoomLevel >= 6 && view.zoomLevel < 7
                    property string hierarchy: "class10"
                }
                MapItemView {
                    id: class15_miv
                    model: class15.model.length >0 ? class15.model[0].data : []
                    delegate: mapDelegate
                    visible: view.zoomLevel >= 7 && view.zoomLevel < 9
                    property string hierarchy: "class15"
                }
                MapItemView {
                    id: class20_miv
                    model: class20.model.length >0 ? class20.model[0].data : []
                    delegate: mapDelegate
                    visible: view.zoomLevel >= 9
                    property string hierarchy: "class20"
                }

                MapItemView{
                    id: miv_world
                    model: world.model[0].data
                    delegate: MapItemGroup{ 
                        id: mapgroup_world
                        required property int index
                        property int item_index: index
                        property var polys: showMap(miv_world.model,index)
                        Repeater{
                            model: polys
                            delegate: MapPolygon{
                                id: polygon_world
                                path: modelData
                                color: "#aaaaaa"
                                border.width:1
                                border.color:"#222222"
                                antialiasing: true
                            }
                        }
                        function showMap(model,j){
                            var paths=[];
                            var path=[];
                            if(model[j].type=="Polygon"){
                                var c=model[j].data.perimeter;
                                for (var i=0;i<c.length;i++){
                                    path.push(QtPositioning.coordinate(c[i].latitude,c[i].longitude));
                                }
                                paths.push(path);
                                }
                                if(model[j].type=="MultiPolygon"){
                                var polygons=model[j].data;
                                for(var k=0;k<polygons.length;k++){
                                    var c=polygons[k].data.perimeter;
                                    for (var i=0;i<c.length;i++){
                                    path.push(QtPositioning.coordinate(c[i].latitude,c[i].longitude));
                                    }
                                    paths.push(path);
                                    path=[];
                                }
                            }
                            return paths;
                        }
                    }
                }
                //MapItemView{
                //    id: miv2
                //    model: tsunami.model[0].data
                //    delegate: MapItemGroup{ 
                //        id: mapgroup2
                //        required property int index
                //        property var polys: showTsunami(miv2.model,index)
                //        property var col: tsunamiLineColor(miv2.model,index)
                //        property var wid: tsunamiLineWidth(miv2.model,index)
                //        Repeater{
                //            model: polys
                //            delegate: MapPolyline{
                //                path: modelData
                //                line.color: col
                //                line.width: wid
                //            }
                //        }
                //        function showTsunami(model,j){
                //            var paths=[];
                //            var path=[];
                //            //print(Object.entries(tsunami.model[0].data[0].type))
                //            //print(Object.entries(model[j].properties.code))
                //            //print(tsunamiWarningCodes[0])
                //            if(model[j].type=="LineString"){
                //            
                //            var c=model[j].data.path;
                //            for (var i=0;i<c.length;i++){
                //                path.push(QtPositioning.coordinate(c[i].latitude,c[i].longitude));
                //            }
                //            paths.push(path);
                //            }
                //            if(model[j].type=="MultiLineString"){
                //                var polys=model[j].data;
                //                for(var k=0;k<polys.length;k++){
                //                    var c=model[j].data[k].data.path;
                //                    for (var i=0;i<c.length;i++){
                //                        path.push(QtPositioning.coordinate(c[i].latitude,c[i].longitude));
                //                    }
                //                    paths.push(path);
                //                    path=[];
                //                }
                //            }
                //            return paths;
                //        }
                //        function tsunamiLineColor(model,j){
                //            //print(Object.entries(tsunami.model[0].data[0].type))
                //            tsunamiWarningCodes="61"
                //            var color="black"
                //            //print(typeof model[j].properties.code);
                //            //print(typeof tsunamiWarningCodes);
                //            if(tsunamiWarningCodes.includes(model[j].properties.code)){
                //                color="#F30000";
                //            }
                //            if(bigtsunamiWarningCodes.includes(model[j].properties.code)){
                //                color="#C800FF";
                //            }
                //            if(tsunamiCautionCodes.includes(model[j].properties.code)){
                //                color="#F2E700";
                //            }
                //            if(tsunamiInfoCodes.includes(model[j].properties.code)){
                //                color="#F2F2FF";
                //            }
                //            return color;
                //        }
                //        function tsunamiLineWidth(model,j){
                //            tsunamiWarningCodes="61"
                //            //print(Object.entries(tsunami.model[0].data[0].type))
                //            var width=1;
                //            //print(typeof model[j].properties.code);
                //            //print(typeof tsunamiWarningCodes);
                //            if(tsunamiWarningCodes.includes(model[j].properties.code)){
                //                width=2;
                //            }
                //            if(bigtsunamiWarningCodes.includes(model[j].properties.code)){
                //                width=4;
                //            }
                //            if(tsunamiCautionCodes.includes(model[j].properties.code)){
                //                width=2;
                //            }
                //            if(tsunamiInfoCodes.includes(model[j].properties.code)){
                //                width=1;
                //            }
                //            return width;
                //        }
                //    }
                //}
                
                
            }
        }
    }

    // 情報パネル
    Item {
        id: infoPanel
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 350
        anchors.margins: 5
        
        // 情報表示用のコンテナ
        Rectangle {
            anchors.fill: parent
            color: "#f0f0f0"
            border.color: "gray"
            border.width: 1
            
            Column {
                anchors.fill: parent
                anchors.margins: 5
                spacing: 5
                Rectangle{
                    //anchors.top: parent.top
                    //anchors.left: parent.left
                    color: "#bafff9ff"
                    width: parent.width
                    height: 24
                    Text {
                        id: infoTitle
                        //anchors.fill:parent
                        text: "地域名"
                        font.pixelSize: 18
                        font.bold: true
                    }
                }
                //土砂災害警戒情報用
                Column{
                    spacing: 2
                    visible: {
                        infoHeadTitle_VXWW50.text != ""
                    }
                    width: parent.width
                    Text {
                        id: infoDateTime_VXWW50
                        text: ""
                        font.pixelSize: 12
                        font.bold: false
                    }
                    Text {
                        id: infoHeadTitle_VXWW50
                        text: ""
                        font.pixelSize: 16
                        font.bold: true
                    }
                    Row{
                        height: {
                            infoHeadTitle_VXWW50.text == "" ? 0 : 22
                        }
                        width: parent.width
                        id: logo_VXWW50
                        spacing:4
                        Repeater {
                            model: logoListModel_VXWW50
                            Image {
                                height:parent.height
                                fillMode:Image.PreserveAspectFit
                                source: model.value
                                antialiasing: true
                            }
                        }
                    }
                    //横線
                    Rectangle {
                        width: parent.width
                        height: 2
                        color: "gray"
                        visible: { 
                            infoHeadTitle_VXWW50.text != "" 
                        }
                    }
                    Text {
                        id: headlineText_VXWW50
                        width: parent.width
                        text: ""
                        wrapMode: TextEdit.Wrap
                    }
                }
                //気象警報用
                Column{
                    spacing:{
                        infoHeadTitle.text == "" ? 0 : 2
                    }
                    width: parent.width
                    Text {
                        id: infoDateTime
                        text: ""
                        font.pixelSize: 12
                        font.bold: false
                    }
                    Text {
                        id: infoHeadTitle
                        text: ""
                        font.pixelSize: 16
                        font.bold: true
                    }
                    Row{
                        height: {
                            infoHeadTitle.text == "" ? 0 : 22
                        }
                        width: parent.width
                        id: logoA
                        spacing:4
                        Repeater {
                            model: logoListModel_VPWW54
                            Image {
                                height:parent.height
                                fillMode:Image.PreserveAspectFit
                                source: model.value
                                antialiasing: true
                            }
                        }
                    }
                    //横線
                    Rectangle {
                        width: parent.width
                        height: 2
                        color: "gray"
                        visible: { 
                            infoHeadTitle.text != "" 
                        }
                    }
                    Text {
                        id: headlineText
                        width: parent.width
                        text: ""
                        wrapMode: TextEdit.Wrap
                    }
                }

            }
        }
    }
}