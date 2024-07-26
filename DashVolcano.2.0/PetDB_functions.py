from config_variables import *
from GVP_functions import *
from Georoc_functions import with_FEOnorm, guess_rock
from collections import Counter
import statistics
import ast
import math

# **********************************************************************************#
#
# This contains functions to manipulate Georoc data.
# --------------------------------------------------
# * load_PetDB
# * createPetDBaroundGVP
# * PetDB_majorrocks: computes/loads rock data from PetDB
#
# Author: F. Oggier
# Last update: 25 April 2024
# **********************************************************************************#


def load_PetDB(volcano):
    """
    """
    
    dfn = pd.read_csv('../GeorocDataset/PetDBaroundGVP.csv')
    dfn['Volcano Name'] = dfn['Volcano Name'].apply(lambda x: list(set(ast.literal_eval(x)))[0].split(';'))
    dfn = dfn[dfn['Volcano Name'].apply(lambda x: True if len(np.intersect1d(x, [volcano])) > 0 else False)]
    # groupby was done by latitude and longitude, so enough to retrieve latitude on longitude
    files = ["../PetDB/earthchem_download_29458.xlsx", "../PetDB/earthchem_download_56807.xlsx"]

    pdbloaded = pd.DataFrame()

    for fn in files:
        # read file
        pdtmp = pd.read_excel(fn)
        # finds the row containing the column names, and removes the rows before
        pdtmp = pdtmp[np.where(pdtmp.iloc[:, 0] == 'SAMPLE ID')[0][0]:]
        # uses the first row as column names and then removes it
        pdtmp.columns = list(pdtmp[0:1].values[0])
        pdtmp = pdtmp.drop(pdtmp.index[[0]])
        # removes duplicated columns and keep the first instance
        pdtmp = pdtmp.loc[:, ~pdtmp.T.duplicated(keep='first')]
        # cleans columns
        oxides_pdb = [x for x in list(pdtmp) if str(x)+'(WT%)' in oxides]
        colpdb = {'ANALYZED MATERIAL': 'MATERIAL'}
        for c in oxides_pdb:
            colpdb[c] = c+'(WT%)'
        pdtmp = pdtmp.rename(columns=colpdb)
        
        # retrieves samples with the right latitudes and longitudes
        pdtmp = pdtmp[(pdtmp['LATITUDE'].isin(dfn['LATITUDE'])) & (pdtmp['LONGITUDE'].isin(dfn['LONGITUDE']))]
        pdbloaded = pdbloaded.append(pdtmp)
        
        # cleans material names
        pdbloaded = pdbloaded.replace({'WHOLE ROCK': 'WR', 'GLASS': 'GL', 'INCLUSION': 'INC'})
        
        # cleans inequalities
        for c in ['LOI(WT%)', 'NA2O(WT%)']:
            pdbloaded[c] = pdbloaded[c].apply(lambda x: float(x.split('<')[1].strip())-0.01 if type(x) == str else x)
        
        # Feo normalization
        pdbloaded = with_FEOnorm(pdbloaded)
        # Add rock names
        pdbloaded = guess_rock(pdbloaded)
    
    return pdbloaded


def createPetDBaroundGVP():
    """

    Args:

    Returns: recreates the file PetDBaroundGVP.csv and returns its content as df

    """   
    
    files = ["../PetDB/earthchem_download_29458.xlsx", "../PetDB/earthchem_download_56807.xlsx"]

    pdb = pd.DataFrame()

    for fn in files:
        # read file
        pdtmp = pd.read_excel(fn)
        # finds the row containing the column names, and removes the rows before
        pdtmp = pdtmp[np.where(pdtmp.iloc[:, 0] == 'SAMPLE ID')[0][0]:]
        # uses the first row as column names and then removes it
        pdtmp.columns = list(pdtmp[0:1].values[0])
        pdtmp = pdtmp.drop(pdtmp.index[[0]])
        # removes duplicated columns and keep the first instance
        pdtmp = pdtmp.loc[:, ~pdtmp.T.duplicated(keep='first')]
        pdb = pdb.append(pdtmp)
    
    # transforms PetDB names into GEOROC names
    oxides_pdb = [x for x in list(pdb) if str(x)+'(WT%)' in oxides]
    colpdb = {'ANALYZED MATERIAL': 'MATERIAL'}
    for c in oxides_pdb:
        colpdb[c] = c+'(WT%)'

    pdb = pdb.rename(columns=colpdb)
    
    # matches with GVP
    pi = math.pi

    # kms apart
    dist = 50

    # Radians = Degrees * PI / 180
    pdb_lat = pdb['LATITUDE']
    pdb_long = pdb['LONGITUDE']
    pdb_lat_rad = pdb['LATITUDE'].astype('float')*pi/180
    pdb_long_rad = pdb['LONGITUDE'].astype('float')*pi/180
    # keep only columns of interest
    pdb = pdb[['LATITUDE', 'LONGITUDE', 'MATERIAL', 'SAMPLE ID']+oxides]

    dfgeo = pd.DataFrame()

    for ltr, lgr, lt, lg in zip(pdb_lat_rad, pdb_long_rad, pdb_lat, pdb_long):
        gvp_lat = dfv['Latitude'].astype('float')*pi/180
        gvp_long = dfv['Longitude'].astype('float')*pi/180
        # acos(sin(lat1)*sin(lat2)+cos(lat1)*cos(lat2)*cos(lon2-lon1))*6371
        a1 = np.sin(ltr)*np.sin(gvp_lat)
        a2 = np.cos(ltr)*np.cos(gvp_lat)
        a3 = np.cos(gvp_long-lgr)
        d = 6371*np.arccos(a1+a2*a3)
    
        dffromgvp = dfv[d <= dist][['Volcano Name', 'Latitude', 'Longitude']]
        if len(dffromgvp.index) > 0:
            # checks for more than one volcano
            if len(dffromgvp.index) > 1:    
                nov = len(dffromgvp.index)
                shorterdist = dist-1
                while nov > 1:
                    dffromgvp = dfv[d <= shorterdist][['Volcano Name', 'Latitude', 'Longitude']]
                    if len(dffromgvp.index) == 1 or shorterdist == 5:
                        # if shorterdist == 5 and len(dffromgvp.index) > 1 :
                        # closev.append(list(dffromgvp['Volcano Name'].values))
                        nov = 1
                    else:
                        shorterdist = shorterdist-1
            # keep chemicals
            subpdb = pdb[(pdb['LATITUDE'] == lt) & (pdb['LONGITUDE'] == lg)]
            subpdb['Volcano Name'] = [';'.join(list(dffromgvp['Volcano Name']))]*len(subpdb)
            dfgeo = dfgeo.append(subpdb)
            dfgeo = dfgeo.drop_duplicates()
            
    # cleans the data
    dfgeo = dfgeo.fillna(0)
    dfgeo['LOI(WT%)'] = dfgeo['LOI(WT%)'].apply(lambda x: float(x.split('<')[1].strip())-0.01 if type(x) == str else x)
    dfgeo['NA2O(WT%)'] = dfgeo['NA2O(WT%)'].apply(lambda x: float(x.split('<')[1].strip())-0.01 if type(x) == str else x)
    
    # Feo normalization
    dfgeo = with_FEOnorm(dfgeo)
    # Add rock names
    dfgeo = guess_rock(dfgeo)
    # rock names excluding inclusions
    dfgeo['ROCK no inc'] = dfgeo['ROCK']
    dfgeo.loc[dfgeo['MATERIAL'] == 'INCLUSION', 'ROCK no inc'] = ''
    # Keeps only the necessary
    dfgeo = dfgeo[['LATITUDE', 'LONGITUDE', 'MATERIAL', 'SAMPLE ID', 'SIO2(WT%)', 'NA2O(WT%)', 'K2O(WT%)', 'CAO(WT%)','FEOT(WT%)','MGO(WT%)', 'ROCK', 'ROCK no inc', 'Volcano Name']]
    
    # group sample names when same location
    matchgroup = dfgeo.groupby(['LATITUDE', 'LONGITUDE']).agg(lambda x: list(x))
    matchgroup['SAMPLE ID'] = matchgroup['SAMPLE ID'].apply(lambda x: x if len(x) <= 3 else list(set(x[0:3]))+['+'+str(len(x)-3)])
    # this creates a single string out of different sample names attached to one location
    matchgroup['SAMPLE ID'] = matchgroup['SAMPLE ID'].apply(lambda x: " ".join([str(y) for y in x]))
    # 
    matchgroup['ROCK'] = matchgroup['ROCK'].apply(lambda x: list(Counter(x).items()))
    matchgroup['ROCK no inc'] = matchgroup['ROCK no inc'].apply(lambda x: list(Counter(x).items()))
    
    for c in chemicals_settings[0:1]:
        matchgroup[c+'mean'] = matchgroup[c].apply(lambda x: statistics.mean(x))
    
    matchgroup.to_csv('../GeorocDataset/PetDBaroundGVP.csv')

    return matchgroup 


def PetDB_majorrocks(tect_setting): 
    """

    Args:
        tect_setting: 

    Returns: a dataframe with volcano names and their PetDB major rocks 1,2 and 3.

    """
    tect_setting = [x for x in tect_setting if x != None and x != ' all GEOROC']
    
    # PetDB
    if ' PetDB' in tect_setting and len(tect_setting) == 1:
        # format tectonic setting names
        tect_GEOROC = [x.strip().replace(' ', '_').replace('/',',') for x in new_tectonic_settings]
    else: 
        tect_GEOROC = [x.strip().replace(' ', '_').replace('/',',') for x in tect_setting if (x != ' PetDB') and (x != ' all GEOROC')]
        
    alldf = pd.DataFrame()
        
    # check if file exists
    for ts in tect_GEOROC:
        # lists files in the folder
        if 'PetDB'+ ts +'.txt' in os.listdir('../PetDB'):
            # file exists, just reads it
            thisdf = pd.read_csv('../PetDB/'+ 'PetDB' + ts +'.txt')
        else:
            # file needs to be created    
            # PetDB volcanoes    
            dicPetDB = pd.read_csv('../GeorocDataset/PetDBaroundGVP.csv')['Volcano Name']
            dicPetDB = pd.read_csv('../GeorocDataset/PetDBaroundGVP.csv')['Volcano Name']
            dicPetDB = dicPetDB.apply(lambda x: set(ast.literal_eval(x)))
            dicPetDB = [list(x)[0].split(';') for x in list(dicPetDB)]
            dicPetDB = list(set([item for sublist in dicPetDB for item in sublist]))
            
            tect_cases = new_tectonic_dict[ts.replace('_', ' ').replace(',','/')].split('+')
          
            if len(tect_cases) < 3: 
                cond = dfv['Tectonic Settings'].isin(tect_cases)
            elif len(tect_cases) == 3:
                cond1 = dfv['Tectonic Settings'] == tect_cases[0]
                cond2 = dfv['Tectonic Settings'] == tect_cases[2].split(';')[0]
                cond3 = dfv['Subregion'].isin(tect_cases[2].split(';')[1:])
                cond = cond1 | ((cond2) & (cond3))
            else:
                cond1 = (dfv['Tectonic Settings'] == tect_cases[0]) | (dfv['Tectonic Settings'] == tect_cases[1])
                cond2 = dfv['Tectonic Settings'] == tect_cases[3].split(';')[0]
                cond3 = dfv['Subregion'].isin(tect_cases[3].split(';')[1:])
                cond = cond1 | ((cond2) & (cond3))
            volcanoesbyts = dfv[cond]['Volcano Name'].unique()
            # make sure there is a matching GEOROC volcano
            volcanoesbyts = [v for v in volcanoesbyts if v in dicPetDB]
    
            all_majorrocks = []
            
            for thisvolcano in volcanoesbyts:
                # loads
                thisdf = load_PetDB(thisvolcano)
                
                for mat in ['WR', 'GL', 'INC']:
                    thisdftmp = thisdf[thisdf['MATERIAL'].str.contains(mat)]
                    
                    totalsamples = len(thisdftmp.index)    
                    # removes UNNAMED, if present
                    allrocks = [x for x in list(thisdftmp['ROCK'].value_counts().index[0:]) if x != 'UNNAMED']
                    # computes percentage
                    allrocksvalues = [thisdftmp['ROCK'].value_counts()[r] for r in allrocks]
                    allrocksvaluesperc = [round(100*(thisdftmp['ROCK'].value_counts()[r]/totalsamples), 1) for r in allrocks]
                    #
                    majorrocks = []
                    cnts = []
                    # >= 10% to qualify as major rock
                    for r, rv, cnt in zip(allrocks, allrocksvaluesperc, allrocksvalues):
                        if rv >= 10:
                            majorrocks += [r]
                            cnts += [cnt]
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
                    
            thisdf = pd.DataFrame(all_majorrocks, columns=['Volcano Name','material', 'PetDB Major Rock 1', 'PetDB Major Rock 2','PetDB Major Rock 3', 'PetDB Major Rock 4', 'PetDB Major Rock 5', 'cnt 1', 'cnt 2', 'cnt 3', 'cnt 4', 'cnt 5'])
            for col in ['PetDB Major Rock 1', 'PetDB Major Rock 2','PetDB Major Rock 3', 'PetDB Major Rock 4', 'PetDB Major Rock 5']:
                newcol = col.split('PetDB ')[1]
                thisdf[newcol] = thisdf[col].replace(GEOROC_rocks,GEOROC_rock_col)
                
            thisdf.to_csv( '../PetDB/' + 'PetDB' + str(ts)+'.txt')
        alldf = alldf.append(thisdf)     

    return alldf
