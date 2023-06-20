import requests
import folium
import streamlit_folium as stf
import streamlit as st

def get_marker_color(disp):
    if disp > 1:
        return 'green'
    elif disp ==1:
        return 'orange'
    else:
        return 'red'

def get_marker_popup(station):
    lab = station['label']
    num = station['num']
    dir = station['dir']
    dias = station['dias']
    horario = station['horario']
    acceso = station['acceso']

    popup = f"<b>Owner:</b> {lab}<br>"
    popup += f"<b>Address:</b> {dir}<br>"
    popup += f"<b>Available chargers:</b> {num}<br>"
    popup += f"<b>Opening days: </b> {dias}<br>"
    popup += f"<b>Hours : </b> {horario}<br>"
    popup += f"<b>Type of access: </b> {acceso}<br>"

    return popup


st.set_page_config(
    page_title="eBCN",
    layout="wide",
)

st.markdown("# eBCN chargers", unsafe_allow_html=True)

col1, col2 = st.columns([3,1])
with col1:
    dire = st.text_input('Introduce an origin to get the route to the closet available charger', 'Example: Av. Diagonal, 467')
with col2:
    type_charger = st.selectbox(
        ' ',
        ('Atleast one available connector', 'More than one available connector'))


if type_charger == "Atleast one available connector":
    n_charg = 1
else:
    n_charg = 2


url = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8cdafa08-d378-4bf1-aad4-fafffe815940/resource/e3732605-4944-44da-b8a0-701df2ba73c3/download'
response = requests.get(url)
data = response.json()

m = folium.Map(location=[41.38879, 2.15899], zoom_start=13)
ubis= []

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

    if disponibles >= n_charg:
        ubis.append((lat, long))

    marker_color = get_marker_color(disponibles)
    marker_popup = get_marker_popup({
        'label': empresa,
        'num': f"{disponibles}/{len(ejemplo['stations'][0]['ports'])}",
        'dir': direccion,
        'dias': dias,
        'horario':horario,
        'acceso': acceso
    })

    folium.Marker(location=[lat, lon],icon=folium.Icon(color=marker_color,icon='plug', prefix='fa'), popup=marker_popup).add_to(m)


if dire:
    geocoding_url = f"https://nominatim.openstreetmap.org/search?q={dire}&format=json"
    response = requests.get(geocoding_url)
    results = response.json()

    if len(results) > 0:
        lat = float(results[0]['lat'])
        lon = float(results[0]['lon'])
        
        folium.Marker(
            location=[lat, lon],
            icon=folium.Icon(color='blue'),
            popup=dire
        ).add_to(m)
        
        closest_point = min(ubis, key=lambda p: ((p[0] - lat)**2 + (p[1] - lon)**2)**0.5)

        try:
            routing_url = f"http://router.project-osrm.org/route/v1/driving/{lon},{lat};{closest_point[1]},{closest_point[0]}?overview=full&geometries=geojson"
            response = requests.get(routing_url)
            route_data = response.json()
            route_geometry = route_data['routes'][0]['geometry']

            route_style = {
                'fillColor': 'blue',
                'color': 'blue',
                'weight': 7
            }

            folium.GeoJson(
                route_geometry,
                style_function=lambda x: route_style
            ).add_to(m)
            bounds = folium.GeoJson(route_geometry).get_bounds()
            center = [(bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2]
            m.fit_bounds(route.get_bounds(), center=center)
        except:
            pass

stf.folium_static(m, width=1300, height=600)
