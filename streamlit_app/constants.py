from typing import TypeVar

import matplotlib as mpl


colors = ["limegreen", "yellow", "orange", "red", "fuchsia"]
cmap = mpl.colors.LinearSegmentedColormap.from_list(
    "x",
    list(zip([0.0, 15/51, 15/34, 15/17, 1], colors))
)

def sm(x: int) -> TypeVar('matplotlib.cm.ScalarMappable'):
    return mpl.cm.ScalarMappable(
        cmap=cmap,
        norm=mpl.colors.Normalize(vmin=0, vmax=1.7*x)
    )

INFO_POLLUTANTS = {
    "PM2.5": {
        "name": "Particules fines",
        "guideline": 15,
        "unit": "µg/m³",
        "scalar mappable": sm(15)
    },
    "PM10": {
        "name": "Particules",
        "guideline": 45,
        "unit": "µg/m³",
        "scalar mappable": sm(45)
    },
    "NO2": {
        "name": "Dioxide d'azote",
        "guideline": 25,
        "unit": "µg/m³",
        "scalar mappable": sm(25)
    },
    "SO2": {
        "name": "Dioxide de soufre",
        "guideline": 40,
        "unit": "µg/m³",
        "scalar mappable": sm(40)
    },
    "CO": {
        "name": "Monoxide de carbone",
        "guideline": 4,
        "unit": "mg/m³",
        "scalar mappable": sm(4)
    }
}

def first_colorbar(pollutant: str) -> TypeVar('matplotlib.figure.Figure'):
    
    def tick_format(value, position):
        if not(position):
            label = "0"
        elif position == 1:
            label = {:^}.format(f"Recommandation de l'OMS :\n {value:.2f}")
        else:
            label = f"{"> "}{value:.2f}"
        return label

    f, ax = mpl.pyplot.subplots()
    ax.set_axis_off()
    x = INFO_POLLUTANTS[pollutant]["guideline"]
    f.colorbar(
        INFO_POLLUTANTS[pollutant]["scalar mappable"],
        orientation="horizontal",
        fraction=1,
        extend="max",
        ticks=[0, x, 1.5*x],
        format=tick_format
    )
    u = INFO_POLLUTANTS[pollutant]["unit"]
    f.suptitle(
        f"Niveaux moyens de concentration de {pollutant} enregistrée sur 24 heures ({u})"
    )
    return f

def second_colorbar(pollutant: str, value: float) -> TypeVar('matplotlib.figure.Figure'):
    
    f, ax = mpl.pyplot.subplots()
    ax.set_axis_off()
    x = value / INFO_POLLUTANTS[pollutant]["guideline"]
    if x > 1.7:
        cmap = mpl.colors.LineraSegmentedColormap.from_list(
            "y",
            list(zip(
                [
                    0.0,
                    (15*x)/(value*3),
                    (15*x)/(value*2),
                    (15*x)/value,
                    value
                ],
                colors
            ))
        )
        sm = mpl.cm.ScalarMappable(
            cmap=cmap,
            norm=mpl.colors.Normalize(vmin=0, vmax=value)
        )
    else:
        sm = INFO_POLLUTANTS[pollutant]["scalar mappable"]
    f.colorbar(
        sm
        cax=ax,
        orientation="horizontal",
        extend="max",
        ticks=[value]
    )
    u = INFO_POLLUTANTS[pollutant]["unit"]
    ax.text(
        value,
        -0.7,
        "^"+"\n".join(["|","|","|","|","Valeur enregistrée :", f"{value:.2f} {u}"])
    )
    return f
