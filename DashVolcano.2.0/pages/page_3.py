#***********************************************************#
# WARNING: this page is still under construction
# last update: July 26 2024
# Author: F. Oggier
#************************************************************#

import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pickle

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
            # *************************************************#
            # Row 1
            # **************************************************#
            dbc.Row([
                # title (h1) and subtitle (p)
                # main header h1
                html.H1(children="World Volcanoes", className="title", ),
                # paragraph
                html.P(
                    children="Displays the number of volcanoes around the world as a function of two parameters,"
                             "one on the x-axis (a rock or a morphology), the other on the y-axis (VEI or eruptive"
                             " material). Data can be filtered out by reliability (no of eruptions with VEI data vs"
                             " no of eruptions) or total no of eruptions. Corresponding chronograms are provided.",
                    className="description",
                ),
            ], align='center', className='intro'),
            html.Br(),

            # *************************************************#
            # Row 2 = Menus
            # **************************************************#
            dbc.Row([
                # first columns
                dbc.Col([
                    html.Div(className="card",
                             children=[html.Div(children="Features", className="menu-title"),
                                      dcc.Checklist(
                                             id='check-features',
                                             options=[
                                                      {'label': 'Rocks', 'value': 'Rocks'},
                                                      {'label': 'Eruption Frequency', 'value': 'Eruption Frequency'},
                                                      {'label': 'VEI', 'value': 'VEI'},
                                                     ],
                                             value=[None, None, None]
                                            ),
                                       dcc.Input(
                                           id='threshold',
                                           type='number',
                                           min=0,max=1,
                                           placeholder='key in a threshold'
                                       )
                                      ],
                             ),
                ], width=6),
                # second column
                dbc.Col([
                    html.Div(className="card",
                             children=[
                                 html.Div(children="Volcano Name", className="menu-title"),
                                 dcc.Dropdown(
                                     id="Gvp-names-dropdown",
                                     options=[
                                         {"label": vn, "value": vn} for vn in sorted(lst_names)],
                                     # default value
                                     value=None,
                                 ),
                                 dcc.RadioItems(id='period-button',
                                                options=[
                                                    {'label': 'BC', 'value': 'BC'},
                                                    {'label': 'before 1679', 'value': 'before 1679'},
                                                    {'label': '1679 and after', 'value': '1679 and after'}],
                                                value='1679 and after',
                                                )
                             ]
                             ),
                ], width=6),
            ], align='center'),
            html.Br(),

            # *************************************************#
            # Row 3 = Figures
            # **************************************************#
            dbc.Row([
                # column 1
                dbc.Col([
                    html.Div(dcc.Graph(
                        id="rock-vei-chart",
                        hoverData={'points': [{'customdata': 'names'}]},
                    ),
                        className="card", ),
                ],),
                
            ], align='center'),
            dbc.Row([
                # column 1
                dbc.Col([
                    html.Div(dcc.Graph(id="rock-vei-chart-thresh"), className="card", ),
                ], width=4),
                # column 2
                dbc.Col([
                    html.Div(dcc.Graph(id="rock-vei-chart-samples"), className="card", ),
                ], width=4),
                # column 3
                dbc.Col([
                    html.Div(dcc.Graph(id="chrono"), className="card", ),
                ], width=4),
            ], align='center'),
            html.Br(),

            # **************************************************#

        ]),
    ),
])


# **************************************************************#
# Call backs
# **************************************************************#
@app.callback(
    # cautious that using [] means a list, which causes error with a single argument
    [
        dash.dependencies.Output("rock-vei-chart", "figure"),
        dash.dependencies.Output("rock-vei-chart-thresh", "figure"),
        dash.dependencies.Output("rock-vei-chart-samples", "figure"),
    ],
    [
        # from checkbox features
        dash.dependencies.Input("check-features", "value"),
        # from input
        dash.dependencies.Input("threshold", "value"),
        # from Gvp name slider
        dash.dependencies.Input("Gvp-names-dropdown", "value"),
    ],
)
def update_charts(features, thresh, volcano_name):
    """
    """
    fig = go.Figure()
    fig1 = go.Figure()
    fig2 = go.Figure()
    
    # loads a dictionary containing the no of rocks for all volcanoes
    vperc = perc_rock()
    
    # index of chosen volcano
    if not(volcano_name is None):
        idx = list(vperc.keys()).index(volcano_name)  
       
    # total correlation matrix
    C = np.zeros((len(vperc.keys()), len(vperc.keys())))   
    
    # initialization
    dff = pd.DataFrame()
    
    if 'Rocks' in features:
        # computes percentage of rocks
        rckb = []
        nosmples = []
        for k in vperc.keys():
            rckb.append([x/sum(vperc[k]) for x in vperc[k]])
            nosmples.append(sum(vperc[k]))
        # updates dataframe
        dff = pd.DataFrame(rckb, columns=GEOROC_rocks)    
    
        # correlation matrix
        if not("cr" in os.listdir('.')):
            rows = []

            for r1 in rckb:
                row = []
                for r2 in rckb:
                    mse = np.square(np.subtract(np.array(r1), np.array(r2))).sum()/2
                    row.append(mse)
                rows.append(row)
            Cr = np.matrix(rows)
            with open("Cr", "wb") as cr:   
                pickle.dump(Cr, cr)  
        else:
           with open("cr", "rb") as cr:   
               Cr = pickle.load(cr)   
        
        # max Cr = 1       
        C = C + Cr
        
    if 'Eruption Frequency' in features:
        # short repose = < 1 year
        # medium repose = 1 < 50
        # long repose = above 50
        # computes eruptive frequency
        dfd, dfr = compute_eruptionperiods(vperc.keys())
        
        # computes the no of short, long and medium eruptions
        dfgrp = dfd[['Volcano Name', 'Eruption Number']].groupby('Volcano Name').count().reset_index()
        dfgrptmp = dfd[['Volcano Name', 'long eruption']].groupby('Volcano Name').sum().reset_index()
        dfgrp = dfgrp.merge(dfgrptmp, on='Volcano Name', how='left')
        dfgrptmp = dfd[['Volcano Name', 'medium eruption']].groupby('Volcano Name').sum().reset_index()
        dfgrp = dfgrp.merge(dfgrptmp, on='Volcano Name', how='left')
        dfgrptmp = dfd[['Volcano Name', 'short eruption']].groupby('Volcano Name').sum().reset_index()
        dfgrp = dfgrp.merge(dfgrptmp, on='Volcano Name', how='left')
       
        # gathers frequency data
        freq = []
        for k1 in vperc.keys():
            n1 = dfgrp[dfgrp['Volcano Name'] == k1]['Eruption Number']
            if len(n1.index) > 0:
                n1 = float(n1)
                # eruptions
                d1 = dfgrp[dfgrp['Volcano Name'] == k1].values[0]
                # repose
                dr = dfr[dfr['Volcano Name'] == k1][['repose_x','repose_y']]
                drl = list(dr['repose_x']+dr['repose_y'])[0]
                # half weight repose half weight eruption
                drll = len([x for x in drl if x > 50])/(2*len(drl))
                drlm = len([x for x in drl if (x>=1)&(x<=50)])/(2*len(drl))
                drls = len([x for x in drl if x <1])/(2*len(drl))
                freq.append([x/(2*d1[1]) for x in d1[2:]]+[drll, drlm, drls])    
            else:
                freq.append([0,0,0,0,0,0])
        dffreq = pd.DataFrame(freq, columns = ['long eruption', 'medium eruption', 'short eruption', 'long repose', 'medium repose', 'short repose']).round(3)
        dictfreq = dffreq.T.to_dict('list')
    
        # update dataframe
        for i in ['long eruption', 'medium eruption', 'short eruption', 'long repose', 'medium repose', 'short repose']:
            dff[i] = dffreq[i]
        
        # correlation matrix
        if not("cf" in os.listdir('.')):
            rows = []

            for r1 in freq:
                row = []
                for r2 in freq:
                    mse = np.square(np.subtract(np.array(r1), np.array(r2))).sum()/2
                    row.append(mse)
                rows.append(row)
            Cf = np.matrix(rows)
            with open("Cf", "wb") as cf:   
                pickle.dump(Cf, cf)  
        else:
           with open("cf", "rb") as cf:   
               Cf = pickle.load(cf)   
        
        # max 0.46       
        C = C + Cf
        
        
    if 'VEI' in features:
        # computes VEI frequency
        dftmp = df[['Volcano Name', 'VEI']]
        dftmp = dftmp.groupby('Volcano Name')['VEI'].apply(list).reset_index(name='VEI')
        dictVEI = dftmp.set_index('Volcano Name').T.to_dict('list')
        
        # gather vei data
        veis = []
       
        for k1 in vperc.keys():
            row = []
            r1 = dictVEI[k1][0]
            r1 = [int(i) for i in r1 if type(i)==str]
            r1c = []
            if len(r1) == 0:
                for i in range(8):
                    r1c.append(0) 
            else: 
                for i in range(8):
                    r1c.append(len([r for r in r1 if r==i])/len(r1))
            veis.append(r1c)           
        
        # updates dataframe
        dfvei = pd.DataFrame(veis, columns = [str(i) for i in range(8)]) 
    
        # update dataframe
        for i in [str(i) for i in range(8)]:
            dff[i] = dfvei[i]
                    
        # correlation matrix
        if not("cv" in os.listdir('.')):
            rows = []

            for r1 in veis:
                row = []
                for r2 in veis:
                    mse = np.square(np.subtract(np.array(r1), np.array(r2))).sum()/2
                    row.append(mse)
                rows.append(row)
            Cv = np.matrix(rows)
            with open("Cv", "wb") as cv:   
                pickle.dump(Cv, cv)  
        else:
           with open("cv", "rb") as cv:   
               Cv = pickle.load(cv)   
        
        # max Cv = 1 
        C = C + Cv/2
        
    # normalize C
    nofeat = len([x for x in features if not(x is None)] )
    if nofeat > 0:
        C = C/nofeat
        
    if not(volcano_name is None) and np.any(C):
        # find similar volcanoes
        lv = C[idx].tolist()[0]
        clse = []
        if thresh is None:
            thresh = 2
        for i in range(len(lv)):
            # filter out negative
            if lv[i] <= thresh and lv[i]>=0:
                clse.append(i)

        clsecol = [0 if not(x in clse) else 1 for x in range(len(vperc.keys()))]  
        dff['Close'] = clsecol
             
        if len(dff.index) > 0:
            customlabels = {}
            for c in list(dff):
                customlabels[c] = c.lower()[0:8] +'<br>'+ c.lower()[8:]
            fig = px.parallel_coordinates(dff, color='Close', 
                              color_continuous_scale=px.colors.sequential.Bluered,
                              labels = customlabels
                                          )
            
            if 'Rocks' in features:
                hoverdata = {'no': False, 'dist': True, 'name': True, 'samples': True, 'shape': False}
                if 'VEI' in features:
                    if 'Eruption Frequency' in features:
                        dfc = pd.DataFrame( {'samples': [nosmples[i] for i in clse],
                                 'dist': [lv[i] for i in clse], 
                                 'name': [list(vperc.keys())[i] for i in clse],
                                 'erup': [dictfreq[i] for i in clse], 
                                 'VEI': [dictVEI[list(vperc.keys())[i]] for i in clse],})
                        hoverdata['erup'] = True
                    else:
                        dfc = pd.DataFrame( {'samples': [nosmples[i] for i in clse],
                                 'dist': [lv[i] for i in clse], 
                                 'name': [list(vperc.keys())[i] for i in clse],
                                 'VEI': [dictVEI[list(vperc.keys())[i]] for i in clse],})
                    hoverdata['VEI'] = True
                else:
                    if 'Eruption Frequency' in features:
                        dfc = pd.DataFrame( {'samples': [nosmples[i] for i in clse],
                                 'dist': [lv[i] for i in clse], 
                                 'erup': [dictfreq[i] for i in clse], 
                                 'name': [list(vperc.keys())[i] for i in clse]})
                        hoverdata['erup'] = True
                    else:
                        dfc = pd.DataFrame( {'samples': [nosmples[i] for i in clse],
                                 'dist': [lv[i] for i in clse], 
                                 'name': [list(vperc.keys())[i] for i in clse]})                 
                                 
                dfc = dfc.sort_values(by=['dist'], ascending=True)
                dfc['no'] = [i for i in range(len(clse))]                  
                # samples
                conditions = [(dfc['samples'] < 10), (dfc['samples'] >= 10) & (dfc['samples'] <= 30), (dfc['samples'] > 30)]
                choices = ['circle', 'square', 'diamond']
                dfc['shape'] = np.select(conditions, choices)                 
                                                                     
                fig1 = px.scatter(dfc, x= 'no',
                                   y= 'dist', 
                                   symbol='shape',
                                   hover_data=hoverdata)
                                   
                newnames = {'circle':'less than 10', 'square': 'less than 30', 'diamond':'more than 30'}
                fig1.for_each_trace(lambda t: t.update(name = newnames[t.name],
                                      legendgroup = newnames[t.name],))
                fig1.update_layout(legend_title="", xaxis_title="", yaxis_title="distance",)                 
                          
            else:
                if 'VEI' in features:
                    if 'Eruption Frequency' in features:
                        dfc = pd.DataFrame( { 'VEI': [dictVEI[list(vperc.keys())[i]] for i in clse],
                                 'dist': [lv[i] for i in clse], 
                                 'erup': [dictfreq[i] for i in clse], 
                                 'name': [list(vperc.keys())[i] for i in clse]})
                        hoverdata = ['dist', 'name', 'VEI', 'erup']    
                    else: 
                        dfc = pd.DataFrame( { 'VEI': [dictVEI[list(vperc.keys())[i]] for i in clse],
                                 'dist': [lv[i] for i in clse], 
                                 'name': [list(vperc.keys())[i] for i in clse]})
                        hoverdata = ['dist', 'name', 'VEI']             
                else:
                    if 'Eruption Frequency' in features:
                        dfc = pd.DataFrame( {
                                 'dist': [lv[i] for i in clse], 
                                 'erup': [dictfreq[i] for i in clse], 
                                 'name': [list(vperc.keys())[i] for i in clse]})
                        hoverdata = ['dist', 'name', 'erup']            
                    else:             
                        dfc = pd.DataFrame( {
                                 'dist': [lv[i] for i in clse], 
                                 'name': [list(vperc.keys())[i] for i in clse]})
                        hoverdata = ['dist', 'name']             
                                 
                dfc = dfc.sort_values(by=['dist'], ascending=True)
                dfc['no'] = [i for i in range(len(clse))] 
                fig1 = px.scatter(dfc, x= 'no',
                                   y= 'dist', 
                                   hover_data=hoverdata)
                                   
            dfs = dff[dff['Close']==1]
            dfs = dfs.drop('Close', axis=1)
            dfs = dfs.T
            # add volcano names
            dfs.columns = [list(vperc.keys())[i] for i in clse]
            dfs['no'] = [list(dff)[i].lower() for i in range(len(dfs.index))]
                
            fig2 = px.line(dfs, x='no', y = dfs.columns[0:-1], markers=True)   
            fig2.update_layout(legend_title="Volcano", xaxis_title="", yaxis_title="",)  
            fig2.update_xaxes(tickangle=45)                       
       
    # fig.update_layout(title='<b>Similarities</b> <br>', )
    fig1.update_layout(title='<b>Threshold</b> <br>', )
    fig1.update_xaxes(tickangle=45) 
    # fig2.update_layout(title='<b>Samples</b> <br>', )
    

    return fig, fig1, fig2


@app.callback(
    # cautious that using [] means a list, which causes error with a single argument
    dash.dependencies.Output("chrono", "figure"),
    [
        # from Gvp name slider
        dash.dependencies.Input("Gvp-names-dropdown", "value"),
        # from rock-vei-chart
        dash.dependencies.Input("rock-vei-chart-thresh", "hoverData"),
        # from radio button periods
        dash.dependencies.Input("period-button", 'value')
    ],
)
def update_chronogram_chart(volcano_name, hoverdata, period_choice):
    """
    """
    
    lstv = []
    
    # custom data is stored last, names are in the second item
    # if hover on the trendline, no customdata
    if not(hoverdata is None): 
        if 'customdata' in hoverdata['points'][-1].keys():
            lstv = [hoverdata['points'][-1]['customdata'][0]]

    fig = go.Figure()
    if not(volcano_name is None):
        fig = update_chronogram(lstv + [volcano_name], period_choice)
    else:
        if len(lstv) > 0:
            fig = update_chronogram(lstv, period_choice)
    return fig



