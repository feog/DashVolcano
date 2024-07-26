# ************************************************************************************* #
#
# This creates a one-page layout, that hosts side-by-side two TAS diagrams for the same
# volcano, with below its chronogram.
# Contains two functions:
# 1) update_joint_chemchart: jointly updates both TAS diagrams
# 2) add_chems: superimpose chemicals on chronogram
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

import pandas as pd
import numpy as np
from datetime import datetime

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
                html.H1(children="TAS Diagrams and Chronogram", className="title", ),
                # paragraph
                html.P(
                    children="On the left, a TAS diagram using Georoc data. On the right, the same samples are filtered out,"  
                    " so only samples matching GVP eruptions are shown, so their VEI is given, if known. "
                    "On the right, a round symbol means either no VEI or a VEI at most 2, while a triangle means a VEI at least 3."
                    "Below, a chronogram shows the eruption history, during three periods: before BC, after BC until 1679, after 1679. "
                    "VEI data is superimposed, the line connecting the VEI points shows the fluctuations of VEI over time." 
                    "Samples from Georoc are further superimposed, to see the evolution of SIO2 and K2O over time.",
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
                        id="erup-filter3",
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
                    # second drop down
                    #html.Div(children="Eruption date(s)", className="menu-title"),
                    #dcc.Dropdown(
                    #    id="erup-filter4",
                    #    options=[{"label": region, "value": region} for region in []],
                        # default value
                    #    value="all",
                    #    clearable=False,
                    #),
                ], width=3),
                # empty column to create alignment
                dbc.Col([
                ], width=3),
            ], align='center', ),
            html.Br(),

            # *************************************************#
            # chemical plots 
            # **************************************************#
            dbc.Row([
                # inserts a graph
                # a dcc.Graph components expect a figure object
                # or a Python dictionary containing the plot’s data and layout.
                dbc.Col([
                    # first plot
                    html.Div(
                        dcc.Graph(id="chem-chart-georoc3"),
                    ),
                ], className="card"),
                dbc.Col([
                    # first plot
                    html.Div(
                        dcc.Graph(id="chem-chart-georoc4"),
                    ),
                ], className="card"),
            ], align='center'),
            
            # *************************************************#
            # chronogram
            # **************************************************#
            dbc.Row([
                # inserts a graph
                # a dcc.Graph components expect a figure object
                # or a Python dictionary containing the plot’s data and layout.
                dbc.Col([
                    # second plot
                    html.Div(
                        dcc.Graph(id="vei-chart3"),
                    ),
                    # third plot
                    # html.Div(
                    #    dcc.Graph(id="gvpevent-chart3"),
                    #),
                ], className="card"),
                dbc.Col([
                    # checklist
                    html.Div(
                        dcc.Checklist(
                            id="GEOROCsample-filter",
                            options=[
                                 {'label': 'GEOROC', 'value': 'GEOROC'}],
                            labelStyle={'margin-right': '5px'},
                            value=['GEOROC'],
                            className='check',
                        ),
                    ),
                    html.Br(),
                
                    # second plot
                    html.Div(
                        dcc.RadioItems(id='period-button',
                                        options=[
                                            {'label': 'BC', 'value': 'BC'},
                                            {'label': 'before 1679', 'value': 'before 1679'},
                                            {'label': '1679 and after', 'value': '1679 and after'}
                                            ],
                                        value='1679 and after',
                                        ),
                    ),
                    ], width=1),
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
    dash.dependencies.Output("erup-filter3", "options"),
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

    return opts

# part 2
@app.callback(
    dash.dependencies.Output("erup-filter4", "options"),
    # from drop down
    dash.dependencies.Input("region-filter", "value"),
)
def set_date_options2(volcano_name2):
    """

    Args:
        volcano_name2: name of a chosen volcano

    Returns:  Updates eruption dates choice based on volcano name

    """
    # loads Georoc data based on volcano_name
    if not (volcano_name2 == "start"):
        dfgeoroc = load_georoc(volcano_name2)

    opts2 = update_onedropdown(volcano_name2)

    return opts2


# ************************************#
#
# callbacks for figure updates
#
# ************************************#

@app.callback(
    # to the dcc.Graph with id='chem-chart-georoc3'
    # cautious that using [] means a list, which causes error with a single argument
    [
        dash.dependencies.Output("chem-chart-georoc3", "figure"),
        dash.dependencies.Output("vei-chart3", "figure"),
        dash.dependencies.Output("chem-chart-georoc4", "figure"),
    ],
    [
        # from drop down
        dash.dependencies.Input("region-filter", "value"),
        # from date drop down
        dash.dependencies.Input("erup-filter3", "value"),
        # from radio button periods
        dash.dependencies.Input("period-button", 'value'),
         #
        dash.dependencies.Input("GEOROCsample-filter", 'value'),
        
    ],
)
def update_charts_rock_vei(volcano_name, date, period_choice, addGEOROC):
    """

    Args:
        volcano_name: GEOROC name of volcano
        date: eruptions dates, possibly all

    Returns: Updates plots based on user's inputs, for first volcano

    """

    # first TAS diagram 
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.85, 0.2], vertical_spacing=0.05,)
    fig, dfchem = update_chemchart(volcano_name, fig, date)
    
    # second figure
    # checks if data is present
    if not (volcano_name is None) and not (volcano_name == "start"):
        n = volcano_name
        # handles long names
        if n in dict_Georoc_sl.keys():
            n = dict_Georoc_sl[n]
        # automatic matching
        if n in dict_Georoc_GVP.keys():
            n = dict_Georoc_GVP[n]
        else:
            n = volcano_name.title()
        
        fig2 = update_chronogram([n], period_choice)
         # addGEOROC: to decide whether to superimpose GEOROC samples
        if len(addGEOROC) > 0:
            fig2 = add_chems(dfchem, fig2, period_choice)
            
        figgvp = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.85, 0.2], vertical_spacing=0.05,)
        figgvp, tmp = update_joint_chemchart(volcano_name, dfchem, figgvp, date)
        
    else:
        fig2 = go.Figure()
        figgvp = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.85, 0.2], vertical_spacing=0.05,)
        figgvp = plot_TAS(figgvp)

    return fig, fig2, figgvp

def update_joint_chemchart(thisvolcano_name, thisdf, thisfig, thisdate):
    """

    Args:
        thisvolcano_name: name of a volcano
        thisfig: the figure being updated
        thisdate: the eruption dates, possibly all
        db: use "georoc" or "combined" for the combined GVP-GEOROC dataset

    Returns: Updates both the chemical plot based on user's inputs, 
             Also the dataframe used to draw the plot

    """
    colsGvp = ['Volcano Name','Start Year','End Year','VEI'] 
    
    # not sure why I need to load again but anyway
    if not (thisvolcano_name == "start") and not(thisvolcano_name is None):
        # laods a combined GVP GEOROC dataframe
        dfGvpGeo = pd.DataFrame([],columns = colsGvp + list(thisdf))
        # we need a GVP match
        if (thisvolcano_name in dict_Georoc_GVP.keys()) or (thisvolcano_name in dict_Georoc_sl.keys()):
            n = thisvolcano_name
            # handles long names
            if n in dict_Georoc_sl.keys():
            	 n = dict_Georoc_sl[n]
            # automatic matching
            if n in dict_Georoc_GVP.keys():
                n = dict_Georoc_GVP[n]
            else:
                n = thisvolcano_name.title()
                
            # loads volcano data    
            dfmatchv = df[df['Volcano Name'] == n]
            
            # makes sure there is data
            if len(dfmatchv.index) > 0:
                # if NaN for 'End Year', uses 'Start Year'
                dfmatchv['End Year'] = dfmatchv.apply(
                    lambda row: row['Start Year'] if pd.isnull(row['End Year']) else row['End Year'], axis=1)    
                    
            # matches dates    
            if thisdate == 'all':
                all_dates_gvp = match_GVPdates(thisvolcano_name, 'forall', n)
            else:
                this_date_gvp = match_GVPdates(thisvolcano_name, thisdate, n)
                # check if matches for this date
                if not(this_date_gvp[0]) == 'not found':
                    all_dates_gvp = [[int(thisdate.split('-')[0]), this_date_gvp]]
                else:
                    all_dates_gvp = []
            
        else:
            all_dates_gvp = []
             
        # if match found
        # thisdf already contains the right data, issue is to match with GVP to get VEI data
        if len(all_dates_gvp)>0:
            for dse in all_dates_gvp:
                gy = dse[0]
                se = dse[1]
                # there could be several rows in dfmatch, if several eruptions in one year
                dfmatch = dfmatchv[(dfmatchv['Start Year'].astype(str) == se[0]) & (dfmatchv['End Year'].astype(str) == se[1])]    
                # georoc month
                gm = [x for x in thisdf[thisdf['ERUPTION YEAR']==gy]['ERUPTION MONTH'].unique()]
                gm_clean = [x for x in gm if not(np.isnan(x)) and (x>0)]
                # in the same year, looks for month match
                if (se[0] == se[1]) and len(gm_clean)>0:
                    # extract month
                    gvpm = [list(x) for x in dfmatch[['Start Month', 'End Month']].astype(float).values] 
                    # removes 0 and nan
                    gvpm = [x for x in gvpm if (not(np.isnan(x[0])) and (x[0]>0) and not(np.isnan(x[1])) and (x[1]>0))]
                    # matches month
                    fnd_months = [[y,x] for x in gvpm for y in gm if  x[0] <= y <= x[1]]
                    if len(fnd_months) > 0 :
                        # GEOROC month
                        gm = [x[0] for x in fnd_months]
                        # gvp start and end months
                        sm = [x[1][0] for x in fnd_months]
                        em = [x[1][1] for x in fnd_months]
                        dfmatch = dfmatch[(dfmatch['Start Month'].astype(float).isin(sm))&(dfmatch['End Month'].astype(float).isin(em))]   
                 
                # if months are matching, unlikely to have several rows left
                # if several rows, takes the first 
                rowgvp = dfmatch[colsGvp].values[0]
                #there could be several GEOROC rows for one GVP row
                rowsgeoroc = thisdf[(thisdf['ERUPTION YEAR']==gy)&(thisdf['ERUPTION MONTH'].isin(gm))][list(thisdf)].values
                rowdf = []
                for rw in rowsgeoroc:
                    rowdf.append(list(rowgvp)+list(rw))
                dfGvpGeo = dfGvpGeo.append(pd.DataFrame(rowdf,columns = colsGvp +  list(thisdf)))
                        
        dff = dfGvpGeo   
                  
    else:
        # empty dataframe with right columns
        d = {'SIO2(WT%)': [], 'NA2O(WT%)': [],
             'K2O(WT%)': [], 'NA2O(WT%)+K2O(WT%)': [], 'color': [],
             'FEO(WT%)': [], 'CAO(WT%)': [], 'MGO(WT%)': [], 'ERUPTION YEAR': [], 'color': [], 'MATERIAL':[]}
        dff = pd.DataFrame(data=d)

    # adds the TAS layout
    thisfig = plot_TAS(thisfig)
    # draws the scatter plot
    thisfig = plot_chem(thisfig, dff, ['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], lbls)
    # change title
    thisfig.update_layout(title='<b>Chemical Rock Composition from Georoc (with known eruptions)</b> <br>', )

    return thisfig, dff    
    


def add_chems(thisdf,thisfig,thisperiod):
    """

    Args:
        thisdf: GEOROC data
        thisfig: chronogram figure to be updated
        thisperiod: 3 periods of eruptions

    Returns: add GEOROC chemical to GVP chronogram

    """
    if thisperiod == '1679 and after':
        thisdf = thisdf[thisdf['ERUPTION YEAR'] >= 1679].rename(columns={'ERUPTION YEAR': 'year', 'ERUPTION MONTH': 'month', 'ERUPTION DAY': 'day'})
        # removes some bad inputs
        thisdf['month'] = np.where((thisdf['month'] > 12), 1, thisdf['month'])  
        thisdf['month'] = np.where((thisdf['month'] < 1), 1, thisdf['month'])    
        # in case the day is more than 31   
        thisdf['day'] = np.where((thisdf['day'] > 31), 1, thisdf['day'])      
        thisdf['day'] =  thisdf['day'].replace(0, 1) 
        
    elif thisperiod == 'before 1679':
        thisdf = thisdf[(thisdf['ERUPTION YEAR'] < 1679) & (thisdf['ERUPTION YEAR'] > 0)]
    else:
        thisdf = thisdf[thisdf['ERUPTION YEAR'] <0]
    
    # just makes sure we got float and not string    
    thisdf['K2O(WT%)'] = thisdf['K2O(WT%)'].astype(float).apply(lambda x: round(x, 2))    
    thisdf['NA2O(WT%)'] = thisdf['NA2O(WT%)'].astype(float).apply(lambda x: round(x, 2)) 
    thisdf['SIO2(WT%)'] = thisdf['SIO2(WT%)'].astype(float).apply(lambda x: round(x, 2))   
              
    for lbl in lbls:
       
        # selects rows based on rocks of interest
        dffc = thisdf[thisdf['color'] == lbl]
        
        if thisperiod == '1679 and after':
            xdate = pd.to_datetime(dffc[['year', 'month', 'day']])
        else:
            xdate = dffc['ERUPTION YEAR']
        
        # add K2O
        thisfig.add_trace(
            go.Scatter(
                x=xdate,
                mode='markers',
                marker_color='cornflowerblue',
                customdata=dffc[['NA2O(WT%)','K2O(WT%)']],
                hovertemplate='x=%{x}<br>%{customdata}',
                y= (0 - .4)  + (dffc['K2O(WT%)']+dffc['NA2O(WT%)'])/100,
                name = 'NA2O+K2O',
                showlegend=False
                )
        )
          
        # add SIO2
        thisfig.add_trace(
            go.Scatter(
                x=xdate,
                mode='markers',
                marker_color='cornflowerblue',
                customdata=dffc['SIO2(WT%)'],
                hovertemplate='x=%{x}<br>%{customdata}',
                y= (0 - .4)  + dffc['SIO2(WT%)'].astype(float)/100,
                name = 'SIO2',
                showlegend=False
                )
        )   
    return thisfig       

