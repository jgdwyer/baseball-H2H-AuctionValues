import pandas as pd
import numpy as np

N_teams = 14
N_hitters = 9
N_SP = 8
N_RP = 4
budget = 260
frac_hitter_budget = 0.5
frac_pitcher_budget = 1 - frac_hitter_budget


def calcSGPHitters(df, cat_offsets):
    """Calculates SGP values for hitters"""
    # Get the SGP replacement level headers from the matlab script (Get_SGP_thresholds_from_lastyeardata.m)
    sgp = load_sgp_thresh_last_year('H')
    # Sort the data
    df = df.sort_values(by='wOBA', ascending=False)
    # Keep only the top players for calculating averages for rate categories
    top_hitters = df.head(N_hitters * N_teams)
    # Calculate "wAVG"
    numer = (N_hitters - 1) * top_hitters['H'].mean() + df['H']
    denom = (N_hitters - 1) * top_hitters['AB'].mean() + df['AB']
    df['wAVG'] = numer/denom - top_hitters['AVG'].mean()
    # Calculate wOBA
    monbase = top_hitters['PA'].mean() * top_hitters['OBP'].mean()
    numer = (N_hitters - 1) * monbase + df['H'] + df['BB'] + df['HBP']
    denom = (N_hitters - 1) * top_hitters['PA'].mean() + df['PA']
    df['wOBP'] = numer/denom - top_hitters['OBP'].mean()
    # Calculate wSLG
    numer = (N_hitters - 1) * top_hitters['TB'].mean() + df['TB']
    denom = (N_hitters - 1) * top_hitters['AB'].mean() + df['AB']
    df['wSLG'] = numer/denom - top_hitters['SLG'].mean()
    # Now get the sgp by dividing by the values calculated from last year's totals
    for cat in ['AVG', 'OBP', 'SLG']:
        df['s' + cat] = df['w' + cat] / sgp[cat][0] - cat_offsets['s' + cat][0]
    for cat in ['HR', 'R', 'RBI', 'SB', 'TB']:
        df['s' + cat] = (df[cat] - sgp[cat][1]) / sgp[cat][0] - cat_offsets['s' + cat][0]
    # Sum up all of these entries to get the total SGP
    df['SGP'] = df[['sAVG', 'sOBP', 'sSLG', 'sHR',
                    'sR', 'sRBI', 'sSB', 'sTB']].sum(axis=1)
    # Now sort by total SGP descending
    df = df.sort_values(by='SGP', ascending=False)
    return df.reset_index(drop=True)


def calcPositionOffsets(cat_offsets, df):
    """Calculate the position offset values.
    Go through all hitters in order of SGP and assign them positions. It doesn't
    actually matter what list a player is assigned to. The point is to get
    replacement values"""
    # Initiailize each list by putting in the best hitter (will remove later)
    defensive_spectrum = {'C': 0, 'SS': 1, '2B': 2, '3B': 3, 'CF': 4, 'LF': 5, 'RF': 6, '1B': 7, 'U': 8}
    positions = list(defensive_spectrum.keys())
    meta_ranked = {m: pd.DataFrame(columns=df.columns) for m in positions}
    for _, row in df.iterrows():
        # Loop over all positions this player is eligible at
        # Get the SGP of all players at each eligible position
        posrank = pd.Series(index=positions)
        for pos in row['position'].split(','):
            posrank[pos] = len(meta_ranked[pos])  # how many better players are already assigned to that position
        bestposits = list(posrank[posrank == posrank.min()].index)
        # In the case of ties, go down the defensive spectrum - sort is ascending so lower values are better
        bestpos = sorted(bestposits, key=lambda x: defensive_spectrum[x])[0]  # custom sorting
        # Finally add the row to the end of the correct dataframe
        meta_ranked[bestpos] = meta_ranked[bestpos].append(row, ignore_index='True')
    # TODO: Account for bench hitters?
    cat_offsets = update_category_offsets(cat_offsets, meta_ranked, positions)
    # Get the positional difference by looking at the value of the last player
    # TODO: These don't seem to be normalized correctly
    pos_offsets = pd.Series({pos: meta_ranked[pos]['SGP'][N_teams-1] for pos in positions})
    return cat_offsets, pos_offsets


def update_category_offsets(cat_offsets, meta_ranked, positions):
    """

    :param cat_offsets: Previous value
    :param meta_ranked: dictionary of dataframes
    :param positions: list of str
    :return: Updated value of cat_offsets
    """
    sgp_per_category = N_teams * (N_teams - 1) / 2
    sgp_difference_per_cat = dict()
    for cat in ['sAVG', 'sOBP', 'sSLG', 'sHR', 'sR', 'sRBI', 'sSB', 'sTB']:
        sgp_assigned = sum([meta_ranked[pos][cat][:N_teams].sum() for pos in positions])
        sgp_difference_per_cat[cat] = sgp_assigned - sgp_per_category
        # Divide the difference by the total number of active players since this is a per-player metric
        cat_offsets[cat] += sgp_difference_per_cat[cat] / (N_teams * N_hitters)
    print('Updated offsets for each category. Should get progressively smaller: {}'.format(sgp_difference_per_cat))
    return cat_offsets


def addPositions(udf, pos_offsets):
    pos_offsets = pos_offsets.sort_values()
    # Initialize
    pos_offset_values = pd.Series(index=udf.index)
    # Now go thru each player, add their new score and add them to the appropriate output list
    for cntrr, row in udf.iterrows():
        # Check to see if the player gets extra points -- the following go IN ORDER
        player_positions = row['position'].split(',')
        most_valuable_position = sorted(player_positions, key=lambda x: pos_offsets[x])[0]
        pos_offset_values[cntrr] = pos_offsets[most_valuable_position]
    # Create position assigned row
    udf['p_SGP'] = udf['SGP'] - pos_offset_values
    # Sort dataframe by descending p_SGP
    udf = udf.sort_values(by='p_SGP', ascending=False)
    udf = udf.reset_index(drop=True)
    # Get the sum of SGP and p_SGP of the owned, starting players
    sgp_sum = udf['SGP'][:N_teams * N_hitters].sum()
    p_sgp_sum = udf['p_SGP'][:N_teams * N_hitters].sum()
    # Get the difference from what it should be
    sgp_diff = (N_teams*(N_teams-1)*8/2-sgp_sum)  # /(N_teams*N_hitters)  #8 hitting cats
    p_sgp_diff = (N_teams*(N_teams-1)*8/2-p_sgp_sum)  # /(N_teams*N_hitters)
    print('sgp diff (should be near zero):{:.1f}'.format(sgp_diff))
    print('p_sgp diff (should be near zero):{:.1f}'.format(p_sgp_diff))
    # Calculate expected salaries
    udf['xusal'] = udf['SGP'] / sgp_sum * budget * frac_hitter_budget * N_teams
    udf['xsal'] = udf['p_SGP'] / p_sgp_sum * budget * frac_hitter_budget * N_teams
    udf['dsal'] = udf['salary'] - udf['xsal']
    # Round the dataframe
    rounding_dict = {'wAVG': 3, 'wOBP': 3, 'wSLG': 3, "sAVG": 1, "sOBP": 1,
                     "sSLG": 1, "sHR": 1, "sR": 1, "sRBI": 1, "sSB": 1,
                     "sTB": 1, 'SGP': 1, 'p_SGP': 1, 'xusal': 0, 'xsal': 0,
                     'dsal':0}
    udf = udf.round(rounding_dict)
    # Reorder columns
    column_order = ["Name", "xusal", "xsal", "salary", "dsal", "mlb_team", "jabo_team", "position",
                 "PA", "AVG", "OBP", "SLG", "HR", "SB", "sAVG", "sOBP", "sSLG",
                 "sR", "sRBI", "sTB", "sHR", "sSB", "R", "RBI", "wOBA", "WAR",
                 "playerid", "SGP", "p_SGP"]
    udf = udf[column_order]
    # Create a dict of data frames
    meta = assign_positions_to_dataframes(udf)
    # Write each to file
    for key, _ in meta.items():
        meta[key].to_csv('./output/' + key + '.csv', index=False)
    return udf, meta


def load_sgp_thresh_last_year(players):
    """Get the SGP replacement level headers from the matlab script
    (Get_SGP_thresholds_from_lastyeardata.m)"""
    return pd.read_csv('./source_data/sgp_thresh_lastyear_values_' + players + '.csv')


def assign_positions_to_dataframes(df):
    """Given an input dataframe, create a dictionary of dataframes for each
    position and assign each player to one or more of the position dataframes"""
    meta = {pos: pd.DataFrame(columns=df.columns) for pos in ['RF', 'CF', 'LF', '1B', '2B', 'SS', '3B', 'C', 'U',
                                                              'Uonly']}
    # For each player, write a new row for each position
    for _, row in df.iterrows():
        for pos in row['position'].split(','):
            meta[pos] = meta[pos].append(row, ignore_index='True')
        # Handle the case when the only eligible position is utility
        if row['position'] == 'U':
            meta['Uonly'] = meta['Uonly'].append(row, ignore_index='True')
    return meta


def calcSGPPitchers(cat_offsets, SP, RP):
    # Get the SGP replacement level values from the matlab script
    # These are the headers
    sgp = load_sgp_thresh_last_year('P')
    # Sort the data for SP and keep the top pitchers for calculating rate cats
    SP = SP.sort_values(by='WAR', ascending=False)
    top_SP = SP.head(N_SP * N_teams)
    # sort the relievers
    RP = RP.sort_values(by='WAR', ascending=False)
    top_RP = RP.head(N_RP * N_teams)
    # Now combine the sp and rp
    top_P = pd.concat([top_SP, top_RP], axis=0)
    P = pd.concat([SP, RP], axis=0)
    # Calculate "wERA"
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
    # Calculate "wSO/BB"
    numer_SP = (N_SP - 1) * top_SP['SO'].mean() + N_RP * top_RP['SO'].mean()
    denom_SP = (N_SP - 1) * top_SP['BB'].mean() + N_RP * top_RP['BB'].mean()
    numer_RP = N_SP * top_SP['SO'].mean() + (N_RP - 1) * top_RP['SO'].mean()
    denom_RP = N_SP * top_SP['BB'].mean() + (N_RP - 1) * top_RP['BB'].mean()
    mean_sobb = (top_SP['SO'].mean() + top_RP['SO'].mean()) / \
                (top_SP['BB'].mean() + top_RP['BB'].mean())
    wsobb = []
    for _, row in P.iterrows():
        if row['GS'] == 0:
            val = (numer_RP + row['SO']) / (denom_RP + row['BB'])
        else:
            val = (numer_SP + row['SO']) / (denom_SP + row['BB'])
        wsobb.append(val - mean_sobb)
    P['wSO/BB'] = wsobb
    # Now get the sgp by dividing by the values calculated from last year's totals
    for cat in ['ERA', 'WHIP', 'SO/BB']:
        P['s' + cat] = P['w' + cat] / sgp[cat][0] - cat_offsets['s' + cat][0]
    for cat in ['SO', 'W', 'SV', 'HLD', 'IP']:
        P['s' + cat] = (P[cat] - sgp[cat][1]) / sgp[cat][0] - cat_offsets['s' + cat][0]
    P.loc[P['GNS'] == 0, 'sSV'] = 0
    P.loc[P['GNS'] == 0, 'sHLD'] = 0
    # Sum up all of these entries to get the total SGP
    P['SGP'] = P[['sERA', 'sWHIP', 'sIP', 'sSO/BB',
                  'sSO', 'sW', 'sSV', 'sHLD']].sum(axis=1)
    # Now sort by total SGP descending
    P = P.sort_values(by='SGP', ascending=False)
    P = P.reset_index(drop=True)
    SP = P[P['GS']>0].reset_index(drop=True)
    RP = P[P['GS']==0].reset_index(drop=True)
    return SP, RP, P


def normSGPPitchers(cat_offsets, SP, RP):
    sgp_thresh = dict()
    # Loop over each category
    N_topSP = N_teams * N_SP
    N_topRP = N_teams * N_RP
    # for k in range(0, 8):
    for cat in ["sERA", "sWHIP", "sIP", "sSO/BB", "sSO", "sW", "sHLD", "sSV"]:
        star = SP[cat][:N_topSP].sum() + RP[cat][:N_topRP].sum()
        sgp_thresh[cat] = star - N_teams*(N_teams - 1)/2
        cat_offsets[cat] += sgp_thresh[cat] / (N_teams * (N_SP + N_RP))
    return cat_offsets, sgp_thresh


def reorder_cols(P):
    # Write the output header file
    column_order = ["Name", "xsal", "salary", "dsal", "mlb_team", "jabo_team", "IP", "ERA",
                    "K/9", "BB/9", "SV", "HLD", "sERA", "sWHIP", "sIP", "sSO/BB",
                    "sSO", "sW", "sSV", "sHLD", "SO/BB", "SGP", "playerid", 'GS']
    # Get an estimate for the expected salary
    N_topP = N_teams * (N_SP + N_RP) + 1
    sgp_sum = P['SGP'][:N_topP].sum()
    sgp_sum_diff = sgp_sum - N_teams*(N_teams - 1)/2*8
    print('The total SGP should be close to 0: {:.1f}'.format(sgp_sum_diff))
    # Calculate expected salary
    P['xsal'] = P['SGP'] / sgp_sum * budget * frac_pitcher_budget * N_teams
    P['dsal'] = P['salary'] - P['xsal']
    # Round output columns
    rounding_dict = {'SO/BB': 1, "IP": 1, "sERA": 1, "sWHIP": 1, "sIP": 1,
                     "sSO/BB": 1, "sSO": 1, "sW": 1, "sSV": 1, 'sHLD': 1,
                     'SGP': 1, 'xsal': 0, 'dsal': 0}
    P = P.round(rounding_dict)
    # Set column order
    P = P[column_order]
    SP = P[P['GS'] > 0].reset_index(drop=True)
    RP = P[P['GS'] == 0].reset_index(drop=True)
    return P, SP, RP
