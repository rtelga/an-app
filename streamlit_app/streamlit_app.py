from datetime import date, datetime, timedelta
from statistics import mean
from typing import List

import streamlit as st
from pandas import DataFrame, read_csv, read_excel, Series

from constants import INFO_POLLUTANTS, first_colorbar, second_colorbar

def get_codes() -> Series:
    df = read_excel(
        "https://www.lcsqa.org/system/files/media/documents/Liste points de mesures 2021 pour site LCSQA_27072022.xlsx".replace(" ","%20")
        sheet_name=1
    ).set_axis(station.iloc[1].to_list(), axis="columns").iloc[2:]
    return df["Code station"]


@st.cache_data(show_spinner="Récupération des données en cours")
def import_data(station: str, n_days: int) -> None:
    progress_bar = st.progress(0.0)
    result = []
    url = "https://files.data.gouv.fr/lcsqa/concentrations-de-polluants-atmospheriques-reglementes/temps-reel/"
    columns = ["code site", "Polluant", "Date de début", "valeur brute"]
    for k, d in enumerate(date.today()-timedelta(days=k) for k in range(1, n_days)):
        try:
            df = read_csv(
                f"{url}{d.year}/FR_E2_{d.isoformat()}.csv",
                sep=";"
            )
            df = df[df["code site"]==station]
            df = df[df["validité"]==1]
            df = df[df["valeur brute"] > 0]
            df = df.fillna(float(0))
            df = df[columns]
        except:
            df = DataFrame(["None"]*4, columns=columns)
        result.append(df)
        x = "s" if n_days-k > 1 else ""
        progress_bar.progress((k+1)/n_days, text=f"{n_days-k} jour{x} restant{x}")
    progress_bar.empty()
    st.session_state["data"] = result

@st.cache_data()
def get_values(station: str, n_days: int, pollutant: str) -> List[float]:
    dataframes = st.session_state["data"]
    result = []
    for df in dataframes:
        try:
            df = df[df["Pollutant"]==pollutant]
            df["date"] = df["Date de début"].apply(
                lambda x: datetime.fromisoformat(
                    f"{x[:10].replace("/", "-")}T{x[11:]}"))
            datetimes = (datetime.fromisoformat(
                f"{df["date"].iloc[0].date().isoformat()}T00:00:00")+
                timedelta(hours=k) for k in range(24))
            dictionary = {x.isoformat(): -1 for x in datetimes}
            for d, v in zip(df["date"], df["value"]):
                dictionary[d.isoformat()] = v
            result.append(list(dictionary.values()))
        except:
            result.append([])
    return list(result.values())



if "stations" not in st.session_state:
    st.session_state["stations"] = get_codes()
if "data" not in st.session_state:
    st.session_state["data"] = None
if "location" not in st.session_state:
    st.session_state["location"] = "Métropole"
if "overseas" not in st.session_state:
    st.session_state["overseas"] = None
if "i" not in st.session_state:
	st.session_state["i"] = 0
if "colorbar" not in st.session_state:
    st.session_state["colorbar"] = None

st.markdown(
    """
    <div id="map">
        <div id="station-name" style="background-color: #000000; color: #FFFFFF"></div>
        <div id="station-code" style="background-color: rgba(17, 214, 29, 1); color rgba(218, 67, 24): ; border: 4px solid; text-align: center"></div>
    </div>
    <div id="plot"></div>
    <div id="legend"></div>
    <script src="https://cdn.jsdelivr.net/npm/ol@v10.4.0/dist/ol.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ol@v10.4.0/ol.css">

    <script type="module">

        import { geojsonData } from './map/departments.js';
        import { stations } from './map/stations.js';

        const departmentLayer = new ol.layer.VectorLayer({
            source: new ol.source.VectorSource({
                features: new ol.format.GeoJSON().readFeatures(
                    geojsonData,
                    {featureProjection: 'EPSG:3857'}
                )
            }),
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: [0, 0, 247, 1],
                    width: 0.7
                }),
                fill: new ol.style.Fill({color: [217, 224, 247, 0.4]})
            })
        });

        const stationLayer = new ol.layer.VectorLayer({
        source: new ol.source.VectorSource(),
        style: new ol.style.Style({
            image: new ol.style.Circle({
                radius: 7,
                fill: new ol.style.Fill({
                    color: [4, 4, 7, 1]
                })
            })
        })
    });

        const departmentWithNoDataLayer = new ol.layer.VectorLayer({
            source: new ol.source.VectorSource(),
            style: new ol.style.Style({
                fill: new ol.style.Fill({
                    color: [247, 0, 0, 0.7]
                })
            })
        });

        const stationName = document.getElementById("station-name");
        const overlayA = new ol.Overlay({
            element: stationName,
            positioning: 'bottom-center'
        });

        const stationCode = document.getElementById("station-code");
        const overlayB = new ol.Overlay({
            element: stationCode,
            positioning: 'bottom-center'
        });

        const m = new ol.Map({
            target: "map",
            layers: [
                new ol.layer.TileLayer({
                    source: new ol.source.OSM(),
                }),
                departmentLayer
            ],
            overlays: [overlayA],
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
            map.render();
        };

        const pointerMoveCallback = (e) => {
            if (m) {
                let text;
                const departmentStyle = departmentLayer.getStyle();
                const hightlightStyle = new ol.style.Style({
                    stroke: new ol.style.Stroke({
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
            map.render();
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
                    tooltip.textContent = `Code station :\n\n ${properties.code}`;
                    overlayB.setPosition([e.coordinate[0], e.coordinate[1]+4000]);
                    feature.getStyle().setFill(new ol.style.Fill({color: [0, 247, 0, 1]}));
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
                            (s) => new ol.Feature({
                                geometry: new ol.geom.Point(ol.proj.fromLonLat(s.longitude, s.latitude)),
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
            map.render();
        }
        map.render();
    </script>
    """,
    unsafe_allow_html=True
)
  
   
selected_station = st.text_input(
    "Code de la station choisie",
    help="Cliquez sur la station choisie pour faire apparaître son code d'identification."
)
if len(selected_station):
    if selected_station not in st.session_state["stations"]:
        st.error("Le code indiqué n'est pas valide !")
    else:
        options = ["Journée d'hier"] + \
        [f"{k} derniers jours" for k in range(2, 15)]
        period = st.selectbox(
            "Période de pollution souhaitée",
            options)
        n_days = options.index(period)+1
        import_data(selected station, n_days)
        df = st.session_state["data"]
        try:
            available_pollutants = df["Polluant"].unique()
            selected_pollutant = available_pollutants.iloc[0] if \
            not(len(available_pollutant)) else st.radio(
                "Polluants disponibles :",
                available_pollutants
            )
            st.session_state["colorbar"] = first_colorbar(selected_pollutant)
            values = get_values(
                selected_station
                n_days,
                selected_pollutant)
        except:
            st.write("Désolé, aucune donnée disponible pour la période souhaitée !")

         
    @st.fragment()
	def display_chart(pollutant: str) -> None:

        data = {
            "Hour": [f"{x}h00" for x in range(1, 24)],
            "Values": values[st.session_state["i"]]
        }
        dailyAverage = mean(data["Values"])
        sm = INFO_POLLUTANTS[pollutant]["scalar mappable"]
        st.area_chart(
            data,
            x="Hour",
            y="Values",
            color=sm.to_rgba([dailyAverage])[0])
        st.write("\n")
        st.pyplot(st.session_state["colorbar"])
        st.pyplot(second_colorbar(pollutant), dailyAverage)

        def update_values(date: str) -> None:
			if date=="previous":
				st.session_state["i"] -= 1
			else:
				st.session_state["i"] += 1
			st.rerun(scope="fragment")
		
        x, _, y = st.columns([0.1, 0.8, 0.1])
    	with x:
        	if st.session_state["i"] > 0:
                if st.button("Journée précédente"):
            	    update_values("previous")
    	with y:
            if st.session_state["i"] < 14:
        	    if st.button("Journée suivante"):
            	    update_values("next")
    
	display_chart(selected_pollutant)
