import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json
from copy import deepcopy

@st.cache_data
def load_map_json(path):
    with open(path) as response:
        geojson = json.load(response)
    return geojson

def load_data(path):
    df = pd.read_csv(path)
    return df

geojson = load_map_json("./data/raw/georef-switzerland-kanton.geojson")

df_raw = pd.read_csv("./data/raw/renewable_power_plants_CH.csv",
                   dtype={"fips": str})

df = deepcopy(df_raw)

def map_canton_name(row):
    cantons_dict = {
    'TG':'Thurgau', 
    'GR':'Graubünden', 
    'LU':'Luzern', 
    'BE':'Bern', 
    'VS':'Valais',                
    'BL':'Basel-Landschaft', 
    'SO':'Solothurn', 
    'VD':'Vaud', 
    'SH':'Schaffhausen', 
    'ZH':'Zürich', 
    'AG':'Aargau', 
    'UR':'Uri', 
    'NE':'Neuchâtel', 
    'TI':'Ticino', 
    'SG':'St. Gallen', 
    'GE':'Genève',
    'GL':'Glarus', 
    'JU':'Jura', 
    'ZG':'Zug', 
    'OW':'Obwalden', 
    'FR':'Fribourg', 
    'SZ':'Schwyz', 
    'AR':'Appenzell Ausserrhoden', 
    'AI':'Appenzell Innerrhoden', 
    'NW':'Nidwalden', 
    'BS':'Basel-Stadt'}
    
    return cantons_dict.get(row['canton'])

df['kan_name'] = df.apply(map_canton_name, axis=1)
df.energy_source_level_3 = df.energy_source_level_3.fillna('')

st.title("Visulaization of energy production in Switzerland")
st.header("Energy production by Kanton")

show_data = st.checkbox(label="Include data table with visual")

left_column, middle_column, right_column = st.columns([1,1,1])

metric = left_column.radio(label='Metric:', options=['production','tariff','electrical_capacity'])

sources1 = ["All sources"]+sorted(pd.unique(df["energy_source_level_2"]))
source1 = middle_column.selectbox(label="Select an energy source:", options=sources1)

if source1 == "Bioenergy":
    sources2 = ["All types"]+sorted(pd.unique(df[df["energy_source_level_2"]=="Bioenergy"]["energy_source_level_3"]))
    source2 = right_column.selectbox(label="Source type:", options=sources2)
else:
    right_column.text("")
    source2 = "All types"

if source1 == "All sources":
    if metric == "electrical_capacity":
        df_source = df.groupby("kan_name").apply(lambda x: np.average(x.electrical_capacity, weights=x.production)).reset_index().rename(columns={0: "electrical_capacity"})
    else:
        df_source = df.groupby("kan_name").agg({metric: 'sum'}).reset_index()
elif source1 == "Bioenergy":
    if source2 == "All types":
        if metric == "electrical_capacity":
            df_source = df[df["energy_source_level_2"] == source1].groupby("kan_name").apply(lambda x: np.average(x.electrical_capacity, weights=x.production)).reset_index().rename(columns={0: "electrical_capacity"})
        else:
            df_source = df[df["energy_source_level_2"] == source1].groupby("kan_name").agg({metric: 'sum'}).reset_index()
    else:
        if metric == "electrical_capacity":
            df_source = df[(df["energy_source_level_2"] == source1) & (df["energy_source_level_3"] == source2)].groupby("kan_name").apply(lambda x: np.average(x.electrical_capacity, weights=x.production)).reset_index().rename(columns={0: "electrical_capacity"})
        else:
            df_source = df[(df["energy_source_level_2"] == source1) & (df["energy_source_level_3"] == source2)].groupby("kan_name").agg({metric: 'sum'}).reset_index()
else:
    if metric == "electrical_capacity":
        df_source = df[df["energy_source_level_2"] == source1].groupby("kan_name").apply(lambda x: np.average(x.electrical_capacity, weights=x.production)).reset_index().rename(columns={0: "electrical_capacity"})
    else:
        df_source = df[df["energy_source_level_2"] == source1].groupby("kan_name").agg({metric: 'sum'}).reset_index()

st.subheader("Energy production map:")
fig = px.choropleth_mapbox(df_source, geojson=geojson, 
                        color=metric,
                        locations="kan_name", featureidkey="properties.kan_name",
                        center={"lat": 47.0, "lon": 8.0},
                        mapbox_style="carto-positron", zoom=6.5)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig)

if show_data:
    st.subheader("Energy production data:")
    st.dataframe(data=df_source)