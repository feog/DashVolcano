# ************************************************************************************* #
#
# This creates a one-page layout, with a map, a TAS diagram, and AFM diagram, 
# a rock sample frequency radar plot. two rock composition sunburst plots
# 1) create_map_samples: creates the dataframe of samples to be drawn
# 2) displays_map_samples: draws the map
# 3) update_tas: draws the TAS diagram, possibly with selected points
# 4) download_tasdata: downloads the TAS data
#
# Author: F. Oggier
# Last update: Sep 3 2022
# ************************************************************************************* #


import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px

import geopandas as gpd
import json
from shapely.geometry import Polygon, LineString

import pandas as pd
import numpy as np
import ast

# links to the main app
from app import app

# import variables common to all files
# this includes loading the dataframes
from config_variables import *

# import functions to process GVP, GEOROC and PetDB data
from GVP_functions import *
from Georoc_functions import *
from PetDB_functions import *

# *************************#
#
# create a layout
#
# *************************#

disable = {}
for ts in all_tectonic_settings:
    disable[ts] = False

tectonic_options = []
for ts in all_tectonic_settings:
    tectonic_options.append({'label': ts,
                             'disabled': disable[ts],
                             'value': ts})
# GEOROC tectonic settings
# new_GEOROC_tectonic_settings = ([' all GEOROC', ' PetDB']+ GEOROC_tectonic_settings)
# new_GEOROC_tectonic_settings.remove(' Inclusions')
new_GEOROC_tectonic_settings = [' all GEOROC', ' PetDB'] + new_tectonic_settings

                                             
disable2 = {}
for ts in new_GEOROC_tectonic_settings:
    disable2[ts] = False

GEOROC_tectonic_options = []
for ts in new_GEOROC_tectonic_settings:
    GEOROC_tectonic_options.append({'label': ts.replace('Within ', 'Intra').replace('all', ''),
                                    'disabled': disable2[ts],
                                    'value': ts})
                             
disable3 = {}
for ch in GEOROC_rocks+chemicals_settings[0:1]:
    disable3[ch] = False

rocks_options = []
for r in GEOROC_rocks+chemicals_settings[0:1]:
    rocks_options.append({'label': ' '+r,
                          'disabled': disable3[r],
                          'value': r})
                             

layout = html.Div([
    # creates a layout with dbc
    dbc.Card(
        dbc.CardBody([
            # GEOROC data
            # **************************************************#
            dbc.Row([
                # title (h1) and subtitle (p)
                # main header h1
                html.H1(children="Map", className="title", ),
                # paragraph
                html.P(
                    children="Shows GVP volcanoes and the location of GEOROC samples. "
                             "Use the Where menu to zoom into a specific volcano. "
                             "Choose to display data from only GVP, only GEOROC, or both. "
                             "Use the rectangular selection or lasso tool (on the top right corner of the map) "
                             "to select a subset of rock samples, whose chemical composition will be shown " 
                             "in the TAS diagram below. Double-click the map to reset the selection.  "
                             "Use the display tectonic plates/ rift zone/ subduction zone/ intraplate zone check boxes "
                             "to add these zones to the map. Choose specific settings from GEOROC or GVP. ",
                    className="description",
                ),
            ], align='center', className='intro'),
            html.Br(),
            # *************************************************#
            # 2 menus
            # **************************************************#
            dbc.Row([
                # 1st column
                dbc.Col([
                    # first drop down
                    html.Div(children="Where", className="menu-title"),
                    dcc.Dropdown(
                        id="region-filter",
                        options=[{"label": region, "value": region} for region in grnames],
                        # default value
                        value="start",
                    ),
                    #
                    html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'}),
                    # checklist
                    dcc.Checklist(
                        id="db-filter",
                        style={'display': 'block'},
                        options=[
                                 {'label': ' tectonic plates', 'value': 'tectonic'},
                                 {'label': ' divergent plate boundaries', 'value': 'rift'},
                                 {'label': ' convergent plate boundares', 'value': 'subduction'},
                                 {'label': ' transform plate boundaries', 'value': 'intraplate'},
                                 ],
                        labelStyle={'margin-right': '5px'},
                        value=[None]*3,
                        className='check',
                    ),
                    #
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    html.Br()
                ], width=3),
                # empty column for alignment
                dbc.Col([
                ], width=1),
                # 2nd column
                dbc.Col([
                    #
                    html.Br(),
                    html.Div(children="Tectonic Settings", className="menu-title"),
                    dcc.Checklist(
                        id='GEOROC-tectonic-filter',
                        style={'display': 'block'},
                        options=GEOROC_tectonic_options,
                        value=[None]*len(GEOROC_tectonic_options),
                    ),
                    html.Br(),
                    html.Br(),
                    html.Br()
                
                ], width=3),
                # 3rd column
                dbc.Col([
                    # first drop down
                    html.Br(),
                    html.Div(children="Country Name", className="menu-title"),
                    dcc.Dropdown(
                        id="country-filter",
                        options=[
                            {"label": region, "value": region} for region in ['all'] + lst_countries
                        ],
                        # default value
                        value="all",
                    ),
                    # first checklist
                    dcc.Checklist(
                        id='tectonic-filter',
                        style={'display': 'block'},
                        options=tectonic_options,
                        value=['start'] * 10,
                    ),
                 
                ], width=3),
                
            ], align='center', ),
            html.Br(),

            # *************************************************#
            # map
            # **************************************************#
            dbc.Row([
                # inserts a graph
                # a dcc.Graph components expect a figure object
                # or a Python dictionary containing the plot’s data and layout.
                dbc.Col([
                    html.Div(
                        dcc.Graph(id="map"),
                    ),
                ], className='card', align='left', width=9),
                #
                # dbc.Col([
                # ], width=1
                # ),
                # rock menu 
                dbc.Col([
                    html.Div(children="Rock Density", className="menu-title"),
                    #
                    dcc.Checklist(
                        id='rocksopt',
                        style={'display': 'block'},
                        options=rocks_options,
                        value=[None]*len(rocks_options),
                    ),
                
                ], width=3),
            ]),
            html.Br(),

            # *************************************************#
            # chemical plots
            # **************************************************#
            dbc.Row([
                dbc.Col([
                    #
                    html.Br(),
                    html.Div(
                        
                    ),
                    html.Br(),
                ], width=2),   
                #
                dbc.Col([
                    #
                    html.Div(
                        html.Button('Download', id='button-1', n_clicks=0),
                        ),
                ], width=1), 
            ], align='center'),
            html.Br(),
            dbc.Row([
                # inserts a graph
                # a dcc.Graph components expect a figure object
                # or a Python dictionary containing the plot’s data and layout.
                dbc.Col([
                    #
                    html.Div(className="card",
                             children=[
                                       dcc.Graph(id="tas"),
                                       html.Div(id='tas-title3', style={'whiteSpace': 'pre-line'}),
                                      ],
                            ),
                    # html.Div(id='tas-title3', style={'whiteSpace': 'pre-line'}),
                    # dcc.Store stores the legends that are active
                    dcc.Store(id="store3"),
                ], ),
                #
                dbc.Col([
                    #
                    html.Div(className="card",
                        children=[
                                   dcc.Graph(id='afm'),
                                   ],
                    ),
                ], ),
            ], align='center'),
            html.Br(),
            # *************************************************#
            # major rock plots
            # **************************************************#
            dbc.Row([
                dbc.Col([
                    #
                    html.Div(className="card",
                        children=[
                                   dcc.Graph(id='radar'),
                                   ],
                        
                    ),
                    ], width=4),   
                #
                dbc.Col([
                    #
                    html.Div(className="card",
                        children=[
                                   dcc.Graph(id='rocksGEO'),
                                   ],
                    ),
                ], ),
                #
                dbc.Col([
                    #
                    html.Div(className="card",
                        children=[
                                   dcc.Graph(id='rocks'),
                                   ],
                    ),
                ], ),
                #
                ], align='center'),
            html.Br(),
                
        ]),
    ),
])


# ************************************#
#
# 1st callback for figure updates
#
# ************************************#
# to change checkboxes based on input, first column
@app.callback(
    dash.dependencies.Output("tectonic-filter", "options"),
    # from drop down
    dash.dependencies.Input("country-filter", "value"),
)

def set_tectonic_options(country_name):
    """ Updates tectonic choice based on country name
    """
    opts = update_tectonicmenu(country_name)

    return opts


@app.callback(
    # to the dcc.Graph with id='chem-chart-georoc'
    # cautious that using [] means a list, which causes error with a single argument
    [
        dash.dependencies.Output("map", "figure"),
        dash.dependencies.Output("map", "selectedData"),
        dash.dependencies.Output('textarea-example-output', 'children'),
    ],
           
    [
        # from drop down
        dash.dependencies.Input("region-filter", "value"),
        # from check list
        dash.dependencies.Input("db-filter", "value"),
        # from check list
        dash.dependencies.Input("tectonic-filter", "value"),
        # from check list
        dash.dependencies.Input("GEOROC-tectonic-filter", "value"),
        # from drop down
        dash.dependencies.Input("country-filter", "value"),
        # from check list
        dash.dependencies.Input("rocksopt", "value"),
        
    ],
)

def update_map(volcano_name, db, tect_GVP, tect_GEOROC, country, rocksopt):
    """

    Args:
        volcano_name
        db: choice of GEOROC or tectonic display
        tect_GVP: GVP tectonic settings
        tect_GEOROC: GEOROC tectonic settings
        country: GVP country
        rocks: which rocks to display
    Returns: returns a world map

    """
    
    if country != None:
        db.append('GVP')
    if ' PetDB' in tect_GEOROC:
        db.append('PetDB')
    if ' all GEOROC' in tect_GEOROC: 
        db.append('GEOROC')
    
    # default center and zoom
    thiscenter = {}
    thiszoom = 1.3
    
    # empty text
    tectext = ''
    
    # if a volcano name is given, zoom on this volcano
    if not (volcano_name is None) and not (volcano_name == "start"):
        # find gvp name corresponding to GEOROC name
        n = volcano_name
        # handles long names
        if n in dict_Georoc_sl.keys():
            n = dict_Georoc_sl[n]
        # automatic matching
        if n in dict_Georoc_GVP.keys():
            n = dict_Georoc_GVP[n]
        else:
            n = volcano_name.title()
           
        volrecord = dfv[dfv['Volcano Name'] == n]
        # if no eruption data, switches to other record
        if len(volrecord) == 0:
            volrecord = dfvne[dfvne['Volcano Name'] == n]
            
        # in case no GVP record is found
        if len(volrecord) > 0:            
            thiscenter = {'lat': float(volrecord['Latitude']), 'lon': float(volrecord['Longitude'])}
            thiszoom = 8
            tectext += volrecord['Country'] + ', '
            tectext += volrecord['Subregion'] + '\n'
            # GVP tectonic
            tectext += volrecord['Tectonic Settings']
           
        # handles long names
        if volcano_name in dict_Georoc_sl.keys():
            volcano_name = dict_Georoc_sl[volcano_name]
            
        # GEOROC tectonic    
        tects = dict_volcano_file[volcano_name]
        # removes file extension
        tects = [t.split('.csv')[0] for t in tects]
        # removes parts in case there is
        tects = [t.split('part')[0] for t in tects]
        tects = list(set(tects))
        tects = [t.replace('_', ' ') for t in tects]
        tectext += '\n'
        for t in tects:
            if 'Manual' not in t:
                tectext += t + '\n'
    
    chosenrocks = [c.strip() for c in rocksopt if c is not None] 
    dffig = create_map_samples(db, volcano_name, tect_GVP, tect_GEOROC, country, rocksopt)
    fig = displays_map_samples(dffig, thiszoom, thiscenter, db, tect_GVP, tect_GEOROC, country, chosenrocks)
    fig.update_layout(legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ))
    
    # this resets the selected points
    return [fig, None, tectext]


def create_map_samples(db, thisvolcano, tect_GVP, tect_GEOROC, country, rocksopt):
    """

    Args:
        db: choice of db from the check boxes
        thisvolcano: contains volcano from dropped down menu if any
        tect_GVP: to shortlist GVP tectonic settings
        tect_GEOROC: to shortlist GEOROC tectonic settings
        country: to shortlist GVP country
    Returns: returns a world map

    """
    # name of column
    thisname = 'Name'
    
    # retrieves tectonic settings
    tect_lst = [x.strip() for x in tect_GEOROC if x != None]
    
    # PetDB
    # checks if file exists 
    if 'PetDBaroundGVP.csv' in os.listdir('../GeorocDataset'):
        if 'PetDB' in tect_lst:
            # file exists, just reads it
            dfgeo = pd.read_csv('../GeorocDataset/PetDBaroundGVP.csv')   
            # from string back to list
            dfgeo['Volcano Name'] = dfgeo['Volcano Name'].apply(lambda x: set(ast.literal_eval(x)))
            dfgeo['Volcano Name'] = dfgeo['Volcano Name'].apply(lambda y: [x.split(';') for x in y])
            dfgeo['Volcano Name'] = dfgeo['Volcano Name'].apply(lambda y: list(set([item for sublist in y for item in sublist])))
            dfgeo['Volcano Name'] = dfgeo['Volcano Name'].apply(lambda x: [find_new_tect_setting(y) for y in x if y != ''] )
        else:
            # ROCK or ROCK no inc
            dfgeo = pd.DataFrame({'LATITUDE': [], 'LONGITUDE': [], 'SAMPLE ID': [], 'ROCK no inc': [], 'SIO2(WT%)mean': [], 'Volcano Name': []})
    else:
        # creates the file anyway
        dfgeo = createPetDBaroundGVP()
        
    dfgeo = dfgeo.rename(columns={"LATITUDE": "Latitude", "LONGITUDE": "Longitude"})
    dfgeo['db'] = ['PetDB']*len(dfgeo.index)
    dfgeo = dfgeo.rename(columns={'SAMPLE ID': thisname})    
    
    # loads GEOROC
    # lists files in the folder
    if 'GEOROCaroundGVP.csv' in os.listdir('../GeorocDataset'):
        if 'all GEOROC' in tect_lst:
            # file exists, just reads it
            dfgeo2 = pd.read_csv('../GeorocDataset/GEOROCaroundGVP.csv')   
            dfgeo2['Volcano Name'] = dfgeo2['Volcano Name'].apply(lambda x: list(set(ast.literal_eval(x))))
        else:
            # ROCK or ROCK no inc
            dfgeo2 = pd.DataFrame({'LATITUDE MIN': [], 'LATITUDE MAX': [], 'LONGITUDE MIN': [], 'LONGITUDE MAX': [], 'SAMPLE NAME': [], 'ROCK no inc': [], 'SIO2(WT%)mean': [], 'Volcano Name': [] })
    else:
        # creates the file anyway
        dfgeo2 = createGEOROCaroundGVP()

    # handles latitude and longitude
    # removes weird latitudes
    dfgeo2 =  dfgeo2[abs(dfgeo2['LATITUDE MAX']) <= 90]
    dfgeo2['Latitude'] = (dfgeo2['LATITUDE MIN'] + dfgeo2['LATITUDE MAX'])/2
    dfgeo2['Longitude'] = (dfgeo2['LONGITUDE MIN'] + dfgeo2['LONGITUDE MAX'])/2
    dfgeo2['db'] = ['Georoc']*len(dfgeo2.index)
    dfgeo2 = dfgeo2.rename(columns={'SAMPLE NAME': thisname})
    
    # ROCK or ROCK no inc
    dfgeo = dfgeo.append(dfgeo2[['Latitude', 'Longitude', 'db', 'Volcano Name', thisname, 'ROCK no inc']+[s+'mean' for s in chemicals_settings[0:1]]])
    
    # format tectonic setting names
    if len(set(tect_lst) & set([x.strip() for x in new_tectonic_settings])) > 0:
        # filter
        tect_lst = [x for x in tect_lst if (x != 'all GEOROC') & (x != 'PetDB')]
        dfgeo = dfgeo[dfgeo['Volcano Name'].map(lambda x: True if len(list(np.intersect1d(x, tect_lst))) > 0 else False)]
    
    # if a volcano name is given, higlights samples from this volcano
    if not (thisvolcano is None) and not (thisvolcano == "start"):
        dfzoom = load_georoc(thisvolcano)
        # handles latitude and longitude
        # removes weird latitudes
        dfzoom = dfzoom[abs(dfzoom['LATITUDE MAX'].astype(float)) <= 90]
        dfzoom['Latitude'] = (dfzoom['LATITUDE MIN'].astype(float) + dfzoom['LATITUDE MAX'].astype(float))/2
        dfzoom['Longitude'] = (dfzoom['LONGITUDE MIN'].astype(float) + dfzoom['LONGITUDE MAX'].astype(float))/2
        dfzoom['db'] = ['Georoc found']*len(dfzoom.index)
        dfzoom = dfzoom.rename(columns={'SAMPLE NAME': thisname})
        # compares the brown samples (displayed in brown) with the matched samples (so they are displayed in blue)
        if 'all GEOROC' in tect_lst:
            # find samples already present
            fnd = dfgeo['Latitude'].isin(dfzoom['Latitude']) & dfgeo['Longitude'].isin(dfzoom['Longitude']) 
            dfgeo.loc[fnd, 'db'] = 'Georoc found'
            # to get points plotted
            db.append('GEOROC')
            # add samples not present (if any)
            missing = ~(dfzoom['Latitude'].isin(dfgeo['Latitude']) & dfzoom['Longitude'].isin(dfgeo['Longitude']))
            dfmissing = dfzoom[missing]
        
            if len(dfmissing.index) > 0:
                dfgeo = dfgeo.append(dfmissing[['Latitude', 'Longitude', 'db', thisname]])
        else:
            dfgeo = dfgeo.append(dfzoom[['Latitude', 'Longitude', 'db', thisname]])
            # to get points plotted
            db.append('GEOROC')
        
    # GVP tectonic setting
    tect_GVP = [x.strip() for x in tect_GVP if ((x != None) and (x != 'start'))]
    if len(tect_GVP) == 0:
        tect_GVP = [x.strip() for x in all_tectonic_settings]
        # we may still want to display volcanoes with no tectonic setting known
        tect_GVP.append('Unknown')
    
    # GVP with eruption    
    condtc = (dfv['Tectonic Settings'].isin(tect_GVP))
    
    if country == 'all':
        dfgeo3 = dfv[condtc][['Longitude', 'Latitude', 'Volcano Name']]
        
    else:
        condc = (dfv['Country'] == country)
        condtc = (dfv['Tectonic Settings'].isin(tect_GVP))
        dfgeo3 = dfv[(condc)&(condtc)][['Longitude', 'Latitude', 'Volcano Name']]
        
    dfgeo3.loc[:, 'db'] = ['GVP with eruptions']*len(dfgeo3.index)
    dfgeo3 = dfgeo3.rename(columns={'Volcano Name': thisname})
    dfgeo = dfgeo.append(dfgeo3)
    
    # GVP without eruption
    condtc = (dfvne['Tectonic Settings'].isin(tect_GVP))

    if country == 'all':
        dfgeo4 = dfvne[condtc][['Longitude', 'Latitude', 'Volcano Name']]
    else:
        condc = (dfvne['Country'] == country)
        dfgeo4 = dfvne[(condc)&(condtc)][['Longitude', 'Latitude', 'Volcano Name']]
    
    dfgeo4.loc[:, 'db'] = ['GVP no eruption']*len(dfgeo4.index)
    dfgeo4 = dfgeo4.rename(columns={'Volcano Name': thisname})
    dfgeo = dfgeo.append(dfgeo4)
    
    # choose which Db(s) to display
    if 'GEOROC' in db:
        if 'PetDB' in db:
            if 'GVP' in db:
                cond = dfgeo['db'].isin(['Georoc', 'Georoc found', 'PetDB', 'GVP with eruptions', 'GVP no eruption'])
            else:
                cond = dfgeo['db'].isin(['Georoc', 'Georoc found', 'PetDB'])
        else:
            if 'GVP' in db:
                cond = dfgeo['db'].isin(['Georoc', 'Georoc found', 'GVP with eruptions', 'GVP no eruption'])
            else:
                cond = dfgeo['db'].isin(['Georoc', 'Georoc found'])
    else: 
        if 'PetDB' in db:
            if 'GVP' in db:
                cond = dfgeo['db'].isin(['PetDB', 'GVP with eruptions', 'GVP no eruption'])
            else:
                cond = dfgeo['db'].isin(['PetDB'])
        else: 
            if 'GVP' in db:
                cond = dfgeo['db'].isin(['GVP with eruptions', 'GVP no eruption'])
            else:
                cond = dfgeo['db'].isin([''])
    
    dfchoice = dfgeo[cond] 
    
    dfchoice['db'].replace({'Georoc': 'Rock sample (GEOROC)', 'Georoc found': 'Matching rock sample (GEOROC)', 
                            'GVP with eruptions': 'Volcano with known eruption data (GVP)', 
                            'GVP no eruption': 'Volcano with no known eruption data (GVP)'}, inplace=True)
    
    return dfchoice
    

def displays_map_samples(thisdf, thiszoom, thiscenter, db, tect_GVP, tect_GEOROC, country, rocksopt):
    """

        Args:
            thisdf: dataframe to be plotted on the world map
            thiszoom: zoom into the map
            thiscenter: center of the map
            db: choice of tectonic from the check boxes
            tect_GVP: to shortlist GVP tectonic settings
            tect_GEOROC: to shortlist GEOROC tectonic settings
            country: to shortlist GVP country
    Returns: returns a world map

        Returns:
            a map of the world

    """    

    if  len(list(set(rocksopt) & set(chemicals_settings))) > 0 and len([c for c in tect_GEOROC if c is not None]) > 0:
        colorcol = 'SIO2(WT%)mean'
        thisdf['SIO2(WT%)mean'] = thisdf['SIO2(WT%)mean'].fillna(0)
        # filters ranges of silica
        thisdf = thisdf[(thisdf['SIO2(WT%)mean'] >= 30) & (thisdf['SIO2(WT%)mean'] <= 80)]
        thisdf['SIO2(WT%)mean'] = thisdf['SIO2(WT%)mean'].round(-1)
        # color scheme
        this_color_discrete_map = {}
               
    else:
        colorcol = 'db'
        # color scheme
        this_color_discrete_map = {'Rock sample (GEOROC)': 'burlywood', 'PetDB': 'darkseagreen', 
                                   'Volcano with known eruption data (GVP)': 'maroon',
                                   'Volcano with no known eruption data (GVP)': 'black',
                                   'Matching rock sample (GEOROC)': 'cornflowerblue'}
                       
    if len(list(set(rocksopt) & set(GEOROC_rocks)))>0 and len([c for c in tect_GEOROC if c is not None])>0:
        # reads list format from a list in string format
        # ROCK for all rocks, and ROCK no inc to remove inclusions
        thisdf['ROCK no inc'] = thisdf['ROCK no inc'].apply(lambda y: ast.literal_eval(y) if type(y)==str else [])
        thisdf['count'] = thisdf['ROCK no inc'].apply(lambda y: sum([x[1] if x[0] in rocksopt else 0 for x in y]))
        
        # draws the samples on the map
        figtmp = px.density_mapbox(thisdf, lat="Latitude", lon="Longitude", 
                                   z='count', radius=30,
                                   # 'open-street-map', 'white-bg', 'carto-positron', 'carto-darkmatter',
                                   # 'stamen- terrain', 'stamen-toner', 'stamen-watercolor'.
                                   # Allowed values which do require a Mapbox API token are 'basic',
                                   # 'streets', 'outdoors', 'light', 'dark', 'satellite', 'satellite- streets'.
                                   mapbox_style="carto-positron",
                                   height=1000,
                                   width=1350,
                                   zoom=thiszoom,
                                   opacity=0.3,
                                   color_continuous_scale='inferno',
                                   hover_data = ['Latitude', 'Longitude', 'Name', 'db'],
                                   center = thiscenter,
                                   #title = ''
                                  )
        
        if colorcol == 'db':
            thiscolormap = thisdf["db"].replace(this_color_discrete_map)
        if colorcol == 'SIO2(WT%)mean':
            thiscolormap = thisdf['SIO2(WT%)mean']        
        thiscolorscale = px.colors.sequential.Jet[::-1]
            
        figtmp.add_trace(
            go.Scattermapbox(
                             lat=thisdf["Latitude"],
                             lon=thisdf["Longitude"],
                             mode="markers",
                             # showlegend=False,
                             customdata=thisdf['Latitude'].astype(str)+', '+thisdf['Longitude'].astype(str)+', '+thisdf['Name']+', '+thisdf['db'],
                             hovertemplate='%{customdata}',
                             marker={
                                      "color": thiscolormap,
                                      'colorscale': thiscolorscale,
                                    },
                            )
                        )
    else:
        # draws the samples on the map
        figtmp = px.scatter_mapbox(thisdf, lat="Latitude", lon="Longitude", 
            color = colorcol, color_discrete_map=this_color_discrete_map, color_continuous_scale=px.colors.sequential.Jet[::-1],
            # 'open-street-map', 'white-bg', 'carto-positron', 'carto-darkmatter', 'stamen- terrain', 'stamen-toner', 
            # 'stamen-watercolor'. Allowed values which do require a Mapbox API token are 'basic', 'streets', 'outdoors',
            # 'light', 'dark', 'satellite', 'satellite- streets'.
            mapbox_style="carto-positron",
            height = 1000,
            width = 1350,
            zoom = thiszoom,
            hover_data = ['Latitude', 'Longitude', 'Name', 'db'],
            center = thiscenter,
            #title = ''
            )
    
    fig = go.Figure()

    if ('tectonic' in db) or ('rift' in db) or ('subduction' in db) or ('intraplate' in db):
        # plots the plates first
        if 'tectonic' in db:
        
            with open('../tectonicplates-master/GeoJSON/PB2002_plates.json', 'r') as f:
                # this loads the json file  
                js_tect = json.load(f)
    
            # this creates a dataframe from the json
            gdf = gpd.GeoDataFrame.from_features(js_tect)
            
            
            if thiscenter == {}:
                gdfzoom = gdf
            else: 
                zoombox = gpd.GeoSeries([Polygon([(thiscenter['lon']-2, thiscenter['lat']-2), 
                                                  (thiscenter['lon']-2, thiscenter['lat']+2), 
                                                  (thiscenter['lon']+2, thiscenter['lat']+2), 
                                                  (thiscenter['lon']+2, thiscenter['lat']-2)])])
                                 
                gdfz =  gpd.GeoDataFrame({'geometry': zoombox, 'df1_data':[1]})                  
                # intersection of zoom box and plates
                gdfzoombox = gdfz.overlay(gdf, how='intersection')
                # extract from plates only those in the zoom box
                gdfzoom = gdf[gdf['PlateName'].isin(gdfzoombox['PlateName'])]
                
        
            fig = px.choropleth_mapbox(gdfzoom,
                           geojson=gdfzoom.geometry,
                           locations=gdfzoom.index,
                           color = 'PlateName',
                           opacity = 0.1,
                           mapbox_style="carto-positron",
                           center = thiscenter,
                           zoom=thiszoom)
            fig.update_traces(showlegend=False)
            
        if 'rift' in db:
            # source of the data
            # http://www-udc.ig.utexas.edu/external/plates/data.htm
        
            X, Y, names = read_gmt('ridge.gmt')
            
            if thiscenter == {}:
                #gdfzoom = gdf
                zoombox = None
            
            else: 
                zoombox = [thiscenter['lon'], thiscenter['lat']]
                                 
            for (x, y) in zip(X, Y):
                #
                idx = X.index(x)
                if not(zoombox is None):
                 
                    dfgmt = pd.DataFrame(data = {'x': x, 'y': y })
                    dfgmt = dfgmt[(dfgmt['x'] >= thiscenter['lon']-2) & (dfgmt['x'] <= thiscenter['lon']+2)]
                    dfgmt = dfgmt[(dfgmt['y'] >= thiscenter['lat']-2) & (dfgmt['y'] <= thiscenter['lat']+2)]
                     
                    if len(dfgmt.index) == 0:
                        x = []
                        y = []
                        
                fig.add_trace(
                    go.Scattermapbox(
                        lon =x,
                        lat =y,
                        # mode='none',
                        mode='lines',
                        line_color='blue',
                        opacity=0.6,
                        name=names[idx],
                    showlegend=False
                    ),
                )
            fig.update_layout(mapbox = {'style': "carto-positron", 'zoom': thiszoom,  'center': thiscenter})      
            
        if 'subduction' in db:
        
            X, Y, names = read_gmt('trench.gmt')
            
            if thiscenter == {}:
                #gdfzoom = gdf
                zoombox = None
            
            else: 
                zoombox = [thiscenter['lon'], thiscenter['lat']]
        
            for (x, y) in zip(X, Y):
                #
                idx = X.index(x)
                if not(zoombox is None):
                 
                    dfgmt = pd.DataFrame(data = {'x': x, 'y': y })
                    dfgmt = dfgmt[(dfgmt['x'] >= thiscenter['lon']-2) & (dfgmt['x'] <= thiscenter['lon']+2)]
                    dfgmt = dfgmt[(dfgmt['y'] >= thiscenter['lat']-2) & (dfgmt['y'] <= thiscenter['lat']+2)]
                    
                    if len(dfgmt.index) == 0:
                        x = []
                        y = []
                    
                fig.add_trace(
                    go.Scattermapbox(
                        lon =x,
                        lat =y,
                        # mode='none',
                        mode='lines',
                        line_color='red',
                        opacity=0.6,
                        name=names[idx],
                    showlegend=False
                    ),
                )
            fig.update_layout(mapbox = {'style': "carto-positron", 'zoom': thiszoom,  'center': thiscenter})  
            
        if 'intraplate' in db:
            
            X, Y, names = read_gmt('transform.gmt')
            
            if thiscenter == {}:
                #gdfzoom = gdf
                zoombox = None
            
            else: 
                zoombox = [thiscenter['lon'], thiscenter['lat']]
            
            for (x, y) in zip(X, Y):
                #
                idx = X.index(x)
                if not(zoombox is None):
                 
                    dfgmt = pd.DataFrame(data = {'x': x, 'y': y })
                    dfgmt = dfgmt[(dfgmt['x'] >= thiscenter['lon']-2) & (dfgmt['x'] <= thiscenter['lon']+2)]
                    dfgmt = dfgmt[(dfgmt['y'] >= thiscenter['lat']-2) & (dfgmt['y'] <= thiscenter['lat']+2)]
                    
                    if len(dfgmt.index) == 0:
                        x = []
                        y = []
            
                fig.add_trace(
                    go.Scattermapbox(
                        lon =x,
                        lat =y,
                        # mode='none',
                        mode='lines',
                        line_color='green',
                        opacity=0.6,
                        name=names[idx],
                    showlegend=False
                    ),
                )
            fig.update_layout(mapbox = {'style': "carto-positron", 'zoom': thiszoom,  'center': thiscenter})             
        
        # add samples on top of tectonic layouts                   
        for fd in figtmp.data:
            fig.add_trace(fd)
        
    else:

        fig = figtmp
        
    
            
    return fig

# ******************************************#
#
# 2nd callback for updates based on dropdown
#
# ********************************************#
@app.callback(
    [
    dash.dependencies.Output("store3", "data"),
    dash.dependencies.Output("tas-title3", "children")
    ],
    [
     # from drop down
     dash.dependencies.Input("region-filter", "value"),
     #
     dash.dependencies.Input("tas", "figure"),
     #
     dash.dependencies.Input("store3", "data"),
     #
     dash.dependencies.Input("tas", "restyleData"),
     # from selection tool
     dash.dependencies.Input("map", "selectedData"),
     #
     dash.dependencies.Input("GEOROC-tectonic-filter", "value"),
     #
     dash.dependencies.Input("country-filter", "value"),
     #
     dash.dependencies.Input("tectonic-filter", "value"),
     #
     dash.dependencies.Input("db-filter", "value"),
    ]
)
def update_store3(volcanoname, currentfig, store, restyle, selecteddata, tectg, country, tect, db):
    #
    # this function just answers to the callback
    # it redirects to the actual function which computes the subtitle
    #
               
    # checks whether there are markers on the TAS plot
    recs = [d for d in currentfig['data'] if 'customdata' in d.keys() and len(d['marker']['symbol'])>0] 
    if len(recs) > 0:
        #context = []
        store, subtitle = update_subtitle(currentfig, store, restyle, volcanoname, selecteddata, tectg, country, tect, db)
    else:
        subtitle = ''
    
    return store, subtitle       


@app.callback(
    # to the dcc.Graph with id='chem-chart-georoc'
    # cautious that using [] means a list, which causes error with a single argument
    [
    dash.dependencies.Output("tas", "figure"),
    dash.dependencies.Output("afm", "figure"),
    dash.dependencies.Output('radar','figure'),
    ],
    [
        # from drop down
        dash.dependencies.Input("region-filter", "value"),
        # from date drop down
        dash.dependencies.Input("db-filter", "value"),
        # from selection tool
        dash.dependencies.Input("map", "selectedData"),
        # from button
        dash.dependencies.Input('button-1', 'n_clicks'),
        # from GEOROC tectonic check boxes
        dash.dependencies.Input("GEOROC-tectonic-filter", "value"),
    ],
)

def update_TAS_download(volcano_name, db, selectedpts, button, tect_GEOROC):
    """

    Args:
        volcano_name: GEOROC name
        db: what to draw, GVP or GEOROC
        selectedpts: output from select tool, either box or lasso
        button: download button
    Returns: updates the TAS diagram and reset the selected points

    """
    
    # initializes TAS figure
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.85, 0.2], vertical_spacing=0.05,)
    fig.update_layout(title='<b>Chemical Rock Composition from Georoc</b> <br>', )
    # adds TAS layout
    fig = plot_TAS(fig)
    fig, TASdata = update_TAS(fig, volcano_name, db, selectedpts)
    
    # downloads
    download_TASdata(TASdata, button, volcano_name)
    
    # creates afm plot
    fig2 = update_afm(volcano_name,TASdata)
    
    # creates radar plot
    fig3 = update_radar(tect_GEOROC, volcano_name, TASdata)
       
    return fig, fig2, fig3
    

def update_TAS(fig, volcano_name, db, selectedpts):
    """

    Args:
        fig
        volcano_name
        selectedpts
    Returns: 

    """
    # for lasso tool:
    # lassoPoints = corner of the lasso, the only other key is points
    # for rectangular selection:
    # range = corner of the rectangle, the only other key is points
    # selectedpts['points'] is a list of dictionary
    # every dictionary contains a bunch of keys, including 'lon', 'lat', 'text'
    
    thisgeogr = pd.DataFrame()
    
    # keep only points
    if not(selectedpts is None):
        selectedpts = selectedpts['points']
        
        # loads PetDB
        dfgeopdb = pd.read_csv('../GeorocDataset/PetDBaroundGVP.csv')
        # loads GEOROC
        dfgeogr = pd.read_csv('../GeorocDataset/GEOROCaroundGVP.csv')    
        
        dfgeogr['LATITUDE'] = (dfgeogr['LATITUDE MIN']+ dfgeogr['LATITUDE MAX'])/2
        dfgeogr['LONGITUDE'] = (dfgeogr['LONGITUDE MIN'] + dfgeogr['LONGITUDE MAX'])/2
        
        # separate into dbs
        if type(selectedpts) == list:
            # GEOROC, only those in GEOROCaroundGVP file
            with_text = [[x['lon'], x['lat']] for x in selectedpts if 'customdata' in x.keys() and ('Rock sample (GEOROC)' in x['customdata'])]
            # GEOROC, those matching
            with_text_match = [[x['lon'], x['lat']] for x in selectedpts if 'customdata' in x.keys() and ('Matching rock sample (GEOROC)' in x['customdata'])]
            # PetDB
            without_text = [[x['lon'], x['lat']] for x in selectedpts if 'customdata' in x.keys() and 'PetDB' in x['customdata']]
        else:
            print('not list')
            
        morechemsh = ['FEOT(WT%)', 'CAO(WT%)', 'MGO(WT%)']
        if len(without_text) > 0:
            # plots points from PetDB
            pdb_idx = dfgeopdb.set_index(['LATITUDE', 'LONGITUDE'])
            thisgeopdb = pd.DataFrame()
        
            for lt_lg in without_text:
                lt = lt_lg[1]
                lg = lt_lg[0]
                thisgeopdb = thisgeopdb.append(pdb_idx.loc[(lt, lg), ['SIO2(WT%)','NA2O(WT%)','K2O(WT%)','CAO(WT%)','FEOT(WT%)','MGO(WT%)','MATERIAL']])
                   
            convert_df = {}
            for c in list(thisgeopdb):
                #string nan causes issues to ast
                thisgeopdb[c] = thisgeopdb[c].str.replace('nan','0')
                thisgeopdb[c] = thisgeopdb[c].apply(lambda x: ast.literal_eval(x))
                convert_df[c] = [item for sublist in list(thisgeopdb[c].values) for item in sublist]   
             
            thisgeopdb = pd.DataFrame(convert_df)    
            for c in list(thisgeopdb):
                if c != 'MATERIAL':
                    thisgeopdb[c] = thisgeopdb[c].astype(float)
            # recomputes rocks
            thisgeopdb = guess_rock(thisgeopdb)        
            # adds a db column
            thisgeopdb['db'] = ['PetDB']*len(thisgeopdb.index)
        
            thisgeopdb = thisgeopdb.dropna(subset=['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], how='all')
            # update dff to detect abnormal chemicals
            thisgeopdb = detects_chems(thisgeopdb, ['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], morechemsh, lbls2)
            # draws the scatter plot
            thisgeogr = thisgeogr.append(thisgeopdb) 
        
        # plots points from GEOROC
        gr_idx = dfgeogr.set_index(['LATITUDE', 'LONGITUDE'])
        whichfiles = []
        whichlocation = []
        for lt_lg in with_text:
            lt = lt_lg[1]
            lg = lt_lg[0]
            # find files with the selected data
            fnd_idx = list(gr_idx.loc[(lt, lg),'arc'].unique())
            whichfiles += fnd_idx
            # find locations with the selected data
            fnd_idx2 = list(gr_idx.loc[(lt, lg),'LOCATION'].unique())
            whichlocation += fnd_idx2
        # removes duplicates
        whichfiles = list(set(whichfiles))
        whichlocation = list(set(whichlocation))
        
        # matching samples are present, so we need to load them based on the name
        if len(with_text_match) > 0:
            dfloaded = load_georoc(volcano_name)
        else:
            dfloaded = pd.DataFrame()
        
        for pathcsv in whichfiles:
            # change name to latest file version
            pathcsv = fix_pathname(pathcsv)
            # loads the file
            dftmp = pd.read_csv("../GeorocDataset/%s" % pathcsv, low_memory=False, encoding='latin1') 
            # inclusion file has a different format
            if 'Inclusions_comp' in pathcsv:
                # updates columns to have the same format as dataframes from other files
                dftmp = fix_inclusion(dftmp)
            # locations
            dfloc = dftmp[dftmp['LOCATION'].isin(whichlocation)]     
            # adds names to rocks using TAS 
            dfloc = guess_rock(dfloc)
             
            dfloaded = dfloaded.append(dfloc)
          
        if len(dfloaded.index) > 0:
            # add normalization 
            dfloaded = with_FEOnorm(dfloaded)       
            # makes sure all 3 chemicals are present
            dfloaded = dfloaded.dropna(subset=['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], how='all')
            dfloaded = detects_chems(dfloaded, ['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], morechems, lbls)
            # adds a db column
            dfloaded['db'] = ['GEOROC']*len(dfloaded.index)
        # merges both PetDb and Georoc
        thisgeogr = thisgeogr.append(dfloaded) 
        
    else:
        
        if not (volcano_name is None) and not (volcano_name == "start"):
            dfloaded = load_georoc(volcano_name)
            # makes sure all 3 chemicals are present
            dfloaded = dfloaded.dropna(subset=['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], how='all')
            dfloaded = detects_chems(dfloaded, ['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], morechems, lbls)
            # adds a db column
            dfloaded['db'] = ['GEOROC']*len(dfloaded.index)
            thisgeogr = thisgeogr.append(dfloaded)
    
    if len(thisgeogr.index) > 0:
        
        # draws the scatter plot
        fig = plot_chem(fig, thisgeogr, ['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], lbls)
        
        # adds subtitles
        # take the first 4 and removes UNNAMED, if present
        majorrocks = [x for x in list(thisgeogr['ROCK'].value_counts().index[0:5]) if (x != 'UNNAMED' and x != 0)]
    
        # string
        strc = ''
        for mr in majorrocks:
            strc += mr  + ', '
        strc = strc[:-2]    
        
        fig.update_layout(
            annotations=[dict(xref='paper',
                                  yref='paper',
                                  x=0.5, y=-0.25,
                                  showarrow=False,
                                  text=strc)],
                )
    else:
        thisgeogr = pd.DataFrame()
        
    fig.update_layout(
        autosize=False,
        width = 900,
        height =700
        )     
    
    # this returns the dataframe thisgeogr
    return [fig, thisgeogr]

    
def download_TASdata(TASdata, button, volcano_name): 
    """

    Args:
        TASdata: dataframe that was plotted in TAS diagram
        button: download button
        volcano_name: GEOROC volcano name
    Returns: 

    """   
    # if download button is clicked
    # button = no of clicks on the button
    title = ''
    if button >= 1 and len(TASdata.index) > 0:
        #
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        # this is to make sure that only when the last event is button pressed, then the download happens
        if changed_id == 'button-1.n_clicks':
            # no volcano name
            if not (volcano_name is None) and not (volcano_name == "start"):
                title = str(volcano_name)
            else:
                if len(TASdata.index)>0:
                     title = 'selected_points'
            if not(title==''):     
                # cleans up, removes columns that are not needed for download
                locs = ['LOCATION-'+str(i) for i in range(1,9)]
                dropmore = ['GUESSED DATE', 'NA2O(WT%)+K2O(WT%)',
                            'excessFEO(WT%)', 'excessCAO(WT%)', 'excessMGO(WT%)', 'color', 'symbol',
                            'SIO2(WT%)old', 'NA2O(WT%)old', 'K2O(WT%)old']
                
                for loc in locs+dropmore:
                    if loc in list(TASdata): 
                        TASdata = TASdata.drop(loc, axis = 1) 
                
                # removes duplicates
                TASdata = TASdata.drop_duplicates()
                # saves to file
                TASdata.to_excel('download_%s.xlsx' % title, sheet_name='sheet 1', index=False)
    
    
# for the first figure part 1, only rocks
@app.callback(
    # to the dcc.Graph with id='rock-chart'
    # cautious that using [] means a list, which causes error with a single argument
    [
    dash.dependencies.Output('rocks', 'figure'),
    dash.dependencies.Output('rocksGEO', 'figure'),
    ],
    [
        # from country drop down
        dash.dependencies.Input("country-filter", "value"),
        # from GVP tectonic check boxes
        dash.dependencies.Input("tectonic-filter", "value"),
        # from GEOROC tectonic check boxes
        dash.dependencies.Input("GEOROC-tectonic-filter", "value"),
        #
        dash.dependencies.Input("region-filter", "value"),
    ],
)
def update_charts(country_name, tectonic, tect_GEOROC, thisvolcano):
    """

    Args:
        

    Returns: figure with sunburst chart of major rocks for volcanoes on the list

    """
  
    fig = go.Figure()
    # extracts volcanoes by country name/tectonic setting
    if not (country_name is None) and not (country_name == 'start'):
        volcanoesbycountry = extract_by_filter(country_name, tectonic)
    else:
        volcanoesbycountry = []

    # draw sunburst charts
    fig = update_rockchart(volcanoesbycountry, fig)
    
    thisdf = pd.DataFrame()
    db = ''
    
    # draw sunburst chart for GEOROC or PetDB
    if ' PetDB' in tect_GEOROC:
        dftmp = PetDB_majorrocks(tect_GEOROC)
        db += 'PetDB'
        
        if len(dftmp.index) > 0:
            # takes only whole rock
            dftmp = dftmp[dftmp['material'] == 'WR']
            # removes if no major rock
            dftmp = dftmp[dftmp['PetDB Major Rock 1'] != 'No Data']
             # adds db
            dftmp['db'] = ['PetDB']*len(dftmp.index)
            # rename columns
            dftmp.rename(columns={'PetDB Major Rock 1': 'db Major Rock 1', 'PetDB Major Rock 2': 'db Major Rock 2', 'PetDB Major Rock 3': 'db Major Rock 3'}, inplace=True)
            thisdf = thisdf.append(dftmp)
            
    
    if ' all GEOROC' in tect_GEOROC:
        # GEOROC
        dftmp = GEOROC_majorrocks(tect_GEOROC)
        db += 'GEOROC'
        
        if len(dftmp.index) > 0:
            # takes only whole rock and removes if no major rock
            dftmp = dftmp[(dftmp['material'] == 'WR') & (dftmp['GEOROC Major Rock 1'] != 'No Data')]
            # adds db
            dftmp['db'] = ['GEOROC']*len(dftmp.index)
            # rename columns
            dftmp.rename(columns={'GEOROC Major Rock 1': 'db Major Rock 1', 'GEOROC Major Rock 2': 'db Major Rock 2', 'GEOROC Major Rock 3': 'db Major Rock 3'}, inplace=True)
            thisdf = thisdf.append(dftmp) 
            
    # some volcanoes appear in two tectonic settings, this deduplicates
    thisdf = thisdf.drop_duplicates()
    
    if len(thisdf.index):
        thisdf = thisdf[['Volcano Name', 'db Major Rock 1','db Major Rock 2','db Major Rock 3', 'cnt 1', 'cnt 2', 'cnt 3', 'db']]
        
    fig2 = update_GEOrockchart(thisdf, db)
    
    return fig, fig2
    
        
def update_radar(tect_GEOROC, thisvolcano, TASdata):
    
    # retrieves tectonic settings
    tect_lst = [x.strip() for x in tect_GEOROC if x!= None]
    
    # PetDB
    if 'PetDB' in tect_lst:
        # loads
        dfgeo = pd.read_csv('../GeorocDataset/PetDBaroundGVP.csv')[['ROCK', 'Volcano Name']]  
        # from string back to list
        dfgeo['Volcano Name'] = dfgeo['Volcano Name'].apply(lambda x: set(ast.literal_eval(x)))
        dfgeo['Volcano Name'] = dfgeo['Volcano Name'].apply(lambda y: [x.split(';') for x in y])
        dfgeo['Volcano Name'] = dfgeo['Volcano Name'].apply(lambda y: list(set([item for sublist in y for item in sublist])))
        dfgeo['Volcano Name'] = dfgeo['Volcano Name'].apply(lambda x: [find_new_tect_setting(y) for y in x if y!='' ] ) 
    elif 'all GEOROC' in tect_lst:
        dfgeo = pd.read_csv('../GeorocDataset/GEOROCaroundGVP.csv')[['ROCK', 'Volcano Name']]  
        # from string back to list 
        dfgeo['Volcano Name'] = dfgeo['Volcano Name'].apply(lambda x: list(set(ast.literal_eval(x))))
    else:
        # empty
        dfgeo = pd.DataFrame({'ROCK':[], 'Volcano Name':[]}) 
    
    # format tectonic setting names
    if len(set(tect_lst) & set([x.strip() for x in new_tectonic_settings]))>0:  
        # filter
        tect_lst = [x for x in tect_lst if (x!='all GEOROC')&(x!='PetDB')]
        dfgeo = dfgeo[dfgeo['Volcano Name'].map(lambda x: True if len(list(np.intersect1d(x, tect_lst)))>0 else False)]
        if len(dfgeo.index)==0:
            # empty
            dfgeo = pd.DataFrame({'ROCK':[], 'Volcano Name':[]})         
    
    # reads list format from a list in string format
    dfgeo['ROCK'] = dfgeo['ROCK'].apply(lambda y: ast.literal_eval(y) if type(y)==str else [])
    #  
    rlist = []
    for tr in GEOROC_rocks:
        rcount = dfgeo['ROCK'].apply(lambda y: sum([x[1] if x[0]==tr else 0 for x in y])).sum()
        rlist.append(rcount)
    
    fig = go.Figure()
    
    if sum(rlist) > 0:
        fig.add_trace(go.Scatterpolar(
            r=[r*(100/sum(rlist)) for r in rlist],
            theta=GEOROC_rocks,
            fill='toself',
            fillcolor='cadetblue',
            line_color='grey',
            name=' '.join(tect_lst)
        ))
    
    if len(TASdata.index) > 0:
        rcount = TASdata['ROCK'].value_counts() 
    else:
        if thisvolcano!='start' and thisvolcano!=None:
            rcount = load_georoc(thisvolcano)['ROCK'].value_counts()
        else:
            rcount = {}
    
    rlist = []      
    if len(list(rcount.keys())) > 0:      
        for tr in GEOROC_rocks:
            if tr in rcount.keys():
                rlist.append(rcount[tr])
            else:
                rlist.append(0)
        
    if sum(rlist) > 0:  
        fig.add_trace(go.Scatterpolar(
            r=[r*(100/sum(rlist)) for r in rlist],
            theta=GEOROC_rocks,
            fillcolor='indianred',
            line_color='firebrick',
            fill='toself',
            opacity = 0.5, 
            name=thisvolcano
        ))
    
    fig.update_layout(
        title='<b>Rock Sample Frequency</b> <br>',
        polar=dict(
            radialaxis=dict(
            visible=True,
            range=[0, 50]
        )),
      showlegend=False
    )       
       
    return fig

    
def update_afm(volcanoname,TASdata):
    """
    """
  
    if volcanoname in ['start', None] and len(TASdata.index) == 0:
        fig = px.scatter_ternary(pd.DataFrame({"FEOT(WT%)":[0], 'NA2O(WT%)+K2O(WT%)':[0],'MGO(WT%)':[0]}), a="FEOT(WT%)", b='NA2O(WT%)+K2O(WT%)', c='MGO(WT%)')
    else:
        custom_marker_symbols = {'WR': 'circle', 'GL': 'diamond', 'INC': 'square'}
        if len(TASdata.index) > 0:
            dftmp = TASdata[['FEOT(WT%)','NA2O(WT%)', 'K2O(WT%)','MGO(WT%)','MATERIAL']]
        else: 
            dftmp = load_georoc(volcanoname)[['FEOT(WT%)','NA2O(WT%)', 'K2O(WT%)','MGO(WT%)','MATERIAL']]
        dftmp['NA2O(WT%)+K2O(WT%)'] = dftmp['NA2O(WT%)']+dftmp['K2O(WT%)']
        dftmp['MATERIAL'] = dftmp['MATERIAL'].str.split('[').str[0].str.strip()
        fig = px.scatter_ternary(dftmp, a="FEOT(WT%)", b='NA2O(WT%)+K2O(WT%)', c='MGO(WT%)', symbol='MATERIAL', symbol_map = custom_marker_symbols)
    
    fig.add_trace(
    go.Scatterternary(a=[39, 50, 56, 53, 45, 26],
                      b=[11, 14, 18, 28, 40, 70],
                      c=[50, 36, 26, 20, 15, 4],
                      mode='lines',
                      marker=dict(color='purple'),
                      line=dict(width=4),
                      name = '',
                      showlegend=False)
    )
    fig.update_layout(
        title='<b>AFM diagram</b><br>',
        autosize=False,
        width = 900,
        height =700
        ) 
    
    
    return fig
       
     
