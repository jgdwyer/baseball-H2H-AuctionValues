import csv
import pandas as pd
import numpy as np

masterid_file = './source_data/ids.csv'

def load_hitters_fangraphs():
    return pd.read_csv('./source_data/proj_dc_hitters.csv')

def add_hitter_cats(df):
    df['1B'] = df['H'] - (df['2B'] + df['3B'] + df['HR'])
    df['TB'] = df['1B']*1 + df['2B']*2 + df['3B']*3 + df['HR']*4
    return df

def add_hitter_ids_manually(df):
    fg_to_cbs = dict()
    fg_to_cbs['3711'] = '1741019'
    fg_to_cbs['sa737507'] = '2066300'
    for fgid, cbsid in fg_to_cbs.items():
        df.loc[df.playerid==fgid, 'cbs_id'] = cbsid
    return df

def prepHitters():
    df = load_hitters_fangraphs()
    df = add_hitter_cats(df)
    df = add_cbs_id(df)
    df = add_hitter_ids_manually(df)
    df = print_missing_and_remove_nulls(df)
    return df

def add_pitchers():
    df = pd.read_csv('./source_data/proj_dc_pitchers.csv')
    df['GNS'] = df['G'] - df['GS']  # Games not started
    df['SO/BB'] = df['SO'].astype('float') / df['BB'].astype('float')
    df['IP/GS'] = df['IP'].astype('float') / df['GS'].astype('float')
    df.loc[df['GNS']>0, 'IP/GS'] = 0
    # Handle division by zero case
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df['SO/BB'].fillna(0, inplace=True)
    df['IP/GS'].fillna(0, inplace=True)
    df['W+H'] = df['BB'] + df['H']
    # Load the id's
    out = add_cbs_id(df)
    #Manually add cbs ids for certain players
    out.loc[out.playerid=='sa658473', 'cbs_id'] ='2044482'
    out.loc[out.playerid=='sa621465', 'cbs_id'] = '2138864'
    out.loc[out.playerid=='sa597893', 'cbs_id'] = '2449977'
    out = print_missing_and_remove_nulls(out)
    return out

def add_cbs_id(df):
    idkey = pd.read_csv('./source_data/ids.csv', dtype={'cbs_id': str})
    # Merge dataframes (SQL-style)
    out = df.merge(idkey[['fg_id', 'cbs_id']], left_on='playerid',
                 right_on='fg_id', how='left')
    return out

def addcbs_info(df, players):
    """This function writes the eligible cbssports positions to the projections file"""
    #Load jabo cbssports data for player (cbsid, name, team, salary, etc.)
    #Load csv data of player cbsid, player name, and mlb team
    cbs = pd.read_csv('./source_data/cbs_' + players + '.csv',
                    names=['cbs_id', 'mlb_team','jabo_team', 'Pos', 'Salary'],
                    dtype={'cbs_id':str})
    out = df.merge(cbs, left_on='cbs_id', right_on='cbs_id', how='inner')
    print('Some data in the cbs players file is NA -- removing it:')
    print(out[out.isnull().any(axis=1)][['Name', 'Team', 'jabo_team', 'Salary', 'WAR']])
    out = out[out['Pos'].notnull()]
    return out

def print_missing_and_remove_nulls(out):
    # Show the best missing hitters that our id file doesn't have
    print("Best players without id's. Manually add these guys in:")
    print(out[out['cbs_id'].isnull()][['Name', 'Team','WAR','playerid']].\
        sort_values('WAR')[::-1][:10])
    # Remove rows that are null in fangraph ids
    out = out[out['cbs_id'].notnull()]
    return out

def separate_SP_RP(df):
    SP = pd.DataFrame(columns=df.columns)
    RP = pd.DataFrame(columns=df.columns)
    SPRP = pd.DataFrame(columns=df.columns)
    print('The following pitchers are not projected to pitch in 2017:')
    for _, row in df.iterrows():
        if (row['GS'] > 0) and (row['GNS'] == 0):
            SP = SP.append(row, ignore_index='True')
        elif (row['GS'] == 0) and (row['GNS'] > 0):
            RP = RP.append(row, ignore_index='True')
        elif (row['GS'] == 0) and (row['GNS']== 0):
            print(row)
        else:
            SPRP = SPRP.append(row, ignore_index='True')
    return SP, RP, SPRP
