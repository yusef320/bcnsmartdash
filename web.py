import requests
import folium
import streamlit_folium as stf
import streamlit as st
import plotly.graph_objects as go



def get_marker_color(disp):
    if disp > 1:
        return 'green'
    elif disp == 1:
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

    popup = f"<b>Available chargers:</b> {num}<br>"
    popup += f"<b>Opening days: </b> {dias}<br>"
    popup += f"<b>Hours: </b> {horario}<br>"
    popup += f"<b>Address:</b> {dir}<br>"
    popup += f"<b>Access: </b> {acceso}<br>"
    popup += f"<b>Owner:</b> {lab}<br>"

    return popup

@st.cache
def grafico_circular(rojos_porc, naranjas_porc, verdes_porc):
    labels = ['No conn. availables', 'One conn. available', 'More than one conn. available']
    valores = [rojos_porc, naranjas_porc, verdes_porc]
    colores = ['#d33d2a', '#f59630', '#71ae26']  # Rojo, naranja, verde

    # Crea la figura y el gráfico circular
    fig = go.Figure(data=[go.Pie(labels=labels, values=valores, marker=dict(colors=colores))])

    # Configura el diseño del gráfico
    fig.update_layout(title_text="% of chargers by number of available connectors",
                      title_x=0.3, legend_x=0.7)

    # Muestra el gráfico interactivo
    st.plotly_chart(fig)


st.set_page_config(
    page_title="eBCN",
    layout="wide",
)


st.markdown("# eBCN chargers", unsafe_allow_html=True)


# Load the JSON data from the provided URL
url = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8cdafa08-d378-4bf1-aad4-fafffe815940/resource/e3732605-4944-44da-b8a0-701df2ba73c3/download'
response = requests.get(url)
data = response.json()


# option to expand and view statistics
with st.expander("**Statistics**"):
    disponibles_list, totales_list = [], []
    for ejemplo in data['locations']:
        disponibles = 0  # cargadores disponibles en esta estación
        for estacion in ejemplo["stations"][0]["ports"]:
            if estacion["port_status"][0]["status"] == "AVAILABLE":
                disponibles += 1
        disponibles_list.append(disponibles)
        totales_list.append(len(ejemplo['stations'][0]['ports']))
    rojos, naranjas, verdes = 0, 0, 0
    for i in range(len(disponibles_list)):
        if disponibles_list[i] == 0:    # no hay ningún conector disponible
            rojos += 1
        elif disponibles_list[i] == 1:
            naranjas += 1
        else:
            verdes += 1
    total = rojos + naranjas + verdes
    rojos_porc = rojos*100/total
    naranjas_porc = naranjas*100/total
    verdes_porc = verdes*100/total
    grafico_circular(rojos_porc, naranjas_porc, verdes_porc)


col1, col2 = st.columns([3,1])
with col1:
    dire = st.text_input('Enter a street (or address if the street is very long) to get the route to the closest available charger', 'Carrer de Nicaragua')
    dire = dire + '. Barcelona, España'
with col2:
    type_charger = st.selectbox(
        'Number of available connectors',
        ('At least one', 'More than one'))


if type_charger == "At least one":
    n_charg = 1
else:
    n_charg = 2


# Create a Folium map centered on Barcelona
m = folium.Map(location=[41.38879, 2.15899], zoom_start=13)
ubis= []
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

    if disponibles >= n_charg:
        ubis.append((lat, lon))
    # Aquí puedes realizar las operaciones que desees con los datos extraídos
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

        # Agregar un marcador en la ubicación ingresada

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
                'weight': 5
            }

            # Agregar la ruta al mapa
            folium.GeoJson(
                route_geometry,
                style_function=lambda x: route_style
            ).add_to(m)
        except:
            pass


# show map
with st.expander(" ", expanded=True):
    stf.folium_static(m, width=1300, height=600)
