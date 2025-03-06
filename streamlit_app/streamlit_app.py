from datetime import date, datetime, timedelta
from typing import List

import streamlit as st
from pandas import concat, DataFrame, read_csv

@st.cache_data()
def get_stations_data(department_code: str) -> list:
    station_data = read_csv(
        f"stations/{department_code}.csv"
    ).to_records()
    result = []
    for x in station_data:
        s = x[3]
        pollutants = []
        recording_dates = (
            date.today()-timedelta(days=k) for k in range(1, 15)
        )
        for d in recording_dates:
            df = dictionary[d]
            pollutants += df[df["code"]==s]["Polluant"].to_list()
            pollutants = list(
                set(pollutants) & set(["PM2.5", "PM10", "NO2", "SO2", "CO"])
            )
        if len(pollutants):
            result.append([list(x), pollutants])
    return result

@st.cache_data(show_spinner="Récupération des données en cours")
def import_pollution_data(station: str, n_days: int) -> List[DataFrame]:
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
    return result

@st.cache_data()
def get_records(station: str, n_days: int, pollutant: str) -> List[float]:
    dataframes = import_pollution_data(station, n_days)
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

if "selected_station" not in st.session_state:
    st.session_state["selected_station"] = None
if "map_id" not in st.session_state:
    st.session_state["map_id"] = 0
if "location" not in session_state:
    st.session_state["location"] = "Métropole"
if "overseas" not in session_state:
    st.session_state["overseas"] = None

@st.fragment
def display_map()
    st.markdown(
        f"""
        <div id="map">
            <div id="tooltip></div>
        </div>
        <div id="location"></div>
        <script type="module" src="./js/map{st.session_state["map_id"]}.js"></script>
        """,
        unsafe_allow_html=True
    )

    _, column = st.columns([0.6, 0.4])
    overseas_departments = {
        "Guadeloupe": 971,
        "Martinique": 972,
        "Guyane": 973,
        "La Réunion": 974,
        "Mayotte": 976,
        "Saint-Martin": 977
    }

    def update_view():
        rerun = True
        if st.session_state["location"] == "Métropole":
            st.session_state["map_id"] = 0
        else:
            if st.session_state["overseas"]:
                st.session_state["map_id"] = \
                overseas_departments[st.session_state["overseas"]]
            else:
                rerun = False
        if rerun:
            st.rerun(scope="fragment")

    with column:
        location = st.radio(
            "",
            ["Métropole", "Outre-mer"],
            key="location",
            on_change=update_view
        )
        if location == "Outre-mer":
            overseas = st.selectbox(
                "Département souhaité",
                list(overseas_departments.keys()),
                index=None,
                key="overseas",
                on_change=update_view
            )

if st.session_state["selected_station"]:
    n_days = st.selectbox(
        "Periode de pollution souhaitée",
        [f"{k} dernier{"s" if k > 1 else ""} jours" for k in range(1, 15)]
    )
    df = concat(import_pollution_data(
        st.session_state["selected_station"],
        n_days
    ))
    available_pollutants = df["Polluant"].unique()
    selected_pollutant = available_pollutants.iloc[0] if \
    not(len(available_pollutant)) else st.radio(
        "Polluants disponibles :",
        available_pollutants
    )
    records = get_records(
        st.session_state["selected_station"],
        n_days,
        selected_pollutant)
