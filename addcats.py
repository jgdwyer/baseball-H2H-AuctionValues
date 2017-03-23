import csv
import pandas as pd
import numpy as np

masterid_file = './source_data/ids.csv'


def add_hitters():
    # Load hitter projection file and write new columns
    df = pd.read_csv('./source_data/proj_dc_hitters.csv')
    df['1B'] = df['H'] - (df['2B'] + df['3B'] + df['HR'])
    df['TB'] = df['1B']*1 + df['2B']*2 + df['3B']*3 + df['HR']*4
    # Load the id's
    out = add_cbs_id(df)
    #Manually add cbs ids for certain players
    out.loc[out.playerid=='3711', 'cbs_id'] ='1741019'
    out.loc[out.playerid=='sa737507', 'cbs_id'] = '2066300'
    # Show the best missing hitters that our id file doesn't have
    out = print_missing_and_remove_nulls(out)
    return out

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
