from config_variables import *
import plotly.graph_objs as go
from numpy.linalg import inv
from GVP_functions import rocks_to_color, find_new_tect_setting
from plotly.subplots import make_subplots
import re
from collections import Counter
import statistics
import pickle


# **********************************************************************************#
#
# This contains functions to manipulate Georoc data.
# --------------------------------------------------
# * load_georoc: loads data for a given volcano
# * fix_pathname
# * fix_inclusion
# * with_FEOnorm: handles FEOT and normalizes oxides 
# * guess_rock: associates a rock name based on chemicals and TAS diagram
# * extract_date: extract date information from comments
# * plot_TAS: draws the TAS background
# * add_alkaline_series
# * add_alkaline_line
# * detects_chems
# * plot_chem
# * match_GVPdates: given a Georoc date, matches GVP date 
# * update_chemchart
# * update_onedropdown
# * filter_date: filters a dataframe by date
# * update_onedropdown: creates menus for filtering per date
# * GEOROC_majorrock: computes major rocks for GEOROC data
# * update_GEOrockchart
# * createGEOROCaroundGVP: creates a df of GEOROC samples around GVP volcanoes
# * createPetDBaroundGVP: creates a df of PetDB samples around GVP volcanoes
# * retrieved_fromfigure
# * update_subtitle: updates subtitles based on user clicks on legends
# * GEOROC_sunburst
# * perc_rock: computes the percentage of rocks for all volcanoes
#
#
# Author: F. Oggier
# Last update: 25 April 2024
# **********************************************************************************#

def load_georoc(thisvolcano):
    """

    Args:
        thisvolcano: name of a volcano

    Returns: a data frame with the georoc data corresponding to the volcano given as input
             manual samples can be added at the end of the code

    """
    colsloc = ['LOCATION-1', 'LOCATION-2', 'LOCATION-3', 'LOCATION-4', 'LOCATION-5',
               'LOCATION-6', 'LOCATION-7', 'LOCATION-8', 'LOCATION-9']           
    
    # handles long names
    if thisvolcano in dict_Georoc_sl.keys():
        thisvolcano = dict_Georoc_sl[thisvolcano]

    # files containing this volcano
    all_pathcsv = dict_volcano_file[thisvolcano]

    dfloaded = pd.DataFrame()
    for pathcsv in all_pathcsv:
        # find the latest version of the file to use
        pathcsv = fix_pathname(pathcsv)
        # print('GEOROC file used:', pathcsv)
        
        dftmp = pd.read_csv("../GeorocDataset/%s" % pathcsv, low_memory=False, encoding='latin1')
        
        if 'Inclusions_comp' in pathcsv:
            # updates columns to have the same format as dataframes from other files
            dftmp = fix_inclusion(dftmp)
            
        # add manual samples
        elif 'ManualDataset' in pathcsv:
            # in case some columns are missing
            for cl in ['LATITUDE MIN', 'LATITUDE MAX', 'LONGITUDE MIN', 'LONGITUDE MAX', 'SAMPLE NAME']+chemcols + colsrock + ['LOI(WT%)']:
                if not(cl in list(dftmp)):
                    dftmp[cl] = np.nan
            # makes sure captial letters are used
            dftmp['TECTONIC SETTING'] = dftmp['TECTONIC SETTING'].str.upper()
            dftmp['LOCATION'] = dftmp['LOCATION'].str.upper()

        else:
            
            # keep only volcanic rocks
            dftmp = dftmp[dftmp['ROCK TYPE'] == 'VOL']
            dftmp = dftmp[['LOCATION']+['LATITUDE MIN', 'LATITUDE MAX', 'LONGITUDE MIN', 'LONGITUDE MAX', 'SAMPLE NAME'] + chemcols + colsrock + ['LOI(WT%)']]
          
        # deprecated: dfloaded = dfloaded.append(dftmp)
        dfloaded = pd.concat([dfloaded, dftmp])
    
    # most volcanoes are located after the the 3rd backslash,
    # but sometimes we need the location after the 2nd
    # in fact, in inclusion, they can be anywhere
    splt = dfloaded['LOCATION'].str.split('/', expand=True)
    dfloaded[colsloc[0:len(splt.columns)]] = splt

    # keeps only data for this volcano
    if ',' in thisvolcano:
        # issues with , as a delimiter
        if thisvolcano == 'SANTIAGO (JAMES, SAN SALVADOR)':
            all_names = [' SANTIAGO (JAMES, SAN SALVADOR)', ' SANTIAGO (JAMES, SAN SALVADOR) ']
        else:
            # the data is dirty, sometimes there are spaces, sometimes not
            all_names = [ns.strip().upper() for ns in thisvolcano.split(',')]
            all_names += [' ' + nm for nm in all_names]
            all_names += [nm + ' ' for nm in all_names]
            all_names += [' ' + nm + ' ' for nm in all_names]
    else:
        # the data is dirty, sometimes there are spaces, sometimes not
        all_names = [' ' + thisvolcano.upper(), thisvolcano.upper(),
                     thisvolcano.upper() + ' ', ' ' + thisvolcano.upper() + ' ']

    # special clause for volcanoes which need a second column for disambiguation
    if thisvolcano in ['SUMBING - SUMATRA', 'SUMBING - JAVA']:
        region = thisvolcano.split('-')[1] + ' '
        dfloaded = dfloaded[(dfloaded['LOCATION-4'] == ' SUMBING') & (dfloaded['LOCATION-3'] == region)]
    else:
        # looks for matches in all columns
        dftmp = pd.DataFrame()
        # sometimes, it is needed to look at LOCATION COLUMNS
        dfloaded['LOCATION COMMENT'].fillna('', inplace=True)
        dfloaded['LOCATION FROM COMMENT'] = dfloaded['LOCATION COMMENT'].str.split(',').str[0]
        allcolsloc = colsloc[0:len(splt.columns)] + ['LOCATION FROM COMMENT']
        
        for cls in allcolsloc:
            # deprecated: dftmp = dftmp.append(dfloaded[dfloaded[cls].isin(all_names)])
            dftmp = pd.concat([dftmp, dfloaded[dfloaded[cls].isin(all_names)]])
            
        # in case same match is found through several columns
        dfloaded = dftmp.drop_duplicates()

    # no matter in which column the match was found, the correct name is always put in LOCATION-4
    if thisvolcano in dict_Georoc_sl.values():
        dfloaded.loc[:, 'LOCATION-4'] = ' ' + dict_Georoc_ls[thisvolcano]
    else:
        dfloaded.loc[:, 'LOCATION-4'] = ' ' + thisvolcano

    # adds dates from LOCATION COMMENT
    # finds the dates
    dfloaded['GUESSED DATE'] = dfloaded['LOCATION COMMENT'].astype(str).fillna('').apply(extract_date)
    # replace NaN in ERUPTION YEAR 
    dfloaded['ERUPTION YEAR'].fillna(dfloaded['GUESSED DATE'], inplace=True)
    
    # add normalization 
    dfloaded = with_FEOnorm(dfloaded)
    
    # adds names to rocks using TAS 
    dfloaded = guess_rock(dfloaded)

    return dfloaded


def fix_pathname(thisarc):
    """

    Args:
        thisarc: file name without any suffix

    Returns: file name with the right suffix (which contains the date of the latest download)

    """    
    if not('ManualDataset' in thisarc):
        
        folder, filename = thisarc.split('/')
        # lists files in the folder
        tmp = os.listdir('../GeorocDataset/%s' % folder)
        # now because of the new name, needs to find the file with the right suffix
        # in fact it is worse, since they changed the concatenation of words
        # so first replace hyphen and underscores with spaces, then split with respect to spaces
        words = filename.replace('-', ' ').replace('_', ' ').split(' ')
        # next find filenames that contain all the words
        # there could be several, it is assumed that the year comes first then the month
        # this should put the most recent file first
        newname = sorted([x for x in tmp if all(y in x for y in words)])[::-1]
        # if there is no year, it will come first and it shouldn't
        if len(newname) > 1 and not(newname[0][0].isdigit()):
            # put the file name with no date at the end
            newname.insert(len(newname), newname.pop(0))
       
        thisarc = folder+'/'+newname[0]

    return thisarc
    

def fix_inclusion(thisdf):
    """

    Args:
        thisdf: GEOROC dataframe loaded from the Inclusion file

    Returns: the same dataframe with updated columns to match the format of dataframes from other files

    """    
    # missing columns for inclusions
    thisdf['ERUPTION YEAR'] = np.nan
    thisdf['ERUPTION MONTH'] = np.nan
    thisdf['ERUPTION DAY'] = np.nan
    thisdf['UNIQUE_ID'] = np.nan
    thisdf['MATERIAL'] = ['INC']*len(thisdf.index)
    thisdf['TECTONIC SETTING'] = np.nan
    
    # different names
    thisdf = thisdf.rename({'LATITUDE (MIN.)': 'LATITUDE MIN'}, axis='columns')
    thisdf = thisdf.rename({'LATITUDE (MAX.)': 'LATITUDE MAX'}, axis='columns')
    thisdf = thisdf.rename({'LONGITUDE (MIN.)': 'LONGITUDE MIN'}, axis='columns')
    thisdf = thisdf.rename({'LONGITUDE (MAX.)': 'LONGITUDE MAX'}, axis='columns')
            
    # missing chemical columns
    for cl in ['H2OT(WT%)', 'CL2(WT%)', 'CO1(WT%)', 'CH4(WT%)', 'SO4(WT%)', 'P2O5(WT%)']:
        thisdf[cl] = np.nan
        
    # missing isotopes
    for cl in isotopes:
        thisdf[cl] = np.nan    

    # choice of columns
    thisdf = thisdf[['LOCATION']+['LATITUDE MIN', 'LATITUDE MAX', 'LONGITUDE MIN', 'LONGITUDE MAX', 'SAMPLE NAME'] + chemcols + colsrock + ['LOI(WT%)']+isotopes]
            
    # some chemicals have two numbers instead of one, keeping the first one of the pair
    for ch in chemcols:
        nofloat = [x for x in list(thisdf[ch].unique()) if (type(x) == str and '\\' in x)]
        newvalues = {}
        for x in nofloat:
            # choose the first value of the pair
            newvalues[x] = x.split('\\')[0].strip() 
    
        # replaces the pairs by their first value
        thisdf[ch].replace(to_replace=newvalues, inplace=True)
    
    return thisdf
    

def with_FEOnorm(thisdf):
    """

    Args:
        thisdf: GEOROC dataframe for one volcano
        
    Returns: Among oxydes, we have 'FE2O3(WT%)', 'FEO(WT%)', 'FEOT(WT%)'.
             If FEOT is here, discard the other two, otherwise computes FEOT based on the other two.
             The dataframe with normalized oxides is returned. 

    """    
    # cleans up, oxides include LOI
    for col in oxides:
        # in case two measurements
        nofloat = [x for x in list(thisdf[col].unique()) if (type(x) == str and '\\' in x)]
        newvalues = {}
        for x in nofloat:
            # choose the first value of the pair
            newvalues[x] = x.split('\\')[0].strip() 
        
        # replaces the pairs by their first value
        thisdf[col].replace(to_replace=newvalues, inplace=True)
    
    #  replaces missing oxides and LOI data with 0
    thisdf[oxides] = thisdf[oxides].fillna(0).astype(float)
    # when FEOT(WT%) is available, disregard FE2O3(WT%) and FEO(WT%)
    oxides_nofe = ['SIO2(WT%)', 'TIO2(WT%)', 'AL2O3(WT%)', 'FE2O3(WT%)', 'FEO(WT%)', 'FEOT(WT%)', 'CAO(WT%)', 'MGO(WT%)', 'MNO(WT%)', 'K2O(WT%)', 'NA2O(WT%)', 'P2O5(WT%)']
    # When FEOT(WT%) is not available or empty, then FEOT(WT%) = FE2O3(WT%)/1.111 + FEO(WT%)    
    thisdf.loc[:, 'FEOT(WT%)'] = np.where(thisdf['FEOT(WT%)'] == 0, (thisdf['FE2O3(WT%)']/1.111) + thisdf['FEO(WT%)'], thisdf['FEOT(WT%)'])
    
    # the numerator is the sum of the oxides without FE203 and FEO
    # LOI shouldnt be taken, and should further be removed
    num = thisdf[oxides_nofe].sum(axis=1)-thisdf['LOI(WT%)']
    
    for col in oxides_nofe:
        # normalizes    
        thisdf.loc[:, col] = thisdf[col]*(100/num)
    
    return thisdf


def guess_rock(thisdf):
    """

    Args:
        thisdf: GEOROC dataframe for one volcano

    Returns: a new column with a ROCK name based on TAS

    """
    # adds a new column that stores the guessed name
    thisdf.loc[:, 'ROCK'] = ['UNNAMED']*len(thisdf.index)
    
    # x- and y-axis from the TAS diagram
    x = thisdf['SIO2(WT%)'].astype('float')
    y = (thisdf['NA2O(WT%)'].astype('float') + thisdf['K2O(WT%)'].astype('float'))
    # x and y are greater than 0 (in fact both components of the sum y are greater than 0)
    cond1 = (thisdf['SIO2(WT%)'].astype('float') > 0) & (thisdf['NA2O(WT%)'].astype('float') > 0) & (thisdf['K2O(WT%)'].astype('float') > 0)    
    # lower anti-diagonal 1
    # a,b in ax+b
    ab = np.dot(inv(np.array([[52., 1.], [57., 1.]])), np.array([[5], [5.9]]))
    cond_ab = float(ab[0])*x+float(ab[1]) >= y
    cond_ba = float(ab[0])*x+float(ab[1]) < y
    # anti-diagonal 2
    # a,b in ax+b
    ab2 = np.dot(inv(np.array([[45., 1.], [49.4, 1.]])), np.array([[5], [7.3]]))
    cond_ab2 = float(ab2[0])*x+float(ab2[1]) < y
    cond_ba2 = float(ab2[0])*x+float(ab2[1]) >= y
    # upper anti-diagonal 3
    ab3 = np.dot(inv(np.array([[41., 1.], [52.5, 1.]])), np.array([[7], [14]]))
    cond_ab3 = float(ab3[0])*x+float(ab3[1]) < y
    cond_ba3 = float(ab3[0])*x+float(ab3[1]) >= y
    # lower diagonal
    cd = np.dot(inv(np.array([[49.4, 1.], [52., 1.]])), np.array([[7.3], [5.]]))
    cond_cd = float(cd[0])*x+float(cd[1]) < y
    cond_dc = float(cd[0])*x+float(cd[1]) >= y
    # diagonal
    cd2 = np.dot(inv(np.array([[53., 1.], [57., 1.]])), np.array([[9.3], [5.9]]))
    cond_cd2 = float(cd2[0])*x+float(cd2[1]) < y
    cond_dc2 = float(cd2[0])*x+float(cd2[1]) >= y
    # upper diagonal
    cd3 = np.dot(inv(np.array([[57.6, 1.], [63., 1.]])), np.array([[11.7], [7.]]))
    cond_cd3 = float(cd3[0])*x+float(cd3[1]) < y
    cond_dc3 = float(cd3[0])*x+float(cd3[1]) >= y
    # lower diagonal
    ef = np.dot(inv(np.array([[49.4, 1.], [45., 1.]])), np.array([[7.3], [9.4]]))
    cond_ef = float(ef[0])*x+float(ef[1]) < y
    cond_fe = float(ef[0])*x+float(ef[1]) >= y
    # diagonal
    ef2 = np.dot(inv(np.array([[53., 1.], [48.4, 1.]])), np.array([[9.3], [11.5]]))
    cond_ef2 = float(ef2[0])*x+float(ef2[1]) < y
    cond_fe2 = float(ef2[0])*x+float(ef2[1]) >= y
    # upper diagonal
    ef3 = np.dot(inv(np.array([[57.6, 1.], [52.5, 1.]])), np.array([[11.7], [14.]]))
    cond_ef3 = float(ef3[0])*x+float(ef3[1]) < y
    cond_fe3 = float(ef3[0])*x+float(ef3[1]) >= y

    # else will be FOIDITE
    thisdf.loc[cond1, 'ROCK'] = 'FOIDITE'

    # basalt
    thisdf.loc[cond1 & (x >= 45) & (x < 52) & (y < 5), 'ROCK'] = 'BASALT'

    # basaltic andesite
    thisdf.loc[cond1 & (x >= 52) & (x < 57) & cond_ab, 'ROCK'] = 'BASALTIC ANDESITE'

    # andesite
    thisdf.loc[cond1 & (x >= 57) & (x < 63) & cond_ab, 'ROCK'] = 'ANDESITE'

    # dacite
    # a,b in ax+b 
    d = np.dot(inv(np.array([[76., 1.], [69., 1.]])), np.array([[1.], [8.]]))
    cond_d1 = (x >= 63) & (float(d[0])*x + float(d[1]) >= y)
    thisdf.loc[cond1 & cond_d1 & cond_ab, 'ROCK'] = 'DACITE'

    # trachy-basalt
    thisdf.loc[(y >= 5) & cond_dc & cond_ba2, 'ROCK'] = 'TRACHYBASALT'

    # basaltic trachy-andesite
    thisdf.loc[cond_ba & cond_ba2 & cond_cd & cond_dc2, 'ROCK'] = 'BASALTIC TRACHYANDESITE'

    # trachy-andesite
    thisdf.loc[cond_ba & cond_ba2 & cond_cd2 & cond_dc3, 'ROCK'] = 'TRACHYANDESITE'
    
    # trachy-dacite
    thisdf.loc[cond_ba & cond_ba2 & cond_cd3 & (x < 69), 'ROCK'] = 'TRACHYTE/TRACHYDACITE'

    # rhyolite
    # a,b in ax+b
    cond_r1 = (float(d[0])*x + float(d[1]) < y)
    thisdf.loc[cond1 & cond_r1 & (x >= 69), 'ROCK'] = 'RHYOLITE'

    # phonolite
    thisdf.loc[cond_ab2 & cond_ef3, 'ROCK'] = 'PHONOLITE'

    # tephri-phonolite
    thisdf.loc[cond_ab2 & cond_fe3 & cond_ef2 & cond_ba3, 'ROCK'] = 'TEPHRI-PHONOLITE'

    # phono-tephrite
    thisdf.loc[cond_ab2 & cond_fe2 & cond_ef & cond_ba3, 'ROCK'] = 'PHONO-TEPHRITE'

    # tephrite
    # a,b in ax+b
    t = np.dot(inv(np.array([[41., 1.], [45., 1.]])), np.array([[7.], [5.]]))
    cond_t1 = (float(t[0])*x + float(t[1]) <= y) & cond_ab2 & cond_ba3 & cond_fe
    cond_t2 = (float(t[0])*x + float(t[1]) >= y) & (y >= 3) & (x >= 41) & (x < 45)
    thisdf.loc[cond_t1 | cond_t2, 'ROCK'] = 'TEPHRITE/BASANITE'

    # picro-basalt
    thisdf.loc[cond1 & (y < 3) & (x >= 41) & (x < 45), 'ROCK'] = 'PICROBASALT'

    return thisdf
    

def extract_date(entry):
    
    result = np.nan
    
    # checks if contains a digit
    if bool(re.search(r'\d', entry)):
        # looks for ERUPTION
        fnd1 = re.findall('ERUPTION ([0-9-.]{3,})', entry)+re.findall('([0-9-.]{3,}) ERUPTION', entry)
        # looks for B.C
        fnd2 = re.findall('[0-9]{1,} B.C', entry)
        # looks for long digits with dots
        fnd3 = re.findall('[0-9.]{5,}', entry)
        # looks for MONTHS
        fndmonth = re.findall('(JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)|AUG(?:UST)?|SEPT(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?) ([0-9,\s]*)' ,entry)
        # looks for AD
        fndAD = re.findall('([0-9-.\s]{3,} AD)', entry) + re.findall('([0-9-.\s]{3,} A. D.)', entry)
        # looks for BETWEEN
        fndbetw = re.findall('BETWEEN [0-9]* AND [0-9]*', entry)
        # looks for ERUPTION YEAR(s)
        fndEY = re.findall('ERUPTION YEAR [0-9]*', entry) + re.findall('ERUPTION YEARS [0-9]*', entry)
        # looks for dates separated by /
        fnddat = re.findall('\d*/\d*/\d*', entry)
        fnd = fnd1 + fnd2 + fnd3 + fndmonth + fndAD + fndbetw + fndEY + fnddat
        
        if len(fnd) > 0:
            testi = entry.replace('-', ' ').replace('.', ' ')
            # this loses the years written in less than 4 digits
            fnddat = [x for x in testi.split() if x.isdigit() and len(x) == 4]
            if len(fnddat) == 1:
                result = float(fnddat[0])
            if len(fnddat) == 2:
                # uses only the start year
                result = float(fnddat[0]) 
        
    return result                              


def plot_TAS(thisfig):
    """

    Args:
        thisfig: the figure to be updated

    Returns: Plots a TAS diagram in the background

    """
    X = [[41, 41, 45, 45], [45, 45, 52, 52], [52, 52, 57, 57], [57, 57, 63, 63], [63, 63, 69, 77],
         [41, 41, 45, 49.4, 45, 45, 41], [45, 49.4, 52, 45], [45, 48.4, 53, 49.4, 45], [49.4, 53, 57, 52, 49.4],
         [53, 48.4, 52.5, 57.6, 53], [53, 57.6, 63, 57, 53]]
    Y = [[0, 3, 3, 0], [0, 5, 5, 0], [0, 5, 5.9, 0], [0, 5.9, 7, 0], [0, 7, 8, 0],
         [3, 7, 9.4, 7.3, 5, 3, 3], [5, 7.3, 5, 5], [9.4, 11.5, 9.3, 7.3, 9.4], [7.3, 9.3, 5.9, 5, 7.3],
         [9.3, 11.5, 14, 11.7, 9.3], [9.3, 11.7, 7, 5.9, 9.3]]
    tasnames = ['picro-basalt', 'basalt', 'basaltic andesite', 'andesite', 'dacite',
                'tephrite', 'trachybasalt', 'phono-tephrite', 'basaltic trachyandesite',
                'tephri-phonolite', 'trachyandesite']

    for (x, y) in zip(X, Y):
        thisfig.add_traces(
            go.Scatter(
                x=x,
                y=y,
                # mode='none',
                mode='lines',
                line_color='grey',
                fill='toself',
                # fillcolor= 'rgba(135, 206, 250, 0.5)'
                fillcolor='lightblue',
                opacity=0.2,
                name=tasnames[X.index(x)],
                showlegend=False
            ),
            rows=2, cols=1,
        )
    # add ryholite
    thisfig.add_traces(
        go.Scatter(
            x=[69, 69],
            y=[8, 13],
            mode='lines',
            line_color='lightgrey',
            showlegend=False
        ),
        rows=2, cols=1,
    )
    thisfig.add_traces(
        go.Scatter(
            x=[69, 69, 77, 77, 69],
            y=[8, 13, 13, 0, 8],
            mode='none',
            # mode='lines',
            # line_color='grey',
            fill='toself',
            # fillcolor= 'rgba(135, 206, 250, 0.5)'
            fillcolor='lightblue',
            opacity=0.2,
            name='rhyolite',
            showlegend=False
        ),
        rows=2, cols=1,
    )
    # add trachyte
    # a = 0.562, b=-20.8
    thisfig.add_traces(
        go.Scatter(
            x=[57.8, 65],
            y=[11.7, 15.7],
            mode='lines',
            line_color='lightgrey',
            showlegend=False
        ),
        rows=2, cols=1,
    )
    thisfig.add_traces(
        go.Scatter(
            x=[57.8, 65, 69, 69, 63, 57.8],
            y=[11.7, 15.7, 13, 8, 7, 11.7],
            mode='none',
            # mode='lines',
            # line_color='grey',
            fill='toself',
            # fillcolor= 'rgba(135, 206, 250, 0.5)'
            fillcolor='lightblue',
            opacity=0.2,
            name='trachyte,<br>trachydacite',
            showlegend=False
        ),
        rows=2, cols=1,
    )
    # add phonolyte
    # a = -0.433, b=36.783
    thisfig.add_traces(
        go.Scatter(
            x=[50, 52.5],
            y=[15.13, 14],
            mode='lines',
            line_color='lightgrey',
            showlegend=False
        ),
        rows=2, cols=1,
    )
    thisfig.add_traces(
        go.Scatter(
            x=[50, 65, 57.8, 50],
            y=[15.13, 15.7, 11.7, 15.13],
            mode='none',
            # mode='lines',
            # line_color='grey',
            fill='toself',
            # fillcolor= 'rgba(135, 206, 250, 0.5)'
            fillcolor='lightblue',
            opacity=0.2,
            name='phonolyte',
            showlegend=False
        ),
        rows=2, cols=1,
    )

    return thisfig
    

def add_alkaline_series(thisfig):
    '''
        Alkaline series
        diagram: SiO2 vs K2O
        reference: Peccerillo and Taylor (1976)
        Between calc-alkaline and tholeiite series (lower line): (48, 0.3) (52, 0.5) (56, 0.7) (63, 1.0) (70, 1.3) (78, 1.6)
        Between high-K calc-alkaline and calc-alkaline series (middle line): (48, 1.2) (52, 1.5) (56, 1.8) (63, 2.4) (70, 3.0)
        Between shoshonite and high-K calc-alkaline series (upper line): (48, 1.6) (52, 2.4) (56, 3.2) (63, 4.0)
    '''

    thisfig.add_trace(
        go.Scatter(
            x = [48, 52, 56, 63, 70, 78],
            y = [0.3, 0.5, 0.7, 1.0, 1.3, 1.6],
            mode='lines',
            name='calc-alkaline and tholeiite',
            showlegend=False
        ),
        row=4, col=1,
    )
    
    thisfig.add_trace(
        go.Scatter(
            x = [48, 52, 56, 63, 70],
            y = [1.2, 1.5, 1.8, 2.4, 3.0],
            mode='lines',
            name='high-K calc-alkaline and calc-alkaline',
            showlegend=False
        ),
        row=4, col=1,
    )
    
    thisfig.add_trace(  
        go.Scatter(
            x = [48, 52, 56, 63],
            y = [1.6, 2.4, 3.2, 4.0],
            mode='lines',
            name='shoshonite and high-K calc-alkaline',
            showlegend=False
        ),
        row=4, col=1,
    )
    
    return thisfig    
    
    
def add_alkaline_line(thisfig):
    '''
        Alkalic & sub-alkalic division
        diagram: SIO2 vs NA2O + K2O
        reference: Irvine and Baragar ( 1971, fig. 3B, p.532)
        Coordinates: (39.2,0) (40, 0.4) (43.2, 2) (45, 2.8) (48, 4) (50, 4.75) (53.7,6) (55, 6.4) (60, 8) (65, 8.8) (77.4, 10)    
    
    '''

    thisfig.add_traces(
        go.Scatter(
            x = [39.2, 40, 43.2, 45, 48, 50, 53.7, 55, 60, 65, 74.4],
            y = [0, 0.4, 2, 2.8, 4, 4.75, 6, 6.4, 8, 8.8, 10],
            mode='lines',
            name='Alkalic & sub-alkalic division',
            showlegend=False,
        ),
        rows=2, cols=1,
    )    
    
    return thisfig    


def detects_chems(thisdf, chem1, chem2, theselbls):
    """

    Args:
        thisdf: a dataframe of chemicals
        chem1: list (synthax) for usual chemicals
               first is SIO2, second is NA20, 3rd id K20
        chem2: list (synthax) for more chemical

    Returns: an updated dataframe containing the data for a TAS plot
             also, abnormal other chemicals are computed

    """
    # replaces nan with 0
    thisdf = thisdf.fillna(0)
    # removes if 80 >= SIO2 is > 0
    thisdf = thisdf[(thisdf[chem1[0]] <= 80) &  (thisdf[chem1[0]] > 0)  & (thisdf['FEOT(WT%)'] > 0)]
    thisdf[chem1[1]+'+'+chem1[2]] = thisdf[chem1[1]].astype('float') + thisdf[chem1[2]].astype('float')

    for mc in chem2:
        st_mc = thisdf[mc].astype('float').std()
        mn_mc = thisdf[mc].astype('float').mean()
        if not (np.isnan(st_mc)):
            mstd = mn_mc + st_mc
        else:
            mstd = mn_mc
        thisdf['excess' + mc] = 0
        thisdf.loc[thisdf[mc].astype('float') > mstd, 'excess' + mc] = 2 ** (chem2.index(mc))

    thisdf['color'] = [theselbls[x] for x in list(thisdf.loc[:, ['excess' + mc for mc in chem2]].sum(axis=1).values)]
    
    return thisdf


def plot_chem(thisfig, thisdf, chem1, theselbls):
    """

    Args:
        thisfig: figure to be updated
        thisdf: dataframe from Georoc
        chem1: list (synthax) for usual chemicals
               first is SIO2, second is NA20, 3rd id K20

    Returns: Plots a scatter plot of the chemical composition

    """
    if theselbls == lbls2:
        thiscolorscale = colorscale2
    else:
        thiscolorscale = colorscale   
        
    # if dataframe contains VEI info, this plots different symbols depending on VEI       
    if 'VEI' in list(thisdf):
        thisdf['symbol'] = np.where(thisdf['VEI'].isnull(), 'circle', 
                                    (np.where(thisdf['VEI'].astype('float') <= 2, 'circle', 'triangle-up')))
    else:
        # sometimes two materials are present, this is to retrieve the first one
        oldvalues = [x for x in list(thisdf['MATERIAL'].unique()) if (type(x) == str and '[' in x)]
        newvalues = {}
        for x in oldvalues:
            newvalues[x] = x.split('[')[0].strip() 
        thisdf['MATERIAL'].replace(to_replace=newvalues, inplace=True)
        # in case some MATERIAL entry are missing or off
        thisdf['MATERIAL'][~thisdf['MATERIAL'].isin(['WR', 'GL', 'INC', 'MIN'])] = 'UNKNOWN'
        # adjusts symbol based on material
        thisdf['symbol'] = thisdf['MATERIAL'].replace(to_replace={'WR': 'circle', 'GL': 'diamond', 'INC': 'square', 'MIN': 'x', 'UNKNOWN': 'diamond-wide'})
        
    # plots by symbols (that is material)
    if 'VEI' in list(thisdf):
        full_symbol = {'circle': 'VEI<=2', 'triangle-up': 'VEI>=3'}
        short_symbol = ['circle', 'triangle-up'] 
    else:
        full_symbol = {'circle': 'whole rock', 'diamond': 'volcanic glass', 'square': 'inclusion', 'x': 'mineral', 'diamond-wide': 'UNKNKOWN'}
        short_symbol = ['circle', 'diamond', 'square', 'x', 'diamond-wide'] 
    
    for symbol in short_symbol:
        thismat = thisdf[thisdf['symbol'] == symbol]
        # custom data
        if 'VEI' in list(thisdf):
            thiscustomdata = thismat[chem1[1]].astype(str)+' '+chem1[1]+' '+thismat['MATERIAL']+' VEI='+thismat['VEI']  
        else:
            thiscustomdata = thismat[chem1[1]].astype(str)+' '+chem1[1]+', '+thismat['ROCK']
        # plots
        thisfig.add_traces(
            go.Scatter(
                x=thismat[chem1[0]],
                y=thismat[chem1[1]+'+'+chem1[2]],
                customdata=thiscustomdata,
                hovertemplate='x=%{x}<br>y=%{y}<br>%{customdata}',
                mode='markers',
                marker_symbol=thismat['symbol'],
                marker_color='cornflowerblue',
                name=full_symbol[symbol],
                showlegend=True,
            ),
            rows=2, cols=1,
        )
    for symbol in short_symbol:
        thismat = thisdf[thisdf['symbol'] == symbol]    
        # plots histogram on top
        thisfig.add_traces(
            go.Histogram(
                x=thismat[chem1[0]],
                name=full_symbol[symbol]+' hist',
                marker_color='cornflowerblue',
                histnorm='percent',
            ),
            rows=1, cols=1,
        )
        

    # edits title of legends              
    thisfig['layout']['legend']['title']['text'] = ''              
        
    # styles the markers
    thisfig.update_traces(marker=dict(size=12,
                                     line=dict(width=2,
                                                color='DarkSlateGrey')),
                          selector=dict(mode='markers'))
                         
    if theselbls == lbls2:
        title = 'Chemical Rock Composition from PetDB'
    else:
        title = 'Chemical Rock Composition from Georoc'

    thisfig.update_xaxes(title_text='SiO<sub>2</sub>(wt%)', row=2, col=1, range=[30, 80])
    thisfig.update_yaxes(title_text='Na<sub>2</sub>O+K<sub>2</sub>O(wt%)', row=2, col=1, range=[0, 20])
    thisfig.update_layout(
        title='<b>'+title+'</b>',
        autosize=False,
        width = 900,
        height =700
    )    
    
    return thisfig
    
        
def match_GVPdates(volcano_name, date, gvpvname):
    """

    Args:
        volcano_name: GEOROC name
        date: GEOROC date, it can also take the value "forall", in which case it maps all GEOROC dates to GVP dates
        gvpvname: GVP volcano name
    Returns: matching GVP dates, it is a pair for a single GEOROC date, and a list of pairs for all GEOROC dates

    """
    
    date_gvp = []   
    
    # retrieves dates from georoc
    dfgeoroc = load_georoc(volcano_name)
    dvv = dfgeoroc[dfgeoroc['LOCATION-4'] == ' ' + volcano_name]
    dmy = dvv[['ERUPTION DAY', 'ERUPTION MONTH', 'ERUPTION YEAR']]
    dmy = dmy.dropna(how='all')
    if len(dmy.index) > 0:
        # dates from GVP
        gvpdate = df[df['Volcano Name'] == gvpvname].drop(['Start Year', 'End Year'], axis=1)
        gvpdate['Start Year'] = pd.to_numeric(df['Start Year'])
        gvpdate['End Year'] = pd.to_numeric(df['End Year'])
        # if NaN for 'End Year', uses 'Start Year'
        gvpdate['End Year'] = gvpdate.apply(
            lambda row: row['Start Year'] if pd.isnull(row['End Year']) else row['End Year'], axis=1)

        if not(date == 'forall'):
            # retrieves the georoc date when only one date is of interest
            if '-' in date:
                s = date.split('-')
                gy = int(s[0])
            else:
                gy = int(date)
            gy_list = [gy]
        else:
            # this is to retrieve all dates
            gy_list = dmy['ERUPTION YEAR'].unique()
            
        all_dates_gvp = []
         
        for gy in gy_list:
            # matches the dates from both databases
            gy = int(gy)
            fnd = gvpdate[(gvpdate['Start Year'].astype(int) <= gy) & (gvpdate['End Year'] == gy)]
            if len(fnd.index) > 0:
                # gvp
                if not(date == 'forall'):
                    date_gvp = [str(int(fnd['Start Year'])), str(int(fnd['End Year']))]
                else:
                    date_gvp = fnd[['Start Year', 'End Year']].astype(int).astype(str).values
            else:
                fndbefore = gvpdate[(gvpdate['Start Year'] <= gy) & (gvpdate['End Year'] != gy)]
                if len(fndbefore.index) > 0:
                    # gvp (this if condition is in case not confirmed eruptions are considered)
                    # in the new excel, only confirmed eruptions are here
                    if fndbefore.iloc[0]['Eruption Category'] == 'Confirmed Eruption':
                        rwidx = 0
                    elif fndbefore.iloc[1]['Eruption Category'] == 'Confirmed Eruption':
                        rwidx = 1
                    else:
                        rwidx = 2
                    if not(date == 'forall'):    
                        date_gvp = [str(int(fndbefore.iloc[rwidx]['Start Year'])),
                                    str(int(fndbefore.iloc[rwidx]['End Year']))]
                    else:
                        date_gvp = [[str(int(fndbefore.iloc[rwidx]['Start Year'])),
                                    str(int(fndbefore.iloc[rwidx]['End Year']))]] 
                else:
                    date_gvp = ['not found']  
                                        
            for dg in date_gvp:
                if type(dg) != str: 
                    all_dates_gvp.append([gy, dg])
                         
        if date == 'forall':
            date_gvp = all_dates_gvp
                            
    return date_gvp


def filter_date(thisdate, dff):
    """

    Args:
        thisdate: the eruption dates, possibly all
        dff: GEOROC dataframe

    Returns: dataframe for this date

    """
    if not ((thisdate == 'all') or (thisdate == 'start')):
        # recovers and filters by dates
        if '-' in thisdate:
            s = thisdate.split('-')
            mask = (dff['ERUPTION YEAR'] == float(s[0])) & (dff['ERUPTION MONTH'] == float(s[1]))
            if len(s) == 3:
                mask = mask & (dff['ERUPTION DAY'] == float(s[2]))

        else:
            mask = dff['ERUPTION YEAR'] == float(thisdate)

        dff = dff[mask].dropna(
                subset=['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], how='all')
                
    return dff
    

def update_chemchart(thisvolcano_name, thisfig, thisdate):
    """

    Args:
        thisvolcano_name: name of a volcano
        thisfig: the figure being updated
        thisdate: the eruption dates, possibly all

    Returns: Updates both the chemical plot based on user's inputs, 
             Also the dataframe used to draw the plot

    """
    colsGvp = ['Volcano Name', 'Start Year', 'End Year', 'VEI']
    
    # not sure why I need to load again but anyway
    if not (thisvolcano_name == "start") and not(thisvolcano_name is None):
        dfgeoroc = load_georoc(thisvolcano_name)
    
    # checks if data is present
    if not (thisvolcano_name is None) and thisvolcano_name.upper() in grnames:
        # extracts by name
        # removes the nan rows for the 3 chemicals of interest
        dff = dfgeoroc.dropna(
            subset=['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], how='all')
          
        # update dff to detect abnormal chemicals
        dff = detects_chems(dff, ['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], morechems, lbls)   
        
        # filter dff by dates
        dff = filter_date(thisdate, dff)       
            
    else:
        # empty dataframe with right columns
        d = {'SIO2(WT%)': [], 'NA2O(WT%)': [], 'TIO2(WT%)': [], 'AL2O3(WT%)': [], 'MGO(WT%)': [], 'FEOT(WT%)': [],
             'K2O(WT%)': [], 'NA2O(WT%)+K2O(WT%)': [], 'color': [], 'P2O5(WT%)': [],
             'FEO(WT%)': [], 'CAO(WT%)': [], 'MGO(WT%)': [], 'ERUPTION YEAR': [], 'color': [], 'MATERIAL': [], 'ROCK': []}
        dff = pd.DataFrame(data=d)

    # adds the TAS layout
    thisfig = plot_TAS(thisfig)
    # draws the scatter plot
    thisfig = plot_chem(thisfig, dff, ['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], lbls)
    
    # take the first 4 and removes UNNAMED, if present
    majorrocks = [x for x in list(dff['ROCK'].value_counts().index[0:5]) if x != 'UNNAMED']
    # majorrocks_geo = [GEOROC_rock_col[GEOROC_rocks.index(mr)] for mr in majorrocks]
    
    # string
    strc = ''
    for mr in majorrocks:
        strc += mr + ', '
    strc = strc[:-2]
        
    thisfig.update_layout(
        annotations=[dict(xref='paper',
                          yref='paper',
                          x=0.5, y=-0.25,
                          showarrow=False,
                          text=strc)],
                )

    return thisfig, dff
    

def update_onedropdown(thisvolcano_name):
    """

    Args:
        thisvolcano_name: name of a chosen volcano

    Returns: Updates eruption dates choice based on volcano name

    """

    # checks if data is present
    if not (thisvolcano_name is None) and not (thisvolcano_name == "start") and thisvolcano_name.upper() in grnames:
        # extracts by name
        # loads Georoc data based on volcano_name
        dfgeoroc = load_georoc(thisvolcano_name)

        # removes the nan rows for the 3 chemicals of interest
        dff = dfgeoroc.dropna(
            subset=['SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)'], how='all')[chemcols[1:4]]
        # removes the rows if no date is available, and then removes the duplicate dates
        dff = dff.dropna(subset=['ERUPTION DAY', 'ERUPTION MONTH', 'ERUPTION YEAR'],
                         how='all').astype('float').drop_duplicates().values

        # extracts the dates for display
        dates = []
        for d in [list(x) for x in dff]:
            dd = []
            for i in range(3):
                if np.isnan(d[i]) == False and i <= 2:
                    dd.append(d[i])
                else:
                    if i <= 2:     
                        dd.append(0)
            dates.append(dd[::-1])
        # each date is a list
        dates.sort(key=lambda x: (-x[0], -x[1], -x[2])) 
        
        dates_str = []
        for ymd in dates:
            dd = ''
            for d in ymd:
                if d > 0:
                    dd += str(int(d)) + '-'
            dates_str.append(dd[:-1])
        
        opts = [{'label': i, 'value': i} for i in ['all'] + [x for x in dates_str]]
    else:
        opts = [{'label': i, 'value': i} for i in ['all']]
    return opts


def GEOROC_majorrocks(tect_setting): 
    """

    Args:
        tect_setting: 

    Returns: a dataframe with volcano names and their GEOROC major rocks 1,2 and 3.

    """
    
    tect_setting = [x for x in tect_setting if x != None and x != ' PetDB']
    # GEOROC
    if ' all GEOROC' in tect_setting and len(tect_setting)==1:
        # format tectonic setting names
        tect_GEOROC = [x.strip().replace(' ', '_').replace('/',',') for x in new_tectonic_settings]
    else: 
        # new tectonic settings
        tect_GEOROC = [x.strip().replace(' ', '_').replace('/',',') for x in tect_setting if (x !=' all GEOROC') and (x!=' PetDB')]
        
    alldf = pd.DataFrame()
        
    # check if file exists
    for ts in tect_GEOROC:
        # lists files in the folder
        if ts +'.txt' in os.listdir('../GeorocDataset'):
            # file exists, just reads it
            thisdf = pd.read_csv('../GeorocDataset/' + str(ts)+'.txt')
            
        else:
            # file needs to be created    
            tect_cases = new_tectonic_dict[ts.replace('_', ' ').replace(',','/')].split('+')
          
            if len(tect_cases) < 3: 
                cond = dfv['Tectonic Settings'].isin(tect_cases)
            elif len(tect_cases) == 3:
                cond1 = dfv['Tectonic Settings'] == tect_cases[0]
                cond2 = dfv['Tectonic Settings'] == tect_cases[2].split(';')[0]
                cond3 = dfv['Subregion'].isin(tect_cases[2].split(';')[1:])
                cond = cond1 | ((cond2)&(cond3))
            else:
                cond1 = (dfv['Tectonic Settings'] == tect_cases[0]) | (dfv['Tectonic Settings'] == tect_cases[1])
                cond2 = dfv['Tectonic Settings'] == tect_cases[3].split(';')[0]
                cond3 = dfv['Subregion'].isin(tect_cases[3].split(';')[1:])
                cond = cond1 | ((cond2)&(cond3))
            volcanoesbyts = dfv[cond]['Volcano Name'].unique()
            # make sure there is a matching GEOROC volcano
            volcanoesbyts = [v for v in  volcanoesbyts if v in dict_GVP_Georoc.keys()]
    
            all_majorrocks = []
            
            for thisvolcano in volcanoesbyts:
                # from GVP to GEOROC
                thisvolcano = dict_GVP_Georoc[thisvolcano]
                thisdf = load_georoc(thisvolcano)
                
                for mat in ['WR', 'GL', 'INC']:   
                    thisdftmp = thisdf[thisdf['MATERIAL'].str.contains(mat)]
                    
                    totalsamples = len(thisdftmp.index)    
                    # removes UNNAMED, if present
                    allrocks = [x for x in list(thisdftmp['ROCK'].value_counts().index[0:]) if x != 'UNNAMED']
                    # computes percentage
                    allrocksvalues = [thisdftmp['ROCK'].value_counts()[r] for r in allrocks]
                    allrocksvaluesperc = [round(100*(thisdftmp['ROCK'].value_counts()[r]/totalsamples),1) for r in allrocks]
                    #
                    majorrocks = []
                    cnts = []
                    # >= 10% to qualify as major rock
                    for r, rv, cnt in zip(allrocks, allrocksvaluesperc, allrocksvalues):
                        if rv >= 10:
                            majorrocks += [r]
                            cnts+= [cnt]
                    # 
                    if len(majorrocks) >= 5:
                        majorrocks = majorrocks[0:5]
                        cnts = cnts[0:5]
                    else:
                        majorrocks += ['No Data', 'No Data', 'No Data', 'No Data', 'No Data']
                        majorrocks = majorrocks[0:5]
                        cnts += [0, 0, 0, 0, 0]
                        cnts = cnts[0:5]

                    all_majorrocks.append([thisvolcano]+[mat]+majorrocks+cnts)
                  
            thisdf = pd.DataFrame(all_majorrocks, columns = ['Volcano Name', 'material', 'GEOROC Major Rock 1', 'GEOROC Major Rock 2', 'GEOROC Major Rock 3', 'GEOROC Major Rock 4', 'GEOROC Major Rock 5', 'cnt 1', 'cnt 2', 'cnt 3', 'cnt 4', 'cnt 5'])
            for col in ['GEOROC Major Rock 1', 'GEOROC Major Rock 2', 'GEOROC Major Rock 3', 'GEOROC Major Rock 4', 'GEOROC Major Rock 5']:
                newcol = col.split('GEOROC ')[1]
                thisdf[newcol] = thisdf[col].replace(GEOROC_rocks, GEOROC_rock_col)
                
            thisdf.to_csv( '../GeorocDataset/'+str(ts)+'.txt')
        alldf = alldf.append(thisdf)     

    return alldf


def update_GEOrockchart(thisdf, db): 
    """

    Args:
        thisdf: output of GEOROC_majorrocks 
        db: specifies whether GEOROC and/or PetDB is used
    Returns: sunburst chart with GEOROC major rocks

    """
    this_discrete_map = {}
    for r in GEOROC_rocks:
        # from GEOROC to GVP rock name
        rgvp = GEOROC_rock_col[GEOROC_rocks.index(r)] 
        z = [0] * len(rock_col)
        z[rock_col.index(rgvp)] = 1
        this_discrete_map[r] = 'rgb' + str(rocks_to_color(z))
    
    if 'PetDB' in db and not('GEOROC' in db):
        thistitle = '<b>Rock Composition from PetDB</b> <br>'
    elif 'GEOROC' in db and not('PetDB' in db):
        thistitle = '<b>Rock Composition from GEOROC</b> <br>'
    elif 'PetDB' in db and 'GEOROC' in db:
        thistitle = '<b>Rock Composition from GEOROC and PetDB</b> <br>'
        dfpdb = thisdf[thisdf['db'] == 'PetDB'] 
        dfgeo = thisdf[thisdf['db'] == 'GEOROC']
        dfgeo['Volcano Name'] = dfgeo['Volcano Name'].apply(lambda x: dict_Georoc_GVP[x])
        mr1 = []
        mr2 = []
        mr3 = []
        # union of names
        for v in list(set(dfgeo['Volcano Name']).union(set(dfpdb['Volcano Name']))):
            d1 = {}
            # GEOROC
            if v in list(dfgeo['Volcano Name']):
                rck1 = dfgeo[dfgeo['Volcano Name'] == v][['db Major Rock 1', 'db Major Rock 2', 'db Major Rock 3']].values[0]
                cnt1 = dfgeo[dfgeo['Volcano Name'] == v][['cnt 1', 'cnt 2', 'cnt 3']].values[0]
                for r, c in zip(rck1, cnt1):
                    d1[r] = c
             
            # add PetDB
            if v in list(dfpdb['Volcano Name']):
                cnt2 = dfpdb[dfpdb['Volcano Name'] == v][['cnt 1', 'cnt 2', 'cnt 3']].values[0]
                rck2 = dfpdb[dfpdb['Volcano Name'] == v][['db Major Rock 1', 'db Major Rock 2', 'db Major Rock 3']].values[0]
                for r, c in zip(rck2, cnt2):
                    if r in d1.keys():
                        d1[r] += c
                    else:    
                        d1[r] = c  
                            
            # sorts    
            newmr = [list(x) for x in sorted(d1.items())[0:3]]+[['No Data', 0], ['No Data', 0]]
            newmr.sort(key=lambda x: x[1], reverse=True)
            mr1.append(newmr[0][0])
            mr2.append(newmr[1][0])
            mr3.append(newmr[2][0])   
        thisdf = pd.DataFrame({'db Major Rock 1': mr1, 'db Major Rock 2': mr2, 'db Major Rock 3': mr3})             
           
    else:
        thistitle = '<b>Rock Composition</b><br>'
      
    if len(thisdf.index) > 0:
        
        fig = px.sunburst(thisdf.replace('No Data', ' '), path=["db Major Rock 1", "db Major Rock 2", "db Major Rock 3"],
                          color='db Major Rock 1', color_discrete_map=this_discrete_map,
                          title=thistitle)
                             
        label = fig['data'][0]['labels']
        current_colors = fig['data'][0]['marker']['colors']
        new_colors = []
        for lab, colr in zip(label, current_colors):
            if lab != ' ':
                new_colors.append(colr)
            else:
                new_colors.append('rgb(255, 255, 255)')                        
        
        fig['data'][0]['marker']['colors'] = new_colors
        
    else:
        fig = go.Figure()
        fig.update_layout(title=thistitle) 
        fig.add_traces(
            go.Sunburst(
                labels=['Major Rock 1', 'Major Rock 2', 'Major Rock 3'],
                parents=['', 'Major Rock 1', 'Major Rock 2'],
                marker=dict(
                    colorscale='Greys'
                )
            ),
        )
    
    txt = str(len(thisdf.index)) + ' volcano(es)'
        
    fig.update_layout(
        annotations=[dict(xref='paper',
                          yref='paper',
                          x=0.5, y=-0.25,
                          showarrow=False,
                          text=txt)],
                ) 
                             
    return fig
    
    
def createGEOROCaroundGVP():
    """

    Args:
        none

    Returns: recreates the file GEOROCaroundGVP.csv and returns its content as df

    """
    gvp_names = dfv[['Volcano Name', 'Latitude', 'Longitude']]
    gvp_names = gvp_names.append(dfvne[['Volcano Name', 'Latitude', 'Longitude']])
    # removes unnamed
    gvp_names = gvp_names[gvp_names['Volcano Name'] != 'Unnamed']

    # list all file names, takes the folder names from the Mapping folder to have only folders
    lst_arcs = []
    path_for_arcs = os.listdir('../GeorocGVPmapping')
    
    df_GEOROC = pd.DataFrame()

    for folder in path_for_arcs:
        # lists files in each folder, takes names from the Mapping folder in case different copies of the csv exist
        tmp = os.listdir('../GeorocGVPmapping/%s' % folder)
        # adds the path to include directory 
        lst_arcs += ['%s' % folder + '/' + f[:-4] + '.csv' for f in tmp]
        
    for arc in lst_arcs:
        # this finds the latest file
        newarc = fix_pathname(arc)
        # reads the file
        dftmp = pd.read_csv('../GeorocDataset/%s' %newarc, low_memory=False, encoding='latin1')
        if not('Inclusions_comp' in arc) and not('ManualDataset' in arc):
            # keeps only volcanic rocks
            dfvol = dftmp[dftmp["ROCK TYPE"] == 'VOL']
            dfvol = dfvol.drop('ROCK TYPE', 1)
        else:
            dfvol = dftmp
            
            if 'Inclusions_comp' in arc: 
                # different names
                dfvol = fix_inclusion(dfvol)
                dfvol['MATERIAL'] = 'INC'
            else:
                # missing isotopes
                for cl in ['PB206_PB204', 'PB207_PB204', 'PB208_PB204', 'SR87_SR86', 'ND143_ND144']:
                    dfvol[cl] = np.nan   
        
        # gathers the GEOROC data of interest (to be displayed on the map, and before that, for computing rocks)   
        dfvol = dfvol[['LOCATION', 'LATITUDE MIN', 'LATITUDE MAX', 'LONGITUDE MIN', 'LONGITUDE MAX', 'SAMPLE NAME', 'MATERIAL'] + oxides + ['PB206_PB204', 'PB207_PB204', 'PB208_PB204', 'SR87_SR86', 'ND143_ND144']]
        dfvol['arc'] = [arc]*len(dfvol.index)
        df_GEOROC = df_GEOROC.append(dfvol)
        
    # FEO normalization     
    df_GEOROC = with_FEOnorm(df_GEOROC)
    # add rock names
    df_GEOROC = guess_rock(df_GEOROC)
    # rock names excluding inclusions
    df_GEOROC['ROCK no inc'] = df_GEOROC['ROCK']
    df_GEOROC.loc[df_GEOROC['MATERIAL'] == 'INC', 'ROCK no inc'] = ''
            
    # GVP volcanoes, latitudes and longitudes
    gvp_nm = gvp_names['Volcano Name']
    gvp_lat = gvp_names['Latitude']
    gvp_long = gvp_names['Longitude']

    colgr = ['LOCATION', 'LATITUDE MIN', 'LATITUDE MAX', 'LONGITUDE MIN', 'LONGITUDE MAX', 'SAMPLE NAME', 'ROCK', 'ROCK no inc', 'arc'] + chemicals_settings[0:1]
    colgvp = ['Volcano Name', 'Latitude', 'Longitude']

    # initializes dataframe to contatin the GEOROC samples matching GVP volcanoes
    match = pd.DataFrame()

    for nm, lt, lg in zip(gvp_nm, gvp_lat, gvp_long):
        lt_cond = (df_GEOROC['LATITUDE MIN'].astype(float)-.5 <= lt) & (df_GEOROC['LATITUDE MAX'].astype(float)+.5 >= lt)
        lg_cond = (df_GEOROC['LONGITUDE MIN'].astype(float)-.5 <= lg) & (df_GEOROC['LONGITUDE MAX'].astype(float)+.5 >= lg)
        dfgeo = df_GEOROC[(lt_cond) & (lg_cond)][colgr]
        if len(dfgeo.index) > 0:
            dfgeo['Volcano Name'] = [nm]*len(dfgeo.index)
            dfgeo['Latitude'] = [lt]*len(dfgeo.index)
            dfgeo['Longitude'] = [lg]*len(dfgeo.index)
            match = match.append(dfgeo)

    match = match.drop_duplicates()
    # group sample names when same location
    matchgroup = match.groupby(['LOCATION', 'LATITUDE MIN', 'LATITUDE MAX', 'LONGITUDE MIN', 'LONGITUDE MAX', 'arc']).agg(lambda x: list(x))
    matchgroup = matchgroup.drop(columns=['Latitude', 'Longitude'])
    # attaches a new tectonic setting 
    matchgroup['Volcano Name'] = matchgroup['Volcano Name'].apply(lambda x: list(set([find_new_tect_setting(y) for y in x])))     
    # sometimes the same sample is found in the intersection of several volcanoes
    matchgroup['SAMPLE NAME'] = matchgroup['SAMPLE NAME'].apply(lambda x: list(set([y.split('/')[0].split('[')[0] for y in x])))
    # this shortens and keeps only the first 3 samples 
    matchgroup['SAMPLE NAME'] = matchgroup['SAMPLE NAME'].apply(lambda x: x if len(x) <= 3 else list(set(x[0:3]))+['+'+str(len(x)-3)])
    # this creates a single string out of different sample names attached to one location
    matchgroup['SAMPLE NAME'] = matchgroup['SAMPLE NAME'].apply(lambda x: " ".join(x))
    # 
    matchgroup['ROCK'] = matchgroup['ROCK'].apply(lambda x: list(Counter(x).items()))
    matchgroup['ROCK no inc'] = matchgroup['ROCK no inc'].apply(lambda x: list(Counter(x).items()))
    
    for c in chemicals_settings[0:1]:
        # matchgroup[c] = matchgroup[c].apply(lambda x: np.histogram(x, bins=np.linspace(30,80,6))[0])
        matchgroup[c+'mean'] = matchgroup[c].apply(lambda x: statistics.mean(x))
    matchgroup.to_csv('../GeorocDataset/GEOROCaroundGVP.csv')
    
    return matchgroup
    
        
def retrievedf_fromfigure(currentfig):
    """

    Args:
        currentfig: figure

    Returns: dataframe with points extracted from the figure

    """
    # retrieves records from the figure
    recs = [d for d in currentfig['data'] if 'customdata' in d.keys() and len(d['marker']['symbol']) > 0]
    rocks = [[x.split(',')[1].strip() for x in d['customdata']] for d in recs]
    mats = [d['marker']['symbol'] for d in recs]
    xs = [d['x'] for d in recs]
    ys = [d['y'] for d in recs]
    
    thisdf = pd.DataFrame(data={'MATERIAL': [], 'ROCK': [], 'x':[], 'y': []})
    for rock, mat, x, y in zip(rocks, mats, xs, ys):
        thisdf = thisdf.append(pd.DataFrame(data={'MATERIAL': mat, 'ROCK': rock, 'x': x, 'y': y}))
        
    thisdf = thisdf.replace({'circle': 'WR', 'square': 'INC', 'diamond': 'GL', 'diamond-wide': 'UNKNOWN', 'x': 'MIN'})
    
    return thisdf
    

def update_subtitle(currentfig, store, restyle, *context):
    """

    Args:
        currentfig:
        store:
        restyle:
        context:

    Returns: 

    """
    #
    # inclusion = 19
    # volcanic glass = 18
    # whole glass = 17
    #
    subtitle = ''
    context = list(context)
    
    # retrieves the data from the figure
    thisdf = retrievedf_fromfigure(currentfig)
    # extracts existing materials
    existing_materials = thisdf['MATERIAL'].unique()
        
    if store is None:
        store = context + [True if mt in existing_materials else False for mt in ['WR', 'GL', 'INC']]
     
    else:
        # if no change
        if store[0:len(context)] == context:  
            # thus restyle applies
            for idx, lbl in zip([len(context), len(context)+1, len(context)+2], [17, 18, 19]):
                if not(restyle == None):
                    if restyle[1][0] == lbl:
                        store[idx] = restyle[0]['visible'][0]
                        
        else:
            # if anything changes, reset
            store = context + [True if mt in existing_materials else False for mt in ['WR', 'GL', 'INC']]
    
    visible_materials = [['WR', 'GL', 'INC'][i] for i in [0, 1, 2] if store[i+len(context)] == True]
    if len(existing_materials) > 0:   
        thisdf = thisdf[thisdf['MATERIAL'].isin(visible_materials)]
        # extracts major rocks
        totalsamples = len(thisdf.index)
        majorrocks = [x for x in list(thisdf['ROCK'].value_counts().index[0:5]) if x != 'UNNAMED']
        majorrocksvalues = [round(100*(thisdf['ROCK'].value_counts()[r]/totalsamples), 1) for r in majorrocks]
        
        # material present
        for vm in visible_materials:
            subtitle += vm + '-'
        subtitle = subtitle[:-1] + ': '
        # string
        for mr, mrc in zip(majorrocks, majorrocksvalues):
            subtitle += mr + ' (' + str(mrc) + '%)' + ', '
        subtitle = subtitle[:-2]
    else:      
        majorrocks = []

    return store, subtitle   

    
def GEOROC_sunburst(thisdf):
    """
    """
    fig3 = make_subplots(rows=1, cols=3, specs=[[{"type": "pie"}, {"type": "pie"}, {"type": "pie"}]],
                         subplot_titles=("all", "GL", "INC"))
    
    xs = [0.2, 0.5, 0.8]
    
    for mat, coln in zip(['all', 'GL', 'INC'], [1, 2, 3]):
        if len(thisdf.index) > 0:
            dfmat = thisdf[thisdf['material'] == mat]
            
            if len(dfmat.index) > 0:
                tmpfig = update_GEOrockchart(dfmat)
                # moves the data to graph object
                # ids are needed when labels are repeated
                # formats hovertmplate
                hovertmplate = tmpfig['data'][0]['hovertemplate'].split('{label}<br>')[1]
                splt = hovertmplate.split('parent=%{parent}<br>')
                hovertmplate = splt[0] + splt[1]
                fig3.add_traces(
                    go.Sunburst(
                        ids=tmpfig['data'][0]['ids'].tolist(),
                        labels=tmpfig['data'][0]['labels'].tolist(),
                        parents=tmpfig['data'][0]['parents'].tolist(),
                        values=tmpfig['data'][0]['values'].tolist(),
                        marker=tmpfig['data'][0]['marker'],
                        customdata=tmpfig['data'][0]['customdata'],
                        hovertemplate=hovertmplate
                    ),
                    rows=1, cols=coln,
                )
                     
                fig3['layout']['annotations'][coln-1].update(text=mat+': ' + str(len(dfmat.index)) + ' volcano(es)', font = dict(size=13), 
                                                             xref='paper', yref='paper', x=xs[coln-1], y=-0.25)
                
            else:
                fig3.add_traces(
                    go.Sunburst(
                                labels=['Major Rock 1', 'Major Rock 2', 'Major Rock 3'],
                                parents=['', 'Major Rock 1', 'Major Rock 2'],
                                marker=dict(colorscale='Greys')
                               ),
                    rows=1, cols=coln,
                )
                   
        else:
            fig3.add_traces(
                go.Sunburst(
                        labels=['Major Rock 1', 'Major Rock 2', 'Major Rock 3'],
                        parents=['', 'Major Rock 1', 'Major Rock 2'],
                        marker=dict(colorscale='Greys')
                       ),
                rows=1, cols=coln,
            )
    
    return fig3
    
    
def perc_rock():
    '''
        No input because it loads data from saved files
        output: vperc is a dictionary, with volcano names as keys
    '''   
    
    # loads a list of samples per volcano
    with open("lst1TASall2023", "rb") as fp2:   
        lstTASall = pickle.load(fp2)

    # loads the corresponding volcano name list
    with open("lst1all2023", "rb") as fp1:
        lstall = pickle.load(fp1) 
        
    vperc = {}

    for l, n in zip(lstTASall, lstall):
        rcks = [x for x in l[11]]
        rckscnt = Counter(rcks) 
        rckperc = [0 for x in GEOROC_rocks]
        idx = 0
        for rt in GEOROC_rocks:
            if rt in rckscnt.keys():
                rckperc[idx] = rckscnt[rt] 
            idx += 1
        vperc[n] = rckperc     
   
    return vperc
