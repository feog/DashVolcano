# ************************************************************************************* #
#
# This file creates a class instance of the app DashVolcano.
#
# Author: F. Oggier
# Last update: 23 Sep 2023
# ************************************************************************************* #



import dash
import dash_bootstrap_components as dbc        
        
# ****************************#
#
# create a class instance
#
# ***************************#

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.title = "Volcano Analytics"
