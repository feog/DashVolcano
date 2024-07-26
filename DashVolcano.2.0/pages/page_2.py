# ************************************************************************************* #
#
# This creates a one-page layout, that hosts side-by-side comparison of two volcanoes,
# in terms of TAS diagrams, Harker diagrams, and respective known VEI and rocks.
# Contains two functions:
# 1) update_veichart: creates the VEI plot
# 2) update_oxyde: creates the Harker diagrams
#
# Author: F. Oggier
# Last update: 23 Sep 2023 
# ************************************************************************************* #


import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import json

import pandas as pd
import numpy as np

# links to the main app
from app import app

# import variables common to all files
# this includes loading the dataframes
from config_variables import *

# import functions to process GVP and GEOROC data
from GVP_functions import *
from Georoc_functions import *


# *************************#
#
# create a layout
#
# *************************#

layout = html.Div([
    # creates a layout with dbc
    dbc.Card(
        dbc.CardBody([
            # GEOROC data
            # **************************************************#
            dbc.Row([
                # title (h1) and subtitle (p)
                # main header h1
                html.H1(children="TAS and Harker Diagrams", className="title", ),
                # paragraph
                html.P(
                    children=["Extracts data per volcano. "
                             "The chemical composition is coming from ",
                             html.A("Georoc", href="https://georoc.eu/georoc/new-start.asp", target="_blank"),
                             ", names may be aggregated "
                             "as indicated. The eruption dates can be filtered if available. "
                             "Different symbols correspond to different materials: WR=whole rock, "
                             " GL=volcano glass, INC=inclusion and MIN=mineral. "
                             "The corresponding Harker Diagram is shown. "
                             "The VEI (volcanic explosity index) data is then extracted from ",
                             html.A("GVP", href="https://volcano.si.edu/", target="_blank"), 
                             " with eruption dates. "
                             "If a mapping of dates is found between the two, it is indicated.  "],
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
                    html.Div(children="Volcano Name", className="menu-title"),
                    dcc.Dropdown(
                        id="region-filter",
                        options=[{"label": region, "value": region} for region in grnames],
                        # default value
                        value="start",
                    ),
                    # second drop down
                    html.Div(children="Eruption date(s)", className="menu-title"),
                    dcc.Dropdown(
                        id="erup-filter",
                        options=[{"label": region, "value": region} for region in []],
                        # default value
                        value="all",
                        clearable=False,
                    ),
                    #
                   
                    
                ], width=3),
                # empty column to create alignment
                dbc.Col([
                ], width=3),
                # second column
                dbc.Col([
                    # first drop down
                    html.Div(children="Volcano Name", className="menu-title"),
                    dcc.Dropdown(
                        id="region-filter2",
                        options=[{"label": region, "value": region} for region in grnames],
                        # default value
                        value="start",
                    ),
                    # second drop down
                    html.Div(children="Eruption date(s)", className="menu-title"),
                    dcc.Dropdown(
                        id="erup-filter2",
                        options=[{"label": region, "value": region} for region in []],
                        # default value
                        value="all",
                        clearable=False,
                    ),
                    #
                    
                ], width=3),
                # empty column to create alignment
                dbc.Col([
                ], width=3),
            ], align='center', ),
            html.Br(),

            # *************************************************#
            # chemical plots and GVP events
            # **************************************************#
            dbc.Row([
                # inserts a graph
                # a dcc.Graph components expect a figure object
                # or a Python dictionary containing the plot’s data and layout.
                dbc.Col([
                    # first plot
                    html.Div(
                        dcc.Graph(id="chem-chart-georoc"),
                    ),
                    #
                    html.Div(id='tas-title', style={'whiteSpace': 'pre-line'}),
                    # dcc.Store stores the legends that are active
                    dcc.Store(id="store"),
                    #
                    html.Div(
                        dcc.Graph(id='oxyde-chart', style={'height': '1000px'}),
                    ),
                    # second plot
                    html.Div(
                        dcc.Graph(id="vei-chart"),
                    ),
                ], className="card"),
                dbc.Col([
                    # first plot
                    html.Div(
                        dcc.Graph(id="chem-chart-georoc2"),
                    ),
                    #
                    html.Div(id='tas-title2', style={'whiteSpace': 'pre-line'}),
                    # dcc.Store stores the legends that are active
                    dcc.Store(id="store2"),
                    #
                    html.Div(
                        dcc.Graph(id='oxyde-chart2', style={'height': '1000px'}),
                    ),
                    # second plot
                    html.Div(
                        dcc.Graph(id="vei-chart2"),
                    ),
                ], className="card"),
            ], align='center')
        ]),
    ),
])


# ************************************#
#
# callbacks for menu updates
#
# ************************************#
# part 1
@app.callback(
    dash.dependencies.Output("erup-filter", "options"),
    dash.dependencies.Output("erup-filter", "value"),
    # from drop down
    dash.dependencies.Input("region-filter", "value"),
)
def set_date_options(volcano_name):
    """

    Args:
        volcano_name: name of a chosen volcano

    Returns:  Updates eruption dates choice based on volcano name

    """
    opts = update_onedropdown(volcano_name)

    return opts, 'all'

# part 2
@app.callback(
    dash.dependencies.Output("erup-filter2", "options"),
    dash.dependencies.Output("erup-filter2", "value"),
    # from drop down
    dash.dependencies.Input("region-filter2", "value"),
)
def set_date_options2(volcano_name2):
    """

    Args:
        volcano_name2: name of a chosen volcano

    Returns:  Updates eruption dates choice based on volcano name

    """
    opts2 = update_onedropdown(volcano_name2)

    return opts2, 'all'


# ************************************#
#
# callbacks for figure updates
#
# ************************************#
# part 1
@app.callback(
    # to the dcc.Graph with id='chem-chart-georoc'
    # cautious that using [] means a list, which causes error with a single argument
    [
        dash.dependencies.Output("chem-chart-georoc", "figure"),
        dash.dependencies.Output("vei-chart", "figure"),
        dash.dependencies.Output('oxyde-chart','figure'),
    ],
    [
        # from drop down
        dash.dependencies.Input("region-filter", "value"),
        # from date drop down
        dash.dependencies.Input("erup-filter", "value"),
    ],
)
def update_charts_rock_vei(volcano_name, date):
    """

    Args:
        volcano_name: name of volcano
        date: eruptions dates, possibly all

    Returns: Updates plots based on user's inputs, for first volcano

    """
    
    # first figure
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.85, 0.2], vertical_spacing=0.05,)
    fig, tmp = update_chemchart(volcano_name, fig, date)
    fig = add_alkaline_line(fig)
    
    figa = go.Figure()
    figa = update_oxyde(figa,tmp)
    figa = add_alkaline_series(figa)
    # second figure
    fig2 = go.Figure()
    fig2, fndmatch = update_veichart(volcano_name, fig2, date) 	

    return fig, fig2, figa
    

@app.callback(
    [
    dash.dependencies.Output("store", "data"),
    dash.dependencies.Output("tas-title", "children")
    ],
    [
     # from drop down
     dash.dependencies.Input("region-filter", "value"),
     # from date drop down
     dash.dependencies.Input("erup-filter", "value"),
     #
     dash.dependencies.Input("chem-chart-georoc", "figure"),
     #
     dash.dependencies.Input("store", "data"),
     #
     dash.dependencies.Input("chem-chart-georoc", "restyleData"),
    ]
)
def update_store(volcanoname, date, currentfig, store, restyle):
    #
    # this function just answers to the callback
    # it redirects to the actual function which computes the subtitle
    #
    recs = [d for d in currentfig['data'] if 'customdata' in d.keys() and len(d['marker']['symbol'])>0] 
    if len(recs) > 0:
        store, subtitle = update_subtitle(currentfig, store, restyle, volcanoname, date)
    else:
        subtitle = ''
                 
    return store, subtitle       


# part 2
@app.callback(
    # to the dcc.Graph with id='chem-chart-georoc'
    # cautious that using [] means a list, which causes error with a single argument
    [
        dash.dependencies.Output("chem-chart-georoc2", "figure"),
        dash.dependencies.Output("vei-chart2", "figure"),
        dash.dependencies.Output('oxyde-chart2','figure'),
    ],
    [
        # from drop down
        dash.dependencies.Input("region-filter2", "value"),
        # from date drop down
        dash.dependencies.Input("erup-filter2", "value"),
    ]
)
def update_charts_rock_vei2(volcano_name2, date2):
    """

    Args:
        volcano_name2: name of a volcano
        date2: eruptions dates, possibly all

    Returns: Updates plots based on user's inputs, for second volcano

    """

    # first figure
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.85, 0.2], vertical_spacing=0.05,)
    fig, tmp = update_chemchart(volcano_name2, fig, date2)
    fig = add_alkaline_line(fig)
    figa = go.Figure()
    figa = update_oxyde(figa,tmp)
    figa = add_alkaline_series(figa)

    # second figure
    fig2 = go.Figure()
    fig2, fndmatch = update_veichart(volcano_name2, fig2, date2)


    return fig, fig2, figa

@app.callback(
    [
    dash.dependencies.Output("store2", "data"),
    dash.dependencies.Output("tas-title2", "children")
    ],
    [
     # from drop down
     dash.dependencies.Input("region-filter2", "value"),
     # from date drop down
     dash.dependencies.Input("erup-filter2", "value"),
     #
     dash.dependencies.Input("chem-chart-georoc2", "figure"),
     #
     dash.dependencies.Input("store2", "data"),
     #
     dash.dependencies.Input("chem-chart-georoc2", "restyleData"),
    ]
)
def update_store2(volcanoname2, date2, currentfig2, store2, restyle2):
    #
    # this function just answers to the callback
    # it redirects to the actual function which computes the subtitle
    #
    recs = [d for d in currentfig2['data'] if 'customdata' in d.keys() and len(d['marker']['symbol'])>0] 
    if len(recs) > 0:
        store2, subtitle2 = update_subtitle(currentfig2, store2, restyle2, volcanoname2, date2)
    else:
        subtitle2 = ''
             
    return store2, subtitle2    

# ********************************************************#
#
# Functions for the 4rth callback
# * update_chemchart is in Georoc_functions
# **********************************************************#

def update_veichart(thisvolcano_name, thisfig, thisdate):
    """

    Args:
        thisvolcano_name: name of a GEOROC volcano
        thisfig: figure to be updated
        thisdate: chosen eruption dates, possibly all

    Returns: Updates the VEI content from GVP

    """
    these_annotations = []
    # just some bogus values that never appear as dates to initialize this variable
    date_gvp = [1.2, 1.2]
    vei_ticks = {}
    for j in range(9):
        vei_ticks[j] = 'VEI '+str(j)
    vei_ticks[9] = 'Unknown VEI'

    fndyr = []
    if not (thisvolcano_name is None) and not (thisvolcano_name == 'start'):
        n = thisvolcano_name
        # handles long names
        if n in dict_Georoc_sl.keys():
            n = dict_Georoc_sl[n]
        # automatic matching
        if n in dict_Georoc_GVP.keys():
            n = dict_Georoc_GVP[n]
        else:
            n = thisvolcano_name.title()
        # looks for the name in the eruption list of GVP
        if n in lst_names:
            datav = retrieve_vinfo(n, dfv, df, allrocks)
            c_r, c_g, c_b = rocks_to_color(datav[2])
            thiscolor = (c_r, c_g, c_b)

            # VEI
            dvei = datav[1]
            cnts = []
            veirange = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
            for i in veirange[:-1]:
                cnts.append(len([x for x in dvei if x == i]))

            cnts.append(len([x for x in dvei if not (type(x) == str)]))
            dfvei = pd.DataFrame(data={'VEI': cnts, 'VEI range': veirange})

            # add VEI data
            thisfig.add_traces(
                go.Bar(
                    x=dfvei['VEI range'],
                    y=dfvei['VEI'],
                    marker_color='rgb' + str(thiscolor),
                    name=n
                ),
            )

            # matches GVP dates
            if not ((thisdate == 'all') or (thisdate == 'start')):
                date_gvp = match_GVPdates(thisvolcano_name,thisdate,n)
        
            # dates from GVP
            ddate = datav[3]
            ndate = len(ddate[0])
            dd = []
            for i in range(ndate):
                begend = [x[i] for x in ddate]
                beg = [begend[i] for i in range(0, len(begend), 2)]
                end = [begend[i] for i in range(1, len(begend), 2)]
                dds = ''
                for j in range(3):
                    if type(beg[j]) == str:
                        dds += beg[j] + '-'
                if len(dds) > 0:
                    dds = dds[:-1]
                dde = ''
                for j in range(3):
                    if type(end[j]) == str:
                        dde += end[j] + '-'
                if len(dde) > 0:
                    dde = dde[:-1]
                dd.append([dds, dde])

            # add GVP dates to plot
            fndyr = []
            for i in range(10):
                idx = []
                for j in range(len(dvei)):
                    if i < 9:
                        if dvei[j] == veirange[i]:
                            idx.append(j)
                    else:
                        if not (type(dvei[j]) == str):
                            idx.append(j)
                dfd = pd.DataFrame(data={'date': [dd[j] for j in idx]})
                # this matches dates between georoc and gvp
                fndyr_i = []
                for dse in [dd[j] for j in idx]:
                    yr = [[], []]
                    for j in range(2):
                        if '-' in dse[j]:
                            yr[j] = dse[j].split('-')[-1]
                        else:
                            yr[j] = dse[j]

                    if yr[0] == date_gvp[0] and yr[1] == date_gvp[1]:
                        fndyr_i.append(dse)
                    else:
                        fndyr_i.append(0)
                fndyr.append(fndyr_i)

                thisfig.add_traces(
                    go.Scatter(
                        x=[i] * cnts[i],
                        y=[yi + .5 for yi in range(cnts[i])],
                        mode='markers',
                        # marker_color = 'rgb'+str(thiscolor),
                        marker_symbol='circle',
                        name='eruption date',
                        customdata=dfd['date'],
                        hovertemplate='%{customdata}',
                        showlegend=False
                    ),
                )

                # updates found matches
                if len(fndyr[i]) > 0:
                    y_a = [k for k in range(len(fndyr[i])) if fndyr[i][k] != 0]
                    x_a = i
                    if len(y_a) > 0:
                        y_a = y_a[0] + 1
                        these_annotations += [dict(x=x_a, y=y_a,
                                                  text='eruption match',
                                                  showarrow=True,
                                                  arrowhead=2
                                                  )]

            # add rock composition to caption
            datav2 = datav[2]
            strc = ''
            hasminor = False
            for i in range(1, 10):
                if i in datav2 and i <= 4:
                    strc += 'Major Rock ' + str(i) + ': ' + str(rock_col[datav2.index(i)]) + ' '
                if i in datav2 and i >= 5:
                    if hasminor == False:
                        strc += '<br>'
                        hasminor = True
                    strc += ' Minor Rock ' + str(i) + ': ' + str(rock_col[datav2.index(i)])

            thisfig.update_layout(
                title=go.layout.Title(
                    text='<b>VEI data from GVP</b> <br>',
                    # xref="paper",
                    x=0),
                annotations=[dict(xref='paper',
                                  yref='paper',
                                  x=0.5, y=-0.25,
                                  showarrow=False,
                                  text=strc)] + these_annotations,
                xaxis=dict(
                    tickmode='array',
                    tickvals=[x for x in range(10)],
                    ticktext=[vei_ticks[x] for x in range(10)]

                )
            )

    else:
        thisfig.update_layout(title='<b>VEI data from GVP</b> <br>', )
        thisfig.add_traces(
            go.Bar(
                x=[],
                y=[],
            ),
        )

    return thisfig, fndyr

    
def update_oxyde(thisfig,thisdf):
    """

    Args:
        thisdf: dataframe computed for the above TAS diagram 

    Returns:
        a figure containing a Harker diagram

    """

    thisfig = make_subplots(rows=4, cols=2)
    thisfig.update_layout(title='<b>Harker Diagrams from GEOROC</b> <br>', )

    harkerchems = ['TIO2(WT%)', 'AL2O3(WT%)', 'FEOT(WT%)', 'MGO(WT%)', 'CAO(WT%)', 'NA2O(WT%)', 'K2O(WT%)', 'P2O5(WT%)']
    harkerrows = [1, 1, 2, 2, 3, 3, 4, 4]
    harkercols = [1, 2, 1, 2, 1, 2, 1, 2]

    for chem, thisrow, thiscol in zip(harkerchems, harkerrows, harkercols):
        thisfig.add_traces(
            go.Scatter(
                x=thisdf['SIO2(WT%)'],
                y=thisdf[chem],
                mode='markers',
                marker=dict(symbol='circle'),
                name=chem,
                showlegend=False,
            ),
            rows=thisrow, cols=thiscol,
        )

    # Update x-axis properties
    thisfig.update_xaxes(title_text="SiO<sub>2</sub>(wt%)", row=4, col=1)
    thisfig.update_xaxes(title_text="SiO<sub>2</sub>(wt%)", row=4, col=2)
    for r in range(1, 5):
        for c in range(1, 3):
            thisfig.update_xaxes(range=[30, 80], row=r, col=c)

    # Update yaxis properties
    titles = ["TiO<sub>2</sub>(wt%)", "Al<sub>2</sub>O<sub>3</sub>(wt%)", "FeOT(wt%)", "MgO(wt%)",
              "CaO(wt%)", "Na<sub>2</sub>O(wt%)", "K<sub>2</sub>O(wt%)", "P<sub>2</sub>O<sub>5</sub>(wt%)"]
    maxy = [10, 25, 20, 15, 20, 10, 10, 5]

    for title, my, thisrow, thiscol in zip(titles, maxy, harkerrows, harkercols):
        thisfig.update_yaxes(title_text=title, row=thisrow, col=thiscol)
        thisfig.update_yaxes(range=[0, my], row=thisrow, col=thiscol)

    
    return thisfig
