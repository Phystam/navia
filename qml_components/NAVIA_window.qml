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
    ListModel {
        id: logoListModel_VPHW51
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
        var pref = timelineManager.getPrefName(hierarchy, code);
        if( name === pref || name === "鹿児島県（奄美地方除く）"){
            infoTitle.text = name;
        }else{
            infoTitle.text = pref + " " + name;
        }
        logoListModel_VPWW54.clear()
        logoListModel_VXWW50.clear()
        logoListModel_VPHW51.clear()

        // VPWW54 気象警報用
        if (infoLoader_VPWW54.item) {
            var codes_VPWW54 = timelineManager.getMeteWarningCode(hierarchy, code);
            if (codes_VPWW54.length > 0) {
                infoLoader_VPWW54.item.headlineText = timelineManager.getHeadlineText(hierarchy,code);
                infoLoader_VPWW54.item.headTitleText = timelineManager.getTitle(hierarchy,code);
                var dt_VPWW54 = timelineManager.getUpdated(hierarchy,code);
                infoLoader_VPWW54.item.dateTimeText = (dt_VPWW54 === "2000/01/01 00:00:00") ? "" : dt_VPWW54;
                var logolist_VPWW54 = timelineManager.getMeteWarningLogoPath(hierarchy,code);
                for (var i=0; i<logolist_VPWW54.length; i++){
                    logoListModel_VPWW54.append({"value":logolist_VPWW54[i]});
                }
                infoLoader_VPWW54.item.logoListModel = logoListModel_VPWW54;
            } else {
                infoLoader_VPWW54.item.dateTimeText = "";
                infoLoader_VPWW54.item.headTitleText = "";
                infoLoader_VPWW54.item.headlineText = "";
                infoLoader_VPWW54.item.bodyText = "";
            }
        }

        // VXWW50 土砂災害警戒情報用
        if (infoLoader_VXWW50.item) {
            var codes_VXWW50 = timelineManager.getVXWW50WarningCode(hierarchy, code);
            if (codes_VXWW50.length > 0) {
                infoLoader_VXWW50.item.headlineText = timelineManager.getVXWW50HeadlineText(hierarchy,code);
                infoLoader_VXWW50.item.headTitleText = timelineManager.getVXWW50Title(hierarchy,code);
                var dt_VXWW50 = timelineManager.getVXWW50Updated(hierarchy,code);
                infoLoader_VXWW50.item.dateTimeText = (dt_VXWW50 === "2000/01/01 00:00:00") ? "" : dt_VXWW50;
                var logolist_VXWW50 = timelineManager.getVXWW50LogoPath(hierarchy,code);
                for (var j=0; j<logolist_VXWW50.length; j++){
                    logoListModel_VXWW50.append({"value":logolist_VXWW50[j]});
                }
                infoLoader_VXWW50.item.logoListModel = logoListModel_VXWW50;
            } else {
                infoLoader_VXWW50.item.dateTimeText = "";
                infoLoader_VXWW50.item.headTitleText = "";
                infoLoader_VXWW50.item.headlineText = "";
                infoLoader_VXWW50.item.bodyText = "";
            }
        }

        // VPHW51 竜巻注意情報
        if (infoLoader_VPHW51.item) {
            var codes_VPHW51 = timelineManager.getVPHW51WarningCode(hierarchy, code);
            if (codes_VPHW51.length > 0) {
                infoLoader_VPHW51.item.headlineText = timelineManager.getVPHW51HeadlineText(hierarchy,code);
                infoLoader_VPHW51.item.headTitleText = timelineManager.getVPHW51Title(hierarchy,code);
                var dt_VPHW51 = timelineManager.getVPHW51Updated(hierarchy,code);
                infoLoader_VPHW51.item.dateTimeText = (dt_VPHW51 === "2000/01/01 00:00:00") ? "" : dt_VPHW51;
                var logolist_VPHW51 = timelineManager.getVPHW51LogoPath(hierarchy,code);
                for (var k=0; k<logolist_VPHW51.length; k++){
                    logoListModel_VPHW51.append({"value":logolist_VPHW51[k]});
                }
                infoLoader_VPHW51.item.logoListModel = logoListModel_VPHW51;
            } else {
                infoLoader_VPHW51.item.dateTimeText = "";
                infoLoader_VPHW51.item.headTitleText = "";
                infoLoader_VPHW51.item.headlineText = "";
                infoLoader_VPHW51.item.bodyText = "";
            }
        }

        // VPOA50 記録的短時間大雨情報
        if (infoLoader_VPOA50.item) {
            if (timelineManager.getVPOA50ID(hierarchy,code)!="") {
                infoLoader_VPOA50.item.headlineText = timelineManager.getVPOA50HeadlineText(hierarchy,code);
                infoLoader_VPOA50.item.headTitleText = timelineManager.getVPOA50Title(hierarchy,code);
                var dt_VPOA50 = timelineManager.getVPOA50Updated(hierarchy,code);
                infoLoader_VPOA50.item.dateTimeText = (dt_VPOA50 === "2000/01/01 00:00:00") ? "" : dt_VPOA50;
            } else {
                infoLoader_VPOA50.item.dateTimeText = "";
                infoLoader_VPOA50.item.headTitleText = "";
                infoLoader_VPOA50.item.headlineText = "";
                infoLoader_VPOA50.item.bodyText = "";
            }
        }

        // VPFJ50 府県気象情報
        if (infoLoader_VPFJ50.item) {
            var data_type="VPFJ50"
            if (timelineManager.getVPZJ50ID(hierarchy,code,data_type)!="") {
                infoLoader_VPFJ50.item.headlineText = timelineManager.getVPZJ50HeadlineText(hierarchy,code,data_type);
                infoLoader_VPFJ50.item.headTitleText = timelineManager.getVPZJ50Title(hierarchy,code,data_type);
                infoLoader_VPFJ50.item.bodyText = timelineManager.getVPZJ50BodyText(hierarchy,code,data_type);
                var dt_VPFJ50 = timelineManager.getVPZJ50Updated(hierarchy,code,data_type);
                infoLoader_VPFJ50.item.dateTimeText = (dt_VPFJ50 === "2000/01/01 00:00:00") ? "" : dt_VPFJ50;
            } else {
                infoLoader_VPFJ50.item.dateTimeText = "";
                infoLoader_VPFJ50.item.headTitleText = "";
                infoLoader_VPFJ50.item.headlineText = "";
                infoLoader_VPFJ50.item.bodyText = "";
            }
        }
        // VPFJ50 府県気象概況
        if (infoLoader_VPFG50.item) {
            var data_type="VPFG50"
            if (timelineManager.getVPZJ50ID(hierarchy,code,data_type)!="") {
                infoLoader_VPFG50.item.headlineText = timelineManager.getVPZJ50HeadlineText(hierarchy,code,data_type);
                infoLoader_VPFG50.item.headTitleText = timelineManager.getVPZJ50Title(hierarchy,code,data_type);
                infoLoader_VPFG50.item.bodyText = timelineManager.getVPZJ50BodyText(hierarchy,code,data_type);
                var dt_VPFG50 = timelineManager.getVPZJ50Updated(hierarchy,code,data_type);
                infoLoader_VPFG50.item.dateTimeText = (dt_VPFG50 === "2000/01/01 00:00:00") ? "" : dt_VPFG50;
            } else {
                infoLoader_VPFG50.item.dateTimeText = "";
                infoLoader_VPFG50.item.headTitleText = "";
                infoLoader_VPFG50.item.headlineText = "";
                infoLoader_VPFG50.item.bodyText = "";
            }
        }
        // VPFD51 府県天気予報
        if (infoLoader_VPFD51.item) {
            var data_type="VPFD51"
            if (timelineManager.getVPFD51ID(hierarchy,code,data_type)!="") {
                infoLoader_VPFD51.item.headlineText = timelineManager.getVPFD51HeadlineText(hierarchy,code,data_type);
                infoLoader_VPFD51.item.headTitleText = timelineManager.getVPFD51Title(hierarchy,code,data_type);
                infoLoader_VPFD51.item.bodyText = timelineManager.getVPFD51BodyText(hierarchy,code,data_type);
                var dt_VPFD51 = timelineManager.getVPFD51Updated(hierarchy,code,data_type);
                infoLoader_VPFD51.item.dateTimeText = (dt_VPFD51 === "2000/01/01 00:00:00") ? "" : dt_VPFD51;
            } else {
                infoLoader_VPFD51.item.dateTimeText = "";
                infoLoader_VPFD51.item.headTitleText = "";
                infoLoader_VPFD51.item.headlineText = "";
                infoLoader_VPFD51.item.bodyText = "";
            }
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
                                var check = timelineManager.checkVPHW51(hierarchy,code);
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
        width: 400
        anchors.margins: 5
        // 情報表示用のコンテナ
        Rectangle {
            id: infoarea
            anchors.fill: parent
            anchors.bottomMargin:3
            color: "#f0f0f0"
            border.color: "gray"
            border.width: 1
            Label {
                id: infoTitle
                anchors.leftMargin: 3
                anchors.topMargin: 3
                anchors.rightMargin:3
                text: "地域名"
                anchors.top:parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                font.pixelSize: 20
                font.bold: true
                background: Rectangle {
                    color: "#75fff3ff"
                }
            }
            Flickable {
                anchors.top: infoTitle.bottom
                anchors.bottom: parent.bottom
                anchors.left:infoTitle.left
                anchors.right:infoTitle.right
                contentWidth: parent.width-2*infoTitle.anchors.leftMargin
                //contentHeight: parent.height-infoTitle.height-infoTitle.anchors.topMargin-5
                contentHeight: contentColumn.height
                flickableDirection: Flickable.VerticalFlick
                clip: true
                Rectangle {
                    color: "transparent"
                    border.color: "#ff75ffff"
                    anchors.fill: parent
                }
                Column {
                    id: contentColumn
                    width: parent.width
                    spacing: 5
                    
                    Loader {
                        id: infoLoader_VPFD51
                        source: "infoText_component.qml"
                        width: parent.width
                        //height: item ? item.height : 0
                    }
                    Loader {
                        id: infoLoader_VXWW50
                        source: "infoText_component.qml"
                        width: parent.width
                        //height: item ? item.height : 0
                    }
                    Loader {
                        id: infoLoader_VPWW54
                        source: "infoText_component.qml"
                        width: parent.width
                        //height: item ? item.height : 0
                    }
                    
                    Loader {
                        id: infoLoader_VPHW51
                        source: "infoText_component.qml"
                        width: parent.width
                        //height: item ? item.height : 0
                    }
                    Loader {
                        id: infoLoader_VPOA50
                        source: "infoText_component.qml"
                        width: parent.width
                        //height: item ? item.height : 0
                    }
                    Loader {
                        id: infoLoader_VPFJ50
                        source: "infoText_component.qml"
                        width: parent.width
                        //height: item ? item.height : 0
                    }
                    Loader {
                        id: infoLoader_VPFG50
                        source: "infoText_component.qml"
                        width: parent.width
                        //height: item ? item.height : 0
                    }
                }
            }
        }
    }
}