import csv
import pandas as pd
import numpy as np
from os.path import join
import re

def prepPlayers(players):
    parse_csv('cbs_' + players + '.html')
    df = load_fangraphs(players)
    df = add_cats(df, players)
    df = add_cbs_id(df)
    df = add_ids_manually(df, players)
    df = print_missing_and_remove_nulls(df)
    df = addcbs_info(df, players)
    return df

def load_fangraphs(players):
    return pd.read_csv('./source_data/proj_dc_' + players + '.csv')

def add_hitter_cats(df):
    df['1B'] = df['H'] - (df['2B'] + df['3B'] + df['HR'])
    df['TB'] = df['1B']*1 + df['2B']*2 + df['3B']*3 + df['HR']*4
    return df


def add_ids_manually(df, players):
    fg_to_cbs = dict()
    if players == 'hitters':
        fg_to_cbs['3711'] = '1741019'
        fg_to_cbs['sa737507'] = '2066300'
    elif players == 'pitchers':
        fg_to_cbs['sa658473'] = '2044482'
        fg_to_cbs['sa621465'] = '2138864'
        fg_to_cbs['sa597893'] = '2449977'
    else:
        raise ValueError('Incorrect player string')
    for fgid, cbsid in fg_to_cbs.items():
        df.loc[df.playerid==fgid, 'cbs_id'] = cbsid
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


def parse_csv(html_filename):
    """Converts the cbs html files to csv. The whole thing should be rewritten
        with beautiful soup rather than regular expressions.
    in: html_filename [str] -- the filename of the html
                               (e.g. 'cbs_hitters.html')"""
    csv_file = html_filename[:-5] + '.csv'
    outfile=open('./source_data/' + csv_file, 'w')
    writer = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    with open('./source_data/' + html_filename) as infile:
        for line in infile:
            # Extract the cbs player id
            cbsid = re.findall(r'actionButtons_(.*?)"><',line)
            cbsid = ''.join(cbsid)
            # Extract the mlb team
            mlb = re.findall(r' \| (.*?)<',line)
            mlb = ''.join(mlb)
            # Extract the jabo team
            jabo = re.findall(r'tooltip[\'"] title=(.*?)>', line)
            jabo = ''.join(jabo)
            if "On Waivers" in jabo:
                jabo = 'Free Agent'
            else:
                jabo = re.findall(r'Owned By (.*?)\'>', line)
                jabo = ''.join(jabo)
                jabo = jabo.split('"')[0]
            # Extract the eligible positions
            line = re.findall(r'"right">(.*?)<\/td><td align="right">9999', line)
            line = ''.join(line)
            if 'hitters' in html_filename:
                pos = re.findall(r'^(.*?)<', line)
            else:
                pos = re.findall(r'^(.*?)<\/td', line)
            pos = ''.join(pos)
            # Extract the players' salaries
            sal = re.findall(r'right\">(.*?)$', line)
            sal = ''.join(sal)
            if sal:
                sal = int(sal)
            # Store as list and write to a row in csv file
            c=[]
            if mlb:
                c.append(cbsid)
                c.append(mlb)
                c.append(jabo)
                c.append(pos)
                c.append(sal)
                writer.writerow(c)
