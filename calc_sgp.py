import csv
import numpy as np
import bisect
from subprocess import call #for calling mkdir
import pandas as pd

N_teams = 14
N_activehitters = 9
N_SP = 8
N_RP = 4
budget = 260
frac_hitter_budget = 0.5
frac_pitcher_budget = 1 - frac_hitter_budget
output_dir = "./output/dc_3_19_2017/"


def sgp_hitters(df, asgp):
    # This script calculates the sgp points hitters get in each category
    # The name of our output file
    output_filename = 'tmp/hitssgp.csv'
    #Load our projections file and populate entries in two new lists
    # df = pd.read_csv('./tmp/hits2.csv')
    # Get the SGP replacement level headers from the matlab script (Get_SGP_thresholds_from_lastyeardata.m)
    sgp = load_sgp_thresh_last_year('H')
    # Sort the data
    df = df.sort_values(by='wOBA', ascending=False)
    # Keep only the top players for calculating averages for rate categories
    top_hitters = df.head(N_activehitters * N_teams)
    # Calculate "wAVG"
    numer = (N_activehitters - 1) * top_hitters['H'].mean() + df['H']
    denom = (N_activehitters - 1) * top_hitters['AB'].mean() + df['AB']
    df['wAVG'] = numer/denom - top_hitters['AVG'].mean()
    # Calculate wOBA
    monbase = top_hitters['PA'].mean() * top_hitters['OBP'].mean()
    numer = (N_activehitters - 1) * monbase + df['H'] + df['BB'] + df['HBP']
    denom = (N_activehitters - 1) * top_hitters['PA'].mean() + df['PA']
    df['wOBP'] = numer/denom - top_hitters['OBP'].mean()
    # Calculate wSLG
    numer = (N_activehitters - 1) * top_hitters['TB'].mean() + df['TB']
    denom = (N_activehitters - 1) * top_hitters['AB'].mean() + df['AB']
    df['wSLG'] = numer/denom - top_hitters['SLG'].mean()
    #Now get the sgp by dividing by the values calculated from last year's totals
    for cat in ['AVG', 'OBP', 'SLG']:
        df['s' + cat] = df['w' + cat] / sgp[cat][0] - asgp['s' + cat][0]
    for cat in ['HR', 'R', 'RBI', 'SB', 'TB']:
        df['s' + cat] = (df[cat] - sgp[cat][1]) / sgp[cat][0] - asgp['s' + cat][0]
    #Sum up all of these entries to get the total SGP
    df['SGP'] = df[['sAVG', 'sOBP', 'sSLG', 'sHR',
                    'sR', 'sRBI', 'sSB', 'sTB']].sum(axis=1)
    #Now sort by total SGP descending
    df = df.sort_values(by='SGP', ascending=False)
    df = df.reset_index(drop=True)
    return df


def addpos(df):
    """This function writes the eligible cbssports positions to the projections file"""
    #Load jabo cbssports data for player (cbsid, name, team, salary, etc.)
    #Load csv data of player cbsid, player name, and mlb team
    cbs = pd.read_csv('./tmp/cbs_hitters.csv',
                    names=['cbs_id', 'mlb_team','jabo_team', 'Pos', 'Salary'],
                    dtype={'cbs_id':str})
    out = df.merge(cbs, left_on='cbs_id', right_on='cbs_id', how='inner')
    print('Some data in the cbs players file is NA -- removing it:')
    print(out[out.isnull().any(axis=1)][['Name', 'Team', 'jabo_team', 'Salary', 'wOBA']])
    out = out[out['Pos'].notnull()]
    # Create a dict of data frames
    meta = assign_positions_to_dataframes(udf)
    return meta

def calc_pos_scarcity(sgp_addends, meta):
    """Calculate the position offset values.
    Go through all hitters in order of SGP and assign them positions. It doesn't
    actually matter what list a player is assigned to. The point is to get
    replacement values"""

    #Initiailize each list by putting in the best hitter (will remove later)
    meta_ranked = dict()
    for m in meta:
        meta_ranked[m] = meta[m].head(1)
    for _, row in meta['U'].iterrows():
        #Get the sgp of the player in this row
        sgp = row['SGP']
        #now get the rank of the available positions
        posrank = dict()
        #Loop over all positions this player is eligible at
        #Get the SGP of all players at each eligible position
        for pos in row['Pos'].split(','):
            sgpofcolumn = meta_ranked[pos]['SGP'].get_values()
            #For each eligible position, find out how many players are better (by SGP)
            posrank[pos] = get_rank(sgpofcolumn, sgp)
        #Get which position the player would be the next best at by finding the
        # one with the least number of better players at it
        highest = min(posrank.values())
        bestposits = [k for k, v in posrank.items() if v == highest]
        #In the case of ties, go down the defensive spectrum
        defensive_spectrum = ['U', 'Uonly', '1B', 'RF', 'LF', 'CF', '3B', '2B',
                              'SS', 'C']
        #Values overwrite each other so the toughest to fill position is left at the end
        for pp in defensive_spectrum:
            if pp in bestposits:
                bestpos = pp
        #Finally add the row to the end of the correct dataframe
        meta_ranked[bestpos] = meta_ranked[bestpos].append(row, ignore_index='True')
    #Now remove the initialized value of the best hitter in each list
    for m in meta_ranked:
        meta_ranked[m] = meta_ranked[m].drop(0)
        meta_ranked[m] = meta_ranked[m].reset_index(drop=True)
    sgp = load_sgp_thresh_last_year('H')
    #also need to account for the bench hitters. assume every team carries 3.
    # then 42 extra hitters. more than 4 teams worth
    stardiff = []
    starthresh = dict()
    #We need to normalize SGP so that the total available SGP of all hitters is
    # the number of points that can be gained (i.e., for each category, there are
    # 14 teams, so there are 13 points to be gained in each for each)
    sgp_new = dict()
    for sgpcat in ['sAVG', 'sOBP', 'sSLG', 'sHR', 'sR', 'sRBI', 'sSB', 'sTB']:
        #loop over hitting categories
        star = 0
        for i in range(0, N_teams): #Loop over #teams+4
            for pos in ['U', '1B', 'RF', 'LF', 'CF', '3B', '2B','SS', 'C']: # NO UONLY
                #Load the sum of SGP for each category for the top N_teams+4
                #players at each position since this will represent the total
                # number of owned hitters
                star += meta_ranked[pos][sgpcat][i]
        #We're aiming to minimize this total in order that the sum of points of
        # all the owned players represents the correct
        #Use sum(i=1:N,i)=(N+1)N/2
        #Total SGP available: Team A can gain 13pnts, Team B can gain 12pnts, etc.
        #total number of sgp that can be gained by all teams..each category should have the same # ofthese
        #N_teams not N_teams+4
        starthresh[sgpcat] = star - N_teams*(N_teams-1)/2
        #N_teams-1    #N_teams*(N_teams-1)/2
        #This is the offset threshold that gets added on so that the total number of category points are right
        #This gets added in to the old values
        #Divide the difference by the total number of active players since all  will be contributing to the category
        sgp_new[sgpcat] = sgp_addends[sgpcat] + \
                          starthresh[sgpcat]/((N_teams)*N_activehitters)
    #Print the offsets to each SGP category
    print('Thresholds for each category. These values should be small:')
    print(starthresh)
    #Now print the rows in each file
    cnt=0
    sgp_pos_addends = dict()
    for pos in ['U', '1B', 'RF', 'LF', 'CF', '3B', '2B','SS', 'C']: #defensive_spectrum:
        sgp_pos_addends[pos] = meta_ranked[pos]['SGP'][N_teams-1]
    return sgp_new, sgp_pos_addends, meta_ranked


def get_rank(listo,sgp):
    """returns the index of the first item in a sorted list (must be descending)
     whose value is less than an input value"""
    #Get the first item in the list whose value falls under the entered one
    try:
        index = next(index for index, value in enumerate(listo) if value < sgp)
    #If we reach the end of the list use the last entry as the index
    except StopIteration:
        index = len(listo)
    #If the largest value in the list is the first one below the input value,
    # return an empty string. This is meant for the case in which the player
    # is the best at their position and accounts for players being placed at
    # U when they should really go to another list
    if index == 0:
        index = ''
    return index


def add_pos_sgp(udf, sgp_pos_addends):
    #First make the output directory if it doesn't exist
    call(["mkdir", "-p", output_dir])
    #Load the files into lists
    #Sort the dictionary (returns a list of tuples)
    sgp_pos_add_sort = sorted(sgp_pos_addends.items(),
                              key=lambda sgp_pos_addends: sgp_pos_addends[1],
                              reverse=True) # should go largest to smallest
                              # largest corresponds to best offensive poistion
    print(sgp_pos_add_sort)
    # IGNORE FIRST VALUE???
    # Initialize
    sgp_addend = [0] * len(udf)
    # Now go thru each player, add their new score and add them to the appropriate output list
    for cntrr, row in udf.iterrows():
        # Check to see if the player gets extra points -- the following go IN ORDER
        for pp in sgp_pos_add_sort:
            if pp[0] in row['Pos'].split(','):
                sgp_addend[cntrr] = pp[1]
    print(sgp_addend)
    # Create position assigned row
    udf['p_SGP'] = udf['SGP'] - sgp_addend
    # Sort dataframe by descending p_SGP
    udf = udf.sort_values(by='p_SGP', ascending=False)
    udf = udf.reset_index(drop=True)
    # Get the sum of SGP and p_SGP of the owned, starting players
    sgp_sum = udf['SGP'][:N_teams * N_activehitters].sum()
    p_sgp_sum = udf['p_SGP'][:N_teams * N_activehitters].sum()
    # Get the difference from what it should be
    sgp_diff = (N_teams*(N_teams-1)*8/2-sgp_sum)#/(N_teams*N_activehitters)  #8 hitting cats
    p_sgp_diff= (N_teams*(N_teams-1)*8/2-p_sgp_sum)#/(N_teams*N_activehitters)
    print('sgp diff (should be near zero):')
    print(sgp_diff)
    print('p_sgp diff (should be near zero):')
    print(p_sgp_diff)
    # Calculate expected salaries
    udf['xusal'] = udf['SGP'] / sgp_sum * budget * frac_hitter_budget * N_teams
    udf['xsal'] = udf['p_SGP'] / p_sgp_sum * budget * frac_hitter_budget * N_teams
    udf['dsal'] = udf['Salary'] - udf['xsal']
    # Round the dataframe
    rounding_dict = {'wAVG': 3, 'wOBP': 3, 'wSLG': 3, "sAVG": 1, "sOBP": 1,
                     "sSLG": 1, "sHR": 1, "sR": 1, "sRBI": 1, "sSB": 1,
                     "sTB": 1, 'SGP': 1, 'p_SGP': 1, 'xusal': 0, 'xpsal': 0,
                     'dsal':0}
    udf = udf.round(rounding_dict)
    # Reorder columns
    column_order = ["Name", "xusal", "xsal", "Salary", "dsal", "mlb_team", "jabo_team", "Pos",
                 "PA", "AVG", "OBP", "SLG", "HR", "SB", "sAVG", "sOBP", "sSLG",
                 "sR", "sRBI", "sTB", "sHR", "sSB", "R", "RBI", "wOBA", "WAR",
                 "playerid", "SGP", "p_SGP"]
    udf = udf[column_order]
    # Create a dict of data frames
    meta = assign_positions_to_dataframes(udf)
    # Write each to file
    for key, _ in meta.items():
        meta[key].to_csv(output_dir + key + '.csv', index=False)
    return udf

def load_sgp_thresh_last_year(players):
    """Get the SGP replacement level headers from the matlab script
    (Get_SGP_thresholds_from_lastyeardata.m)"""
    if players == 'H':
        file_tail = ''
    elif players == 'P':
        file_tail = '_P'
    else:
        raise ValueError("Players should be 'H' or 'P' ")
    header = pd.read_csv('./source_data/sgp_thresh_lastyear_header' +
                         file_tail + '.csv')
    sgp = pd.read_csv('./source_data/sgp_thresh_lastyear_values' +
                         file_tail + '.csv', names=header)
    return sgp


def assign_positions_to_dataframes(df):
    """Given an input dataframe, create a dictionary of dataframes for each
    position and assign each player to one or more of the position dataframes"""
    meta = {'RF': pd.DataFrame(columns=df.columns),
            'CF': pd.DataFrame(columns=df.columns),
            'LF': pd.DataFrame(columns=df.columns),
            '1B': pd.DataFrame(columns=df.columns),
            '2B': pd.DataFrame(columns=df.columns),
            'SS': pd.DataFrame(columns=df.columns),
            '3B': pd.DataFrame(columns=df.columns),
            'C': pd.DataFrame(columns=df.columns),
            'U': pd.DataFrame(columns=df.columns),
            'Uonly': pd.DataFrame(columns=df.columns)}
    # For each player, write a new row for each position
    for _, row in df.iterrows():
        for pos in row['Pos'].split(','):
            meta[pos] = meta[pos].append(row, ignore_index='True')
        # Handle the case when the only eligible position is utility
        if row['Pos'] == 'U':
            meta['Uonly'] = meta['Uonly'].append(row, ignore_index='True')
    return meta


def calc_sgp_SPRP(asgp, SP, RP, SPRP):
    #Get the SGP replacement level values from the matlab script
    #These are the headers
    sgp = load_sgp_thresh_last_year('P')
    #Sort the data for SP and keep the top pitchers for calculating rate cats
    SP = SP.sort_values(by='WAR', ascending=False)
    top_SP = SP.head(N_SP * N_teams)
    #sort the relievers
    RP = RP.sort_values(by='WAR', ascending=False)
    top_RP = RP.head(N_RP * N_teams)
    #Now combine the sp and rp
    print(top_SP.shape)
    print(top_RP.shape)
    top_P = pd.concat([top_SP, top_RP], axis=0)
    P = pd.concat([SP, RP], axis=0)
    #Calculate "wERA"
    numer_SP = (N_SP - 1) * top_SP['ER'].mean() + N_RP * top_RP['ER'].mean()
    denom_SP = (N_SP - 1) * top_SP['IP'].mean() + N_RP * top_RP['IP'].mean()
    numer_RP = N_SP * top_SP['ER'].mean() + (N_RP - 1) * top_RP['ER'].mean()
    denom_RP = N_SP * top_SP['IP'].mean() + (N_RP - 1) * top_RP['IP'].mean()
    mean_era = 9 * (top_SP['ER'].mean() + top_RP['ER'].mean()) / \
                   (top_SP['IP'].mean() + top_RP['IP'].mean())
    wera = []
    for _, row in P.iterrows():
        if row['GS']==0:
            val = (numer_RP + row['ER']) / (denom_RP + row['IP'])
        else:
            val = (numer_SP + row['ER']) / (denom_SP + row['IP'])
        wera.append(9 * val - mean_era)
    P['wERA'] = wera
    # Calculate "wWHIP"
    numer_SP = (N_SP - 1) * top_SP['W+H'].mean() + N_RP * top_RP['W+H'].mean()
    denom_SP = (N_SP - 1) * top_SP['IP'].mean() + N_RP * top_RP['IP'].mean()
    numer_RP = N_SP * top_SP['W+H'].mean() + (N_RP - 1) * top_RP['W+H'].mean()
    denom_RP = N_SP * top_SP['IP'].mean() + (N_RP - 1) * top_RP['IP'].mean()
    mean_whip = (top_SP['W+H'].mean() + top_RP['W+H'].mean()) / \
                (top_SP['IP'].mean() + top_RP['IP'].mean())
    wwhip = []
    for _, row in P.iterrows():
        if row['GS']==0:
            val = (numer_RP + row['W+H']) / (denom_RP + row['IP'])
        else:
            val = (numer_SP + row['W+H']) / (denom_SP + row['IP'])
        wwhip.append(val - mean_whip)
    P['wWHIP'] = wwhip
    # Calculate "wIP/GS"
    numer = (N_SP - 1) * top_SP['IP'].mean()
    denom = (N_SP - 1) * top_SP['GS'].mean()
    mean_ipgs = numer / denom
    P['wIP/GS'] = (numer + P['IP']) / (denom + P['GS']) - mean_ipgs
    P.loc[P['GNS']>0, 'wIP/GS'] = 0
    # Calculate "wSO/BB"
    numer_SP = (N_SP - 1) * top_SP['SO'].mean() + N_RP * top_RP['SO'].mean()
    denom_SP = (N_SP - 1) * top_SP['BB'].mean() + N_RP * top_RP['BB'].mean()
    numer_RP = N_SP * top_SP['SO'].mean() + (N_RP - 1) * top_RP['SO'].mean()
    denom_RP = N_SP * top_SP['BB'].mean() + (N_RP - 1) * top_RP['BB'].mean()
    mean_sobb = (top_SP['SO'].mean() + top_RP['SO'].mean()) / \
                (top_SP['BB'].mean() + top_RP['BB'].mean())
    wsobb = []
    for _, row in P.iterrows():
        if row['GS']==0:
            val = (numer_RP + row['SO']) / (denom_RP + row['BB'])
        else:
            val = (numer_SP + row['SO']) / (denom_SP + row['BB'])
        wsobb.append(val - mean_sobb)
    P['wSO/BB'] = wsobb
    #Now get the sgp by dividing by the values calculated from last year's totals
    for cat in ['ERA', 'WHIP', 'IP/GS', 'SO/BB']:
        P['s' + cat] = P['w' + cat] / sgp[cat][0] - asgp['s' + cat][0]
    for cat in ['SO', 'W', 'SV', 'HLD']:
        P['s' + cat] = (P[cat] - sgp[cat][1]) / sgp[cat][0] - asgp['s' + cat][0]
    P.loc[P['GNS']>0, 'sIP/GS'] = 0
    P.loc[P['GNS']==0, 'sSV'] = 0
    P.loc[P['GNS']==0, 'sHLD'] = 0
    #Sum up all of these entries to get the total SGP
    P['SGP'] = P[['sERA', 'sWHIP', 'sIP/GS', 'sSO/BB',
                    'sSO', 'sW', 'sSV', 'sHLD']].sum(axis=1)
    #Now sort by total SGP descending
    P = P.sort_values(by='SGP', ascending=False)
    P = P.reset_index(drop=True)
    return P
