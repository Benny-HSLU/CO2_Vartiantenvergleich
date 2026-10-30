import streamlit as st
import pandas as pd
import altair as alt
import json
import os

# --- Layout & Design Setup ---
st.set_page_config(page_title="CO2 Variantenvergleich", layout="wide")

# Custom CSS für "Dunkles Grünes Glas-Thema"
custom_css = """
<style>
/* Dunkelgrüner Farbverlauf als Hintergrund (unten sehr dunkel, oben etwas heller) */
.stApp {
    background: linear-gradient(to top, #021105, #11381c) !important;
    background-attachment: fixed;
}

/* Transparenter Header */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Haupt-Container als dunkles Milchglas-Panel (Glassmorphismus) */
.main .block-container {
    background: rgba(0, 0, 0, 0.25) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-radius: 20px !important;
    padding: 2rem 3rem !important;
    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    margin-top: 2rem !important;
    margin-bottom: 2rem !important;
}

/* Styling für alle Streamlit Buttons (Mac Glas-Stil) */
div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button {
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

/* Button Hover Effekt */
div[data-testid="stButton"] button:hover, div[data-testid="stDownloadButton"] button:hover {
    background: rgba(255, 255, 255, 0.25) !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3) !important;
    border: 1px solid rgba(255, 255, 255, 0.4) !important;
}

/* Popover / Selectboxen / Inputs - Glas-Stil */
input, div[data-baseweb="select"] > div, div[data-baseweb="popover"] > div, div[data-testid="stPopoverBody"] {
    background: rgba(0, 0, 0, 0.4) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(10px) !important;
    color: #ffffff !important;
}

/* Anpassung der Dropdown-Listen (damit weißer Text lesbar ist) */
ul[data-baseweb="menu"] {
    background-color: #0b2612 !important; 
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
li[data-baseweb="menu-item"] {
    color: #ffffff !important;
}

/* Tabs im Mac-Design */
button[data-baseweb="tab"] {
    background-color: transparent !important;
    border-radius: 10px 10px 0 0 !important;
    color: #aaaaaa !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: rgba(255, 255, 255, 0.1) !important;
    border-bottom: 3px solid #2ecc71 !important;
    color: #ffffff !important;
}

/* Allgemeine Text-Farben anpassen für dunklen Hintergrund */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label, .stApp span, div[data-testid="stMetricValue"], .stMarkdown li {
    color: #ffffff !important;
}

/* Tooltip für Dokumentation Lesbarkeit (Hintergrund abdunkeln) */
div[data-testid="stPopoverBody"] p, div[data-testid="stPopoverBody"] li, div[data-testid="stPopoverBody"] h1, div[data-testid="stPopoverBody"] h2 {
    color: #ffffff !important;
}

/* Vega Tooltip Fix (damit Grafiken beim Hovern keinen weißen Text auf weißem Grund haben) */
#vg-tooltip-element * {
    color: #000000 !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Konfiguration & Konstanten ---
DATA_FILE = "co2_data.json"
DOC_FILE = "anleitung.txt"  # Dokumentations-Datei

DEFAULT_DATA = {
    "config": {
        "length": 10.0,
        "width": 10.0,
        "floor_height": 2.8,
        "num_floors": 3,
        "num_facade_floors": 3,
        "floor_table": [{"Geschoss": "EG", "Wandflaeche": 150.0}, {"Geschoss": "OG1", "Wandflaeche": 150.0}]
    },
    "measures": {
        "Fassade": [{"name": "Standard Putz", "co2": 15.0}],
        "Dach": [{"name": "Standard Ziegel", "co2": 25.0}],
        "Wände": [{"name": "Standard Beton", "co2": 45.0}],
        "Tragstruktur": [{"name": "Standard Beton", "co2": 50.0}]
    },
    "variants": {}
}


# --- Funktionen für Datenpersistenz ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "Tragstruktur" not in data["measures"]:
                data["measures"]["Tragstruktur"] = [{"name": "Standard Beton", "co2": 50.0}]
            return data
    return DEFAULT_DATA.copy()


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# --- Initialisierung der Session State ---
if "app_data" not in st.session_state:
    st.session_state.app_data = load_data()

if "load_counter" not in st.session_state:
    st.session_state.load_counter = 0

if "current_selections" not in st.session_state:
    st.session_state.current_selections = {
        "Fassade": {
            "Nord": [], "Ost": [], "Süd": [], "West": [],
            "Energiebedarf": {"co2_per_a": 0.0, "jahre": 50, "pv_ausgleich": 0.0}
        },
        "Dach": {"Dach": []},
        "Wände": {},
        "Tragstruktur": {"Stützen": [], "Wände": [], "Decken": []}
    }

if "active_variant" not in st.session_state:
    st.session_state.active_variant = None


def update_walls_structure():
    floors = [row["Geschoss"] for row in st.session_state.app_data["config"]["floor_table"]]
    current_walls = st.session_state.current_selections.get("Wände", {})
    new_walls = {f: current_walls.get(f, []) for f in floors}
    st.session_state.current_selections["Wände"] = new_walls


update_walls_structure()

# --- APP START ---
# Header Aufteilung mit Anleitung Oben Links
col_doc, col_header, col_gear = st.columns([1.5, 4, 1.5])

with col_doc:
    st.write("")  # Kleiner Spacer für vertikale Zentrierung
    with st.popover("📖 Anleitung"):
        if os.path.exists(DOC_FILE):
            with open(DOC_FILE, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.warning("Die Datei 'anleitung.txt' wurde im Verzeichnis nicht gefunden.")

with col_header:
    st.title("CO2 Variantenvergleich 🍃")

with col_gear:
    st.write("")  # Kleiner Spacer für vertikale Zentrierung
    with st.popover("⚙️ Gebäude-Konfig."):
        st.subheader("Gebäudedaten")
        c = st.session_state.app_data["config"]
        c["length"] = st.number_input("Länge (m)", value=float(c["length"]), step=1.0)
        c["width"] = st.number_input("Breite (m)", value=float(c["width"]), step=1.0)
        c["floor_height"] = st.number_input("Geschosshöhe (m)", value=float(c["floor_height"]), step=0.1)
        c["num_floors"] = st.number_input("Anzahl Geschosse", value=int(c["num_floors"]), step=1)
        c["num_facade_floors"] = st.number_input("Anzahl Geschosse Fassade", value=int(c["num_facade_floors"]), step=1)

        st.write("Wandflächen pro Geschoss:")
        edited_df = st.data_editor(pd.DataFrame(c["floor_table"]), num_rows="dynamic")
        if st.button("Gebäudedaten speichern"):
            c["floor_table"] = edited_df.to_dict('records')
            save_data(st.session_state.app_data)
            update_walls_structure()
            st.success("Gespeichert!")
            st.rerun()

cfg = st.session_state.app_data["config"]
areas = {
    "Fassade": {
        "Nord": cfg["width"] * cfg["floor_height"] * cfg["num_facade_floors"],
        "Süd": cfg["width"] * cfg["floor_height"] * cfg["num_facade_floors"],
        "Ost": cfg["length"] * cfg["floor_height"] * cfg["num_facade_floors"],
        "West": cfg["length"] * cfg["floor_height"] * cfg["num_facade_floors"]
    },
    "Dach": {
        "Dach": cfg["length"] * cfg["width"]
    },
    "Wände": {row["Geschoss"]: row["Wandflaeche"] for row in cfg["floor_table"]},
    "Tragstruktur": {"Stützen": 0, "Wände": 0, "Decken": 0}
}

st.divider()

col_left, col_right = st.columns([1, 2.5])

# --- LINKE SPALTE: Varianten ---
with col_left:
    st.header("Varianten")
    variants = list(st.session_state.app_data["variants"].keys())

    selected_variant = st.selectbox("Gespeicherte Varianten", ["(Neue Variante)"] + variants)
    if selected_variant != "(Neue Variante)" and st.session_state.active_variant != selected_variant:
        if st.button("Variante laden"):
            st.session_state.active_variant = selected_variant
            st.session_state.current_selections = json.loads(
                json.dumps(st.session_state.app_data["variants"][selected_variant]))

            if "Energiebedarf" not in st.session_state.current_selections["Fassade"]:
                st.session_state.current_selections["Fassade"]["Energiebedarf"] = {"co2_per_a": 0.0, "jahre": 50,
                                                                                   "pv_ausgleich": 0.0}
            if "pv_ausgleich" not in st.session_state.current_selections["Fassade"]["Energiebedarf"]:
                st.session_state.current_selections["Fassade"]["Energiebedarf"]["pv_ausgleich"] = 0.0
            if "Tragstruktur" not in st.session_state.current_selections:
                st.session_state.current_selections["Tragstruktur"] = {"Stützen": [], "Wände": [], "Decken": []}

            update_walls_structure()
            st.session_state.load_counter += 1
            st.rerun()

    st.write(
        f"**Aktuell geladen:** {st.session_state.active_variant if st.session_state.active_variant else 'Keine (ungespeichert)'}")

    if st.button("Speichern (Aktualisieren)"):
        if st.session_state.active_variant:
            st.session_state.app_data["variants"][st.session_state.active_variant] = json.loads(
                json.dumps(st.session_state.current_selections))
            save_data(st.session_state.app_data)
            st.success(f"{st.session_state.active_variant} aktualisiert!")
        else:
            st.warning("Keine aktive Variante zum Aktualisieren. Bitte 'Speichern unter' nutzen.")

    st.divider()

    new_var_name = st.text_input("Neue Variante Name:")
    if st.button("Speichern unter"):
        if new_var_name:
            st.session_state.app_data["variants"][new_var_name] = json.loads(
                json.dumps(st.session_state.current_selections))
            st.session_state.active_variant = new_var_name
            save_data(st.session_state.app_data)
            st.success(f"{new_var_name} gespeichert!")
            st.rerun()
        else:
            st.error("Bitte einen Namen eingeben.")

    st.divider()

    del_variant = st.selectbox("Variante zum Löschen", variants)
    if st.button("Variante löschen"):
        if del_variant in st.session_state.app_data["variants"]:
            del st.session_state.app_data["variants"][del_variant]
            if st.session_state.active_variant == del_variant:
                st.session_state.active_variant = None
            save_data(st.session_state.app_data)
            st.success(f"{del_variant} gelöscht!")
            st.rerun()


# --- RECHTE SPALTE: CO2 Kategorien & Berechnungen ---
def render_category(cat_name, elements_dict):
    st.subheader(f"Kategorie: {cat_name}")

    measures_list = st.session_state.app_data["measures"][cat_name]
    measure_names = [m["name"] for m in measures_list]

    with st.popover(f"⚙️ Massnahmen verwalten ({cat_name})"):
        st.write("**Neue Massnahme hinzufügen**")
        new_m_name = st.text_input("Name der Massnahme", key=f"nm_{cat_name}")
        new_m_co2 = st.number_input("kgCO2/m2", value=10.0, step=1.0, key=f"nc_{cat_name}")
        if st.button("Hinzufügen", key=f"add_btn_{cat_name}"):
            if new_m_name:
                st.session_state.app_data["measures"][cat_name].append({"name": new_m_name, "co2": new_m_co2})
                save_data(st.session_state.app_data)
                st.rerun()

        st.divider()
        st.write("**Massnahme bearbeiten**")
        if measure_names:
            m_to_edit_name = st.selectbox("Massnahme auswählen", measure_names, key=f"edit_sel_{cat_name}")
            m_to_edit_obj = next(
                (m for m in st.session_state.app_data["measures"][cat_name] if m["name"] == m_to_edit_name), None)

            if m_to_edit_obj:
                new_edit_name = st.text_input("Neuer Name", value=m_to_edit_obj["name"], key=f"edit_nm_{cat_name}")
                new_edit_co2 = st.number_input("Neuer kgCO2/m2 Wert", value=float(m_to_edit_obj["co2"]), step=1.0,
                                               key=f"edit_nc_{cat_name}")

                if st.button("Änderungen speichern", key=f"edit_btn_{cat_name}"):
                    if new_edit_name != m_to_edit_name:
                        for elem, rows in st.session_state.current_selections.get(cat_name, {}).items():
                            if isinstance(rows, list):
                                for r in rows:
                                    if r.get("measure") == m_to_edit_name:
                                        r["measure"] = new_edit_name
                        for v_name, v_data in st.session_state.app_data["variants"].items():
                            for elem, rows in v_data.get(cat_name, {}).items():
                                if isinstance(rows, list):
                                    for r in rows:
                                        if r.get("measure") == m_to_edit_name:
                                            r["measure"] = new_edit_name

                    m_to_edit_obj["name"] = new_edit_name
                    m_to_edit_obj["co2"] = new_edit_co2
                    save_data(st.session_state.app_data)
                    st.success("Aktualisiert!")
                    st.rerun()
        else:
            st.info("Keine Massnahmen zum Bearbeiten vorhanden.")

        st.divider()
        st.write("**Massnahme löschen**")
        if measure_names:
            m_to_delete = st.selectbox("Massnahme auswählen (Löschen)", measure_names, key=f"del_sel_{cat_name}")
            if st.button("Löschen", key=f"del_btn_{cat_name}"):
                st.session_state.app_data["measures"][cat_name] = [
                    m for m in st.session_state.app_data["measures"][cat_name] if m["name"] != m_to_delete
                ]
                save_data(st.session_state.app_data)
                st.rerun()

    measure_names = [m["name"] for m in st.session_state.app_data["measures"][cat_name]]
    calc_data = []

    lc = st.session_state.load_counter

    for element, area in elements_dict.items():
        if cat_name == "Tragstruktur":
            st.write(f"**{element}**")
        else:
            area_str = f"{area:,.2f}".replace(",", "'")
            st.write(f"**{element}** ({area_str} m²)")

        rows = st.session_state.current_selections[cat_name][element]

        for i, row_data in enumerate(rows):
            if cat_name == "Tragstruktur":
                c1, c2, c3, c4 = st.columns([3, 2, 1.5, 1])
                with c1:
                    selected_idx = measure_names.index(row_data["measure"]) if row_data[
                                                                                   "measure"] in measure_names else 0
                    if len(measure_names) > 0:
                        row_data["measure"] = st.selectbox("Massnahmen", measure_names, index=selected_idx,
                                                           key=f"sel_{cat_name}_{element}_{i}_{lc}")
                with c2:
                    row_data["flaeche"] = st.number_input("Fläche (m²)", value=float(row_data.get("flaeche", 100.0)),
                                                          min_value=0.0, step=10.0,
                                                          key=f"fl_{cat_name}_{element}_{i}_{lc}")
                with c3:
                    row_data["anzahl"] = st.number_input("Anzahl", value=float(row_data.get("anzahl", 1.0)),
                                                         min_value=0.0, step=1.0,
                                                         key=f"anz_{cat_name}_{element}_{i}_{lc}")
                with c4:
                    st.write("")
                    st.write("")
                    if st.button("❌", key=f"del_{cat_name}_{element}_{i}_{lc}"):
                        st.session_state.current_selections[cat_name][element].pop(i)
                        st.rerun()
            else:
                c1, c2, c3 = st.columns([4, 2, 1])
                with c1:
                    selected_idx = measure_names.index(row_data["measure"]) if row_data[
                                                                                   "measure"] in measure_names else 0
                    if len(measure_names) > 0:
                        row_data["measure"] = st.selectbox("Massnahme", measure_names, index=selected_idx,
                                                           key=f"sel_{cat_name}_{element}_{i}_{lc}")
                with c2:
                    row_data["percent"] = st.number_input("Prozentanteil an der Fläche",
                                                          value=float(row_data.get("percent", 100.0)), min_value=0.0,
                                                          max_value=100.0, step=5.0,
                                                          key=f"perc_{cat_name}_{element}_{i}_{lc}")
                with c3:
                    st.write("")
                    st.write("")
                    if st.button("❌", key=f"del_{cat_name}_{element}_{i}_{lc}"):
                        st.session_state.current_selections[cat_name][element].pop(i)
                        st.rerun()

            co2_val = next(
                (m["co2"] for m in st.session_state.app_data["measures"][cat_name] if m["name"] == row_data["measure"]),
                0)

            if cat_name == "Tragstruktur":
                total_co2 = co2_val * row_data.get("flaeche", 0) * row_data.get("anzahl", 0)
            else:
                total_co2 = area * co2_val * (row_data.get("percent", 0) / 100.0)

            if total_co2 > 0:
                calc_data.append({"Element": element, "Massnahme": row_data["measure"], "CO2 (kg)": total_co2})

        if st.button(f"➕ Zeile hinzufügen ({element})", key=f"add_{cat_name}_{element}_{lc}"):
            if len(measure_names) > 0:
                if cat_name == "Tragstruktur":
                    st.session_state.current_selections[cat_name][element].append(
                        {"measure": measure_names[0], "flaeche": 100.0, "anzahl": 1.0})
                else:
                    st.session_state.current_selections[cat_name][element].append(
                        {"measure": measure_names[0], "percent": 100.0})
                st.rerun()
            else:
                st.error("Bitte zuerst eine Massnahme über das Zahnrad erstellen.")

    energie_co2_total = 0
    if cat_name == "Fassade":
        st.divider()
        st.write("#### Energiebedarf")

        if "Energiebedarf" not in st.session_state.current_selections["Fassade"]:
            st.session_state.current_selections["Fassade"]["Energiebedarf"] = {"co2_per_a": 0.0, "jahre": 50,
                                                                               "pv_ausgleich": 0.0}

        edata = st.session_state.current_selections["Fassade"]["Energiebedarf"]
        if "pv_ausgleich" not in edata:
            edata["pv_ausgleich"] = 0.0

        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            edata["co2_per_a"] = st.number_input("kgCO2/a", value=float(edata.get("co2_per_a", 0.0)), step=10.0,
                                                 key=f"energie_co2_{lc}")
        with col_e2:
            edata["jahre"] = st.number_input("Anzahl Jahre", value=int(edata.get("jahre", 50)), step=1,
                                             key=f"energie_jahre_{lc}")
        with col_e3:
            edata["pv_ausgleich"] = st.number_input("PV-Ausgleich (%)", value=float(edata.get("pv_ausgleich", 0.0)),
                                                    min_value=0.0, max_value=100.0, step=5.0, key=f"energie_pv_{lc}")

        pv_factor = 1.0 - (edata["pv_ausgleich"] / 100.0)
        energie_co2_total = edata["co2_per_a"] * edata["jahre"] * pv_factor

    if calc_data:
        df_pie = pd.DataFrame(calc_data)
        df_pie["CO2_formatiert"] = df_pie["CO2 (kg)"].apply(lambda x: f"{x:,.2f}".replace(",", "'"))

        pie_chart = alt.Chart(df_pie).mark_arc().encode(
            theta=alt.Theta(field="CO2 (kg)", type="quantitative"),
            color=alt.Color(field="Element", type="nominal"),
            tooltip=[
                alt.Tooltip("Element:N"),
                alt.Tooltip("Massnahme:N"),
                alt.Tooltip("CO2_formatiert:N", title="CO2 (kg)")
            ]
        ).properties(width=300, height=300, title=f"CO2 Anteil - {cat_name}")
        st.altair_chart(pie_chart, use_container_width=True)

    if cat_name == "Fassade":
        energie_co2_str = f"{energie_co2_total:,.2f}".replace(",", "'")
        st.metric(label="Gesamter Energiebedarf (nach PV-Abzug)", value=f"{energie_co2_str} kgCO2")


with col_right:
    tab1, tab2, tab3, tab4 = st.tabs(["Fassade", "Dach", "Wände", "Tragstruktur"])
    with tab1:
        render_category("Fassade", areas["Fassade"])
    with tab2:
        render_category("Dach", areas["Dach"])
    with tab3:
        render_category("Wände", areas["Wände"])
    with tab4:
        render_category("Tragstruktur", areas["Tragstruktur"])

# --- BOTTOM SPALTE: Balkendiagramm Variantenvergleich ---
st.divider()
st.header("Variantenvergleich")

variants_to_compare = st.multiselect("Varianten auswählen", list(st.session_state.app_data["variants"].keys()))

if variants_to_compare:
    comparison_data = []

    for var_name in variants_to_compare:
        var_data = st.session_state.app_data["variants"][var_name]

        for cat_name, elements in var_data.items():
            for element_name, rows in elements.items():

                if cat_name == "Fassade" and element_name == "Energiebedarf":
                    pv_factor = 1.0 - (rows.get("pv_ausgleich", 0.0) / 100.0)
                    total_co2 = rows.get("co2_per_a", 0.0) * rows.get("jahre", 0) * pv_factor
                    if total_co2 > 0:
                        comparison_data.append({
                            "Variante": var_name,
                            "Element": "Energiebedarf (Fassade)",
                            "CO2 (kg)": total_co2
                        })
                else:
                    area = areas.get(cat_name, {}).get(element_name, 0)
                    measures_list = st.session_state.app_data["measures"].get(cat_name, [])

                    for row in rows:
                        co2_val = next((m["co2"] for m in measures_list if m["name"] == row["measure"]), 0)

                        if cat_name == "Tragstruktur":
                            total_co2 = co2_val * row.get("flaeche", 0) * row.get("anzahl", 0)
                        else:
                            total_co2 = area * co2_val * (row.get("percent", 0.0) / 100.0)

                        if total_co2 > 0:
                            element_label = f"{element_name} ({cat_name})" if cat_name != element_name else cat_name
                            comparison_data.append({
                                "Variante": var_name,
                                "Element": element_label,
                                "CO2 (kg)": total_co2
                            })

    if comparison_data:
        df_comp = pd.DataFrame(comparison_data)

        df_agg = df_comp.groupby(['Variante', 'Element'])['CO2 (kg)'].sum().reset_index()
        df_agg["CO2_formatiert"] = df_agg["CO2 (kg)"].apply(lambda x: f"{x:,.2f}".replace(",", "'"))

        bar_chart = alt.Chart(df_agg).mark_bar().encode(
            x=alt.X(
                'CO2 (kg):Q',
                title='Gesamt CO2 (kg)',
                axis=alt.Axis(labelExpr="replace(datum.label, /,/g, \"'\")")
            ),
            y=alt.Y('Variante:N', title='Varianten'),
            color=alt.Color('Element:N', title='Gebäudeelement'),
            tooltip=[
                alt.Tooltip('Variante:N'),
                alt.Tooltip('Element:N'),
                alt.Tooltip('CO2_formatiert:N', title='CO2 (kg)')
            ]
        ).properties(height=300)

        st.altair_chart(bar_chart, use_container_width=True)

        st.write("")

        df_export = df_agg[['Variante', 'Element', 'CO2 (kg)']].copy()
        df_export['CO2 (kg)'] = df_export['CO2 (kg)'].apply(lambda x: f"{x:,.2f}".replace(",", "'"))

        csv = df_export.to_csv(index=False, sep=";").encode('utf-8')
        st.download_button(
            label="📥 Daten als CSV exportieren",
            data=csv,
            file_name="co2_variantenvergleich.csv",
            mime="text/csv",
        )
    else:
        st.info("Die ausgewählten Varianten enthalten keine validen CO2-Werte.")
else:
    st.info("Bitte mindestens eine Variante auswählen, um das Vergleichs-Diagramm anzuzeigen.")