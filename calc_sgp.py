import csv
import numpy as np
import bisect
from subprocess import call #for calling mkdir
import pandas as pd

N_teams = 14
N_activehitters = 9
budget = 260
frac_hitter_budget = 0.5
output_dir = "./output/dc_3_6_2017/"

pos_dict = {'C': 2, '1B': 3, '2B': 4, '3B': 5, 'SS': 6, 'LF': 7, 'CF': 8,
          'RF': 9, 'U': 1}

#Define a function to take the mean and std of a column of the data
def mean_and_std(fooy, colind):
    data = [entry[colind] for entry in fooy]
    mm = np.mean(data)
    ss = np.std(data)
    return mm,ss

def sgp_hitters(df, asgp):
    # This script calculates the sgp points hitters get in each category
    # The name of our output file
    output_filename = 'tmp/hitssgp.csv'
    #Load our projections file and populate entries in two new lists
    # df = pd.read_csv('./tmp/hits2.csv')
    # Get the SGP replacement level headers from the matlab script (Get_SGP_thresholds_from_lastyeardata.m)
    header = pd.read_csv('./source_data/sgp_thresh_lastyear_header.csv')
    sgp = pd.read_csv('./source_data/sgp_thresh_lastyear_values.csv', names=header)
    # Sort the data
    df = df.sort_values(by='wOBA')[::-1]
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
    df['SGP'] = df[['sAVG', 'sOBP', 'sSLG', 'sHR', 'sR', 'sRBI', 'sSB', 'sTB']].sum(axis=1)
    #Now sort by total SGP descending
    df = df.sort_values(by='SGP')[::-1]
    df = df.reset_index(drop=True)
    # df.to_csv(output_filename, index=False)
    return df


def addpos(df):
    """This function writes the eligible cbssports positions to the projections file"""
    cbs_h = './tmp/cbs_hitters.csv'

    #Load jabo cbssports data for player (cbsid, name, team, salary, etc.)
    #Load csv data of player cbsid, player name, and mlb team
    cbs = pd.read_csv('./tmp/cbs_hitters.csv',
                    names=['cbs_id', 'mlb_team','jabo_team', 'Pos', 'Salary'],
                    dtype={'cbs_id':str})
    #Now load our hitters' projections file and funnel anyone eligible at catcher to an output file
    # df = pd.read_csv('./tmp/hitssgp.csv', dtype={'cbs_id': str})
    out = df.merge(cbs, left_on='cbs_id', right_on='cbs_id', how='inner')
    print('Some data in the cbs players file is NA -- removing it:')
    print(out[out.isnull().any(axis=1)][['Name', 'Team', 'jabo_team', 'Salary', 'wOBA']])
    out = out[out['Pos'].notnull()]
    # Create a dict of data frames
    meta = {'RF': pd.DataFrame(columns=out.columns),
            'CF': pd.DataFrame(columns=out.columns),
            'LF': pd.DataFrame(columns=out.columns),
            '1B': pd.DataFrame(columns=out.columns),
            '2B': pd.DataFrame(columns=out.columns),
            'SS': pd.DataFrame(columns=out.columns),
            '3B': pd.DataFrame(columns=out.columns),
            'C': pd.DataFrame(columns=out.columns),
            'U': pd.DataFrame(columns=out.columns),
            'Uonly': pd.DataFrame(columns=out.columns)}
    for _, row in out.iterrows():
        for pos in row['Pos'].split(','):
            meta[pos] = meta[pos].append(row, ignore_index='True')
        # Handle the case when the only eligible position is utility
        if row['Pos'] == 'U':
            meta['Uonly'] = meta['Uonly'].append(row, ignore_index='True')
    return meta





def calc_pos_scarcity(sgp_addends, meta):
    #Initiailize each list by putting in the best hitter (will remove later)
    meta_ranked = dict()
    for m in meta:
        meta_ranked[m] = meta[m].head(1)
    #Now go through the list in order of players in p0 (Uall) and assign them positions based on the best rank they would be at at each position. Break ties with the defensive spectrum
    #Note that it doesn't actually matter who is in each list. The point is to get replacement values
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
    #Get the headers too
    # Get the SGP replacement level headers from the matlab script
    #(Get_SGP_thresholds_from_lastyeardata.m)
    header = pd.read_csv('./source_data/sgp_thresh_lastyear_header.csv')
    sgp = pd.read_csv('./source_data/sgp_thresh_lastyear_values.csv', names=header)
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




def get_post_num(posstring):
    """Take the position strin and turns it into a number(s) (3=1B, 4=2B, etc.)"""
    q = posstring.split(',')
    posnum = []
    for r in q:
        posnum.append(pos_dict[r])
    return posnum


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







def add_pos_sgp(sgp_pos_addends):
    #First make the output directory if it doesn't exist
    call(["mkdir", "-p", output_dir])
    #Load the files into lists
    # Invert the position dictionary
    pos_dict_inv = {v: k for k, v in pos_dict.items()}
    pos_dict_inv[0] = 'Uall'
    csvw = dict()
    for i in range(0, 10):
        csvw[i] = csv.writer(open(output_dir + pos_dict_inv[i] + '.csv', 'w'),
                                    delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    p10a=open('./tmp/pos/Ulast.csv',"w")
    p10=csv.writer(p10a, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    hitters=list(csv.reader(open('tmp/pos/Uall.csv'),delimiter=',',quoting=csv.QUOTE_NONNUMERIC))
    hitters2=list(csv.reader(open('tmp/pos/Uall.csv'),delimiter=',',quoting=csv.QUOTE_NONNUMERIC))
    hdr=hitters2.pop(0)
    #The first value is garbage, we need to ignore it
    #Sort the list
    sgp_pos_add_sort=sorted(range(10), key=lambda k: sgp_pos_addends[k])
    sgp_pos_add_sort.remove(0)
    #Reverse the list order so we are sorting descending
    sgp_pos_add_sort.reverse()
    #Remove the header from the Uall list
    header=hitters.pop(0)
    indSGP = header.index("SGP")
    indcbsid = header.index("cbsid")
    indpos = header.index("positions")
    header.append("p_SGP")
    hdr.append("p_SGP")
    # Copy header so that we can reorder the values in the list
    # Rearrange the column order..note that this is for the header and we have
    # to repeat this below for the actual row entries in the loop
    catlist=["Name", "xusal", "xsal", "sal", "dsal", "mlb", "jabo", "positions",
             "PA", "AVG", "OBP", "SLG", "HR", "SB", "sAVG", "sOBP", "sSLG",
             "sR", "sRBI", "sTB", "sHR", "sSB", "R", "RBI", "wOBA", "WAR",
             "playerid", "SGP", "p_SGP"]
    # Write the header in each of the output files
    for i in range(0, 10):
        csvw[i].writerow(catlist)
    p10.writerow(catlist)
    # Initialize
    navg=nobp=nslg=nhr=nr=nrbi=nsb=ntb=nsgp=0
    # Now go thru each player, add their new score and add them to the appropriate output list
    cntrr=0
    for row in hitters:
        hitters3 = list(csv.reader(open('./tmp/pos/Uall.csv'), delimiter=',',
                                 quoting=csv.QUOTE_NONNUMERIC))
        header=hitters3.pop(0)
        header.append("p_SGP")
        cntrr += 1
        # Get position numbers from the position string
        posnum=get_post_num(row[indpos])
        # Check to see if the player gets extra points -- the following go IN ORDER
        q=row[indpos].split(',')
        for posits in q:
            sgp_addend=0
            for pn in sgp_pos_add_sort:
                if pn in posnum:
                    sgp_addend = sgp_pos_addends[pn]
        row.append(row[indSGP] - sgp_addend)
        # Count the sgp in each category
        navg += row[header.index("sAVG")]
        nobp += row[header.index("sOBP")]
        nslg += row[header.index("sSLG")]
        nhr += row[header.index("sHR")]
        nr += row[header.index("sR")]
        nrbi += row[header.index("sRBI")]
        nsb += row[header.index("sSB")]
        ntb += row[header.index("sTB")]
        nsgp += row[header.index("SGP")]
        #Now format each row with the appropriate number of digits for aestheticly pleasing viewing
        statcats = ["PA", 'AB', 'H', '2B', '3B', "HR", "R", "RBI", "BB",
                       "SO", "HBP", "SB", "CS", "wAVG", "wOBP", "wSLG", "sAVG",
                       "sOBP", "sSLG", "sHR", "sR", "sRBI", "sSB", "sTB", 'SGP', 'p_SGP']
        for statcat in statcats:
            if statcat in ['wAVG', 'wOBP', 'wSLG']:
                row[header.index(statcat)] = int(row[header.index(statcat)]*10000/10000)
            elif statcat in ["sAVG", "sOBP", "sSLG", "sHR", "sR", "sRBI", "sSB", "sTB", 'SGP', 'p_SGP']:
                row[header.index(statcat)] = int(row[header.index(statcat)]*10/10)
            else: #integer
                row[header.index(statcat)] = int(row[header.index(statcat)])
        #Reorder the row: Name, SGP,p_SGP, Pos, PA/AB, avg/obp/sgl, sgpcats, scoring cats, other
        row2=[] #initialize
        for cat in catlist:
            if cat in header:
                row2.append(row[header.index(cat)])
            else:
                row2.append(0)
        p10.writerow(row2)
    p10a.close() #was running into a bug..i think the csv writer wasn't closed and it was giving a strange error. explicitly close the open file before beginning tor read it
    #Now need to normalize SGP and p_SGP so that the sum of the owned players add up to the total amount of points
    #Also save the final output files for each position
    #Load the Ulast
    h1file=csv.reader(open('./tmp/pos/Ulast.csv'),delimiter=',',
                           quoting=csv.QUOTE_NONNUMERIC)
    data = [entry for entry in h1file]
    #with open('working/Ulast.csv', 'rb') as h1file:
    #    reader=csv.reader(h1file,delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
    #    data=list(reader)
    data_header = data.pop(0) #There's only one line in this file--h_sgp refers to header for this file
    data.sort(key=lambda data: data[data_header.index("p_SGP")], reverse=True)
    #Get the sum of SGP and p_SGP of the owned, starting players
    sgp_sum=p_sgp_sum=0
    for i in range(0,N_teams*N_activehitters-1):
        sgp_sum=sgp_sum+data[i][data_header.index("SGP")]
        p_sgp_sum=p_sgp_sum+data[i][data_header.index("p_SGP")]
    #Get the difference from what it should be
    sgp_diff = (N_teams*(N_teams-1)*8/2-sgp_sum)#/(N_teams*N_activehitters)  #8 hitting cats
    p_sgp_diff= (N_teams*(N_teams-1)*8/2-p_sgp_sum)#/(N_teams*N_activehitters)
    #Now loop over all this data and subtract this value off of all players SGP and p_SGP and save in rows
    for row in data:
        #Make the output of these columns look nice
        row[data_header.index("SGP")] = round(row[data_header.index("SGP")]*10)/10
        row[data_header.index("p_SGP")] = round(row[data_header.index("p_SGP")]*10)/10
        #Add two new columns
        #"xs_salary","xp_salary","diff_salary"
        xss = row[data_header.index("SGP")]/sgp_sum*budget*frac_hitter_budget*N_teams #multiply by hitter portion of budget
        xps = row[data_header.index("p_SGP")]/p_sgp_sum*budget*frac_hitter_budget*N_teams
        ds = row[data_header.index("sal")] - xps
        row[data_header.index("xusal")] = xss
        row[data_header.index("xsal")] = xps
        row[data_header.index("dsal")] = ds
        # Do some rounding
        row[data_header.index("xusal")] = round(row[data_header.index("xusal")])
        row[data_header.index("xsal")] = round(row[data_header.index("xsal")])
        row[data_header.index("dsal")] = round(row[data_header.index("dsal")])
        # Get position numbers
        posnum = get_post_num(row[data_header.index("positions")])
        # Now put the hitters into the master list and positional lists
        # Also add the sgp for the top 140 hitters in each category
        csvw[0].writerow(row)
        if "U" == row[data_header.index("positions")]:
            csvw[1].writerow(row)
        else:
            for posits in posnum:
                #This is the uonly case
                if posits != 1:
                    csvw[posits].writerow(row)
