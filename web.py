import requests
import folium
from streamlit_folium import folium_static
import streamlit as st


def get_marker_color(disp):
    if disp > 0:
        return 'green'
    else:
        return 'red'


def get_marker_popup(station):
    lab = station['label']
    num = station['num']
    dir = station['dir']
    dias = station['dias']
    horario = station['horario']
    acceso = station['acceso']

    popup = f"<b>Propietario:</b> {lab}<br>"
    popup += f"<b>Dirección:</b> {dir}<br>"
    popup += f"<b>Cargadores disponibles:</b> {num}<br>"
    popup += f"<b>Apertura: </b> {dias}<br>"
    popup += f"<b>Horario: </b> {horario}<br>"
    popup += f"<b>Tipo de propiedad: </b> {acceso}<br>"

    return popup


# Load the JSON data from the provided URL
url = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8cdafa08-d378-4bf1-aad4-fafffe815940/resource/e3732605-4944-44da-b8a0-701df2ba73c3/download'
response = requests.get(url)
data = response.json()

# Create a Folium map centered on Barcelona
m = folium.Map(location=[41.3728027, 2.154058], zoom_start=13)

# Add markers to the map
for ejemplo in data['locations']:
    empresa = ejemplo["network_name"]
    lat, lon = ejemplo["coordinates"]["latitude"], ejemplo["coordinates"]["longitude"]
    direccion = ejemplo["address"]["address_string"]
    acceso = ejemplo["access_restriction"]

    weekdays = {
        1: "Lunes",
        2: "Martes",
        3: "Miércoles",
        4: "Jueves",
        5: "Viernes",
        6: "Sábado",
        7: "Domingo"
    }

    dias = weekdays[ejemplo["opening_hours"]["weekday_begin"]] + " a " + weekdays[ejemplo["opening_hours"]["weekday_end"]]
    horario = ejemplo["opening_hours"]["hour_begin"] + "-" + ejemplo["opening_hours"]["hour_end"]

    disponibles = 0  # cargadores disponibles en esta estación
    for estacion in ejemplo["stations"][0]["ports"]:
        if estacion["port_status"][0]["status"] == "AVAILABLE":
            disponibles += 1

    # Aquí puedes realizar las operaciones que desees con los datos extraídos

    marker_color = get_marker_color(disponibles)
    marker_popup = get_marker_popup({
        'label': empresa,
        'num': disponibles,
        'dir': direccion,
        'dias': dias,
        'horario':horario,
        'acceso': acceso
    })
    folium.Marker(
        location=[lat, lon],
        icon=folium.Icon(color=marker_color),
        popup=marker_popup
    ).add_to(m)
# Display the map using Streamlit
st.markdown("<h1 style='text-align: center;'>Electric Vehicle Chargers in Barcelona</h1>", unsafe_allow_html=True)
folium_static(m)
