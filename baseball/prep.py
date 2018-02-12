import csv

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup


def run(players):
    cbs_df = parse_cbs_files(players)
    df = load_fangraphs(players)
    df = add_cats(df, players)
    df = add_cbs_id(df)
    df = add_ids_manually(df, players)
    df = print_missing_and_remove_nulls(df)
    df = addcbs_info(df, cbs_df, players)
    return df


def load_fangraphs(players):
    return pd.read_csv('./source_data/proj_dc_' + players + '.csv')


def add_ids_manually(df, players):
    fg_to_cbs = dict()
    if players == 'hitters':
        fg_to_cbs['sa877503'] = '2211777'  # acuna
        fg_to_cbs['19755'] = '2901324'  # ohtani
    elif players == 'pitchers':
        fg_to_cbs['sa658473'] = '2044482'
        fg_to_cbs['sa621465'] = '2138864'
        fg_to_cbs['sa597893'] = '2449977'
    else:
        raise ValueError('Incorrect player string')
    for fgid, cbsid in fg_to_cbs.items():
        df.loc[df.playerid == fgid, 'cbs_id'] = cbsid
    return df


def add_cats(df, players):
    if players == 'hitters':
        df['1B'] = df['H'] - (df['2B'] + df['3B'] + df['HR'])
        df['TB'] = df['1B']*1 + df['2B']*2 + df['3B']*3 + df['HR']*4
    elif players == 'pitchers':
        df['GNS'] = df['G'] - df['GS']  # Games not started
        df['SO/BB'] = df['SO'].astype('float') / df['BB'].astype('float')
        df['IP/GS'] = df['IP'].astype('float') / df['GS'].astype('float')
        df.loc[df['GNS']>0, 'IP/GS'] = 0
        # Handle division by zero case
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df['SO/BB'].fillna(0, inplace=True)
        df['IP/GS'].fillna(0, inplace=True)
        df['W+H'] = df['BB'] + df['H']
    else:
        raise ValueError('Incorrect player string')
    return df


def add_cbs_id(df):
    idkey = pd.read_csv('./source_data/ids.csv', dtype={'cbs_id': str}, encoding='iso-8859-1')
    # Merge dataframes (SQL-style)
    return df.merge(idkey[['fg_id', 'cbs_id']], left_on='playerid', right_on='fg_id', how='left')


def addcbs_info(df, cbs, players):
    """This function writes the eligible cbssports positions to the projections file"""
    out = df.merge(cbs, left_on='cbs_id', right_on='cbs_id', how='inner')
    print('Some data in the cbs players file is NA -- removing it:')
    print(out.loc[out['position'].isnull(), ['Name', 'Team', 'Pos', 'jabo_team', 'Salary', 'WAR']])
    return out[out['position'].notnull()]


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
    print('The following pitchers are not projected to pitch in 2017:')
    for _, row in df.iterrows():
        if (row['GS'] > 0) and (row['GNS'] == 0):
            SP = SP.append(row, ignore_index='True')
        elif (row['GNS'] > 0):
            RP = RP.append(row, ignore_index='True')
        else: #GS=0, GNS=0
            print(row)
    return SP, RP


def parse_cbs_files(players):
    """Converts the cbs html files to csv."""
    soup = BeautifulSoup(open('./source_data/cbs_{:s}.html'.format(players), encoding='cp1252'), 'html.parser')
    sortable_stats = soup.find(attrs={"id": "sortableStats"})
    players = sortable_stats.find_all('tr')
    jabo_team, mlb_team, pos, sal, name, cbs_id = [], [], [], [], [], []
    for player in players:
        row = player.find_all('td')
        if len(row) == 6:  # make sure it's not a header or other bogus row
            jabo_team.append(row[1].find('span')['title'])
            name.append(row[2].find('a').string)
            mlb_team.append(row[2].find('span').string[-3:])
            cbs_id.append(row[2].find('a')['href'].split('/')[-1])
            pos.append(row[3].string)
            sal.append(row[4].string)
    return pd.DataFrame({'player_name': name, 'jabo_team': jabo_team, 'mlb_team': mlb_team, 'position': pos,
                         'salary': sal, 'cbs_id': cbs_id})
