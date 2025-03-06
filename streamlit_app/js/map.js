import Feature from 'ol/Feature.js';
import GeoJSON from 'ol/format/GeoJSON.js';
import TileLayer from 'ol/layer/Tile.js';
import Map from 'ol/Map.js';
import 'ol/ol.css';
import { fromLonLat } from 'ol/proj.js';
import OSM from 'ol/source/OSM.js';
import { Circle, Fill, Stroke, Style } from 'ol/style.js';
import Point from 'ol/geom/Point.js';
import VectorLayer from 'ol/layer/Vector.js';
import Overlay from 'ol/Overlay.js';
import VectorSource from 'ol/source/Vector.js';
import View from 'ol/View.js';

import { geojsonData } from './constants/departments.js';
import { stations } from './constants/stations.js';

function displayMap(center, zoom) {
    const departmentLayer = new VectorLayer({
        source: new VectorSource({
            features: new GeoJSON().readFeatures(
                geojsonData,
                {featureProjection: 'EPSG:3857'}
            )
        }),
        style: new Style({
            stroke: new Stroke({
                color: [0, 0, 247, 1],
                width: 0.7
            }),
            fill: new Fill({color: [217, 224, 247, 0.4]})
        })
    });

    const stationLayer = new VectorLayer({
        source: new VectorSource(),
        style: new Style({
            image: new Circle({
                radius: 7,
                fill: new Fill({
                    color: [4, 4, 7, 1]
                })
            })
        })
    });

    const departmentWithNoDataLayer = new VectorLayer({
        source: new VectorSource(),
        style: new Style({
            fill: new Fill({
                color: [247, 0, 0, 0.7]
            })
        })
    });

    const stationName = document.getElementById("station-name");
    const overlayA = new Overlay({
        element: stationName,
        positioning: 'bottom-center'
    });

    const stationCode = document.getElementById("station-code");
    const overlayB = new Overlay({
        element: stationCode,
        positioning: 'bottom-center'
    });
    
    const m = new Map({
        target: "map",
        layers: [
            new TileLayer({
                source: new OSM(),
            }),
            departmentLayer
        ],
        overlays: [overlayA],
        view: new View({
            center: fromLonLat(center),
            zoom: zoom
        }),
        controls: []
    });

    m.on('moveend', moveEndCallback);
    m.on('pointermove', pointerMoveCallback);
    m.on('click', clickCallback);

    const location = document.getElementById("location");
    let hoverCurrentDepartment;
    let clickCurrentDepartment;
    let clickCurrentStation;

    const moveEndCallback = () => {
        if (m) {
            const v = m.getView();
            location.innerHTML = `${v.getCenter()}\n${v.getZoom()}`;
        }
    };

    const pointerMoveCallback = (e) => {
        if (m) {
            let text;
            const departmentStyle = departmentLayer.getStyle();
            const hightlightStyle = new Style({
                stroke: new Stroke({
                    color: [0, 0, 247, 1],
                    width: 4.4
                }),
                fill: departmentStyle.getFill()
            });
            const features = m.getFeaturesAtPixel(e.pixel);
            if (features.length) {
                const feature = features[0];
                const properties = feature.getProperties();
                const featureIsAStation = 'name' in properties;
                m.getTargetElement().style.cursor = featureIsAStation ? 'pointer' : 'default';
                if (! featureIsAStation) {
                    if (feature!==hoverCurrentDepartment) {
                        if (hoverCurrentDepartment){
                            hoverCurrentDepartment.setStyle(departmentStyle);
                        }
                        feature.setStyle(hightlightStyle);
                        hoverCurrentDepartment = feature;
                    }
                    text = properties.nom+' ('+properties.code+')';
                } else {
                    text = properties.name;
                }
                tooltip.textContent = text;
                overlayA.setPosition([e.coordinate[0], e.coordinate[1]+4000]);
            } else {
                if (hoverCurrentDepartment) {
                    hoverCurrentDepartment.setStyle(departmentStyle);
                    hoverCurrentDepartment = undefined;
                }
                overlayA.setPosition(null);
                m.getTargetElement().style.cursor = 'default';
            }
        }
    };
        
    const deselectDepartment = (department) => {
        departmentLayer.getSource().addFeature(department);
        const layers = m.getAllLayers();
        if (layers.includes(stationLayer)) {
            stationLayer.getSource().clear();
            m.removeLayer(stationLayer);
        } else {
            departmentWithNoDataLayer.getSource().clear();
            m.removeLayer(departmentWithNoDataLayer);
        }
    };

    const deselectStation = (station) => {
        station.getStyle().setFill(stationLayer.getStyle().getFill());
        overlayB.setPosition(null);
    }
    
    const clickCallback = (e) => {
        const features = m.getFeaturesAtPixel(e.pixel);
        if (features.length) {
            const feature = features[0];
            const properties = feature.getProperties();
            const currentCode = properties.code;
            if ('name' in properties) {
                if (clickCurrentStation) {
                    deselectStation(clickCurrentStation);
                }
                tooltip.textContent = properties.code;
                overlayB.setPosition([e.coordinate[0], e.coordinate[1]+4000]);
                feature.getStyle().setFill(new Fill({color: [0, 247, 0, 1]}));
            } else {
                if (clickCurrentDepartment) {
                    deselectDepartment(clickCurrentDepartment);
                }
                if (clickCurrentStation) {
                    deselectStation(clickCurrentStation);
                }
                departmentLayer.getSource().removeFeature(feature);
                const x = ['09', '11', '46', '48'];
                if (! x.includes(currentCode)) {
                    const data =  stations[currentCode]
                    const markers = data.map(
                        (s) => new Feature({
                            geometry: new Point(fromLonLat(s.longitude, s.latitude)),
                            code: s.code,
                            name: s.name,
                        })
                    );
                    stationLayer.getSource().addFeatures(markers);
                    m.addLayer(stationLayer);
                    m.getView().fit(feature.getGeometry(), {duration: 700});
                } else {
                    departmentWithNoDataLayer.getSource().addFeature(feature);
                    m.addLayer(departmentWithNoDataLayer);
                }
                clickCurrentDepartment = feature;
            }
        } else {
            if (clickCurrentDepartment) {
                deselectDepartment(clickCurrentDepartment);
                clickCurrentDepartment = undefined;
            }
        }
    }
}

export default displayMap;
