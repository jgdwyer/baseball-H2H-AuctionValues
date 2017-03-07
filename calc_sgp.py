import csv
import numpy as np
import bisect

N_teams = 14
N_activehitters = 9

#Define a function to take the mean and std of a column of the data
def mean_and_std(fooy, colind):
    data = [entry[colind] for entry in fooy]
    mm = np.mean(data)
    ss = np.std(data)
    return mm,ss

def sgp_hitters(asgp=[0,0,0,0,0,0,0,0]):
    # This script calculates the sgp points hitters get in each category
    # The name of our output file
    ofile = open('tmp/hitssgp.csv', 'w')
    writer = csv.writer(ofile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    #Load our projections file and populate entries in two new lists
    with open('tmp/hits2.csv') as f:
      f_csv = csv.reader(f,delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
      statsall = [entry for entry in f_csv]
    with open('tmp/hits2.csv') as f:
      f_csv=csv.reader(f,delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
      statstop = [entry for entry in f_csv]
    # Get the headerss (and remove them from these lists)
    h=statsall.pop(0)
    statstop.pop(0)
    # Get some indices
    scoringcats=["AVG","OBP","SLG","HR","R","RBI","SB","TB"]
    # add some new entries to the header file
    h.append("wAVG") #These "w" columns are intermediate steps used to calculate SGP for rate stats
    h.append("wOBP")
    h.append("wSLG")
    h.append("sAVG")
    h.append("sOBP")
    h.append("sSLG")
    h.append("sHR")
    h.append("sR")
    h.append("sRBI")
    h.append("sSB")
    h.append("sTB")
    h.append("SGP") #This is the total SGP column
    #Get the SGP replacement level headers from the matlab script (Get_SGP_thresholds_from_lastyeardata.m)
    h1file=csv.reader(open('source_data/sgp_thresh_lastyear_header.csv'),delimiter=',')
    h_sgp=[entry for entry in h1file]
    h_sgp=h_sgp.pop(0) #There's only one line in this file--h_sgp refers to header for this file
    #Get the actual values from that same file
    h2file=csv.reader(open('source_data/sgp_thresh_lastyear_values.csv'),delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
    lsgp=[entry for entry in h2file]
    lsgp1=lsgp.pop(0) #This is the increase in each category per point
    lsgp2=lsgp.pop(0) #This is the y-offset from 0 (worst team has about this much)
    #Sort the data
    statstop.sort(key=lambda statstop: statstop[h.index("wOBA")],reverse=True)
    #Remove the botttom entries of the data
    for ii in range(0,len(statstop)-N_teams*N_activehitters):
      statstop.pop(-1)
    #Get the mean # of abs and hits per player of the top guys
    mab,sab=mean_and_std(statstop,h.index("AB"))
    mh,sh=mean_and_std(statstop,h.index("H"))
    mavg,savg=mean_and_std(statstop,h.index("AVG"))
    #Calculate "wAVG"
    for row in statsall:
        numer=(N_activehitters-1)*mh+row[h.index("H")]
        denom=(N_activehitters-1)*mab+row[h.index("AB")]
        row.append((numer/denom)-mavg)
    #Get the mean # of PAs and OBP
    mpa,spa=mean_and_std(statstop,h.index("PA"))
    mobp,sobp=mean_and_std(statstop,h.index("OBP"))
    #Calcualte the mean # of times on base
    monbase=mobp*mpa
    #Now calculate "wOBP"
    for row in statsall:
        numer=(N_activehitters-1)*monbase + row[h.index("H")] + row[h.index("BB")] + row[h.index("HBP")]
        denom=(N_activehitters-1)*mpa + row[h.index("PA")]
        row.append((numer/denom)-mobp)
    #Get the mean # of TBs & slg
    mtb,stb=mean_and_std(statstop,h.index("TB"))
    mslg,sslg=mean_and_std(statstop,h.index("SLG"))
    #Calculate "wSLG"
    for row in statsall:
        numer=(N_activehitters-1)*mtb + row[h.index("TB")]
        denom=(N_activehitters-1)*mab + row[h.index("AB")]
        row.append((numer/denom)-mslg)
    #Now get the sgp by dividing by the values calculated from last year's totals
    for row in statsall:
    #Somehow need to calculate wavg relative to the improvement each hitter would provide over the replacement level BA
        row.append((row[h.index("wAVG")])/lsgp1[h_sgp.index("AVG")]-asgp[h_sgp.index("AVG")])
        row.append((row[h.index("wOBP")])/lsgp1[h_sgp.index("OBP")]-asgp[h_sgp.index("OBP")])
        row.append((row[h.index("wSLG")])/lsgp1[h_sgp.index("SLG")]-asgp[h_sgp.index("SLG")])
        row.append((row[h.index("HR")]-lsgp2[h_sgp.index("HR")])/lsgp1[h_sgp.index("HR")]-asgp[h_sgp.index("HR")])
        row.append((row[h.index("R")]-lsgp2[h_sgp.index("R")])/lsgp1[h_sgp.index("R")]-asgp[h_sgp.index("R")])
        row.append((row[h.index("RBI")]-lsgp2[h_sgp.index("RBI")])/lsgp1[h_sgp.index("RBI")]-asgp[h_sgp.index("RBI")])
        row.append((row[h.index("SB")]-lsgp2[h_sgp.index("SB")])/lsgp1[h_sgp.index("SB")]-asgp[h_sgp.index("SB")])
        row.append((row[h.index("TB")]-lsgp2[h_sgp.index("TB")])/lsgp1[h_sgp.index("TB")]-asgp[h_sgp.index("TB")])
        #Sum up all of these entries to get the total SGP
        row.append(sum(row[h.index("sAVG"):h.index("sTB")+1]))
    #Now sort by total SGP descending
    statsall.sort(key=lambda statsall: statsall[h.index("SGP")],reverse=True)
    writer.writerow(h) #Write the header row to file
    #Write all rows to file
    for row in statsall:
        writer.writerow(row)

def addpos():
    """This function writes the eligible cbssports positions to the projections file"""
    cbs_h = './tmp/cbs_hitters.csv'
    #Have to treat C and U speciall (C b/c it's contained in CF, and U b/c can't have any other strings in it)
    poslist=['1B','2B','3B','SS','LF','CF','RF']
    poslistw=['w1B','w2B','w3B','wSS','wLF','wCF','wRF']
    #Open csv writer files for each position
    ofC=open('./tmp/pos/C.csv',"w")
    of1B=open('./tmp/pos/1B.csv',"w")
    of2B=open('./tmp/pos/2B.csv',"w")
    of3B=open('./tmp/pos/3B.csv',"w")
    ofSS=open('./tmp/pos/SS.csv',"w")
    ofLF=open('./tmp/pos/LF.csv',"w")
    ofCF=open('./tmp/pos/CF.csv',"w")
    ofRF=open('./tmp/pos/RF.csv',"w")
    ofUonly=open('./tmp/pos/Uonly.csv',"w")
    ofUall=open('./tmp/pos/Uall.csv',"w")
    #writer = csv.writer(ofile, delimiter=',')#, quotechar='"', quoting=csv.QUOTE_ALL)
    wC=csv.writer(ofC, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    w1B=csv.writer(of1B, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    w2B=csv.writer(of2B, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    w3B=csv.writer(of3B, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    wSS=csv.writer(ofSS, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    wLF=csv.writer(ofLF, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    wCF=csv.writer(ofCF, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    wRF=csv.writer(ofRF, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    wUonly=csv.writer(ofUonly, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    wUall=csv.writer(ofUall, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    posdict = {'w1B': w1B, 'w2B': w2B, 'w3B': w3B, 'wSS': wSS, 'wLF': wLF,
               'wCF': wCF, 'wRF': wRF}
    #Load jabo cbssports data for player (cbsid, name, team, salary, etc.)
    #Load csv data of player cbsid, player name, and mlb team
    p1file=csv.reader(open(cbs_h), delimiter=',') #not quoting because the ids should be strings (and they aren't quoted in file)
    pp=[entry for entry in p1file]
    #Now get lists of each entry
    p_cbsid = [entry[0] for entry in pp]
    #p_name=zip(*p_id_name_mlbteam)[1]
    p_mlbteam = [entry[1] for entry in pp]
    p_jaboteam = [entry[2] for entry in pp]
    p_positions = [entry[3] for entry in pp]
    p_salary = [entry[4] for entry in pp]

    #Now load our hitters' projections file and funnel anyone eligible at catcher to an output file
    with open('tmp/hitssgp.csv') as f:
        f_csv=csv.reader(f,delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
        header = next(f_csv)
        #Append a few new fields to the header that were obtained from the jabo cbssports html
        header.append("positions")
        header.append("mlb")
        header.append("jabo")
        header.append("sal")
        #Write the header row to some output files
        wC.writerow(header)
        wUonly.writerow(header)
        wUall.writerow(header)
        for w2 in poslistw:
            posdict[w2].writerow(header)
        for row in f_csv:
            #Get the index of each csv id
            try:
                ind=p_cbsid.index(row[header.index("cbsid")])
                #add the positions and other info to each row
                row.append(p_positions[ind])
                row.append(p_mlbteam[ind])
                row.append(p_jaboteam[ind])
                row.append(int(p_salary[ind]))
            except:
    	    #Give a message if unable to find the index value
                strr='Could not find index: '+row[header.index("cbsid")]+' in the lookup table.\nCorresponds to '+row[0]+'\n'
                print(strr)
                continue
            #Find the position and write to the total U file
            wUall.writerow(row)
            if "C" in p_positions[ind] and "CF" not in p_positions[ind]:
                wC.writerow(row)
            if "U" == p_positions[ind]:
                wUonly.writerow(row)
            for w2,ps in zip( poslistw,poslist):
                if ps in p_positions[ind]:
                    posdict[w2].writerow(row)



def calc_pos_scarcity():
    #Have to treat C and U speciall (C b/c it's contained in CF, and U b/c can't have any other strings in it)
    poslist=['1B','2B','3B','SS','LF','CF','RF']
    poslistw=['w1B','w2B','w3B','wSS','wLF','wCF','wRF']
    #ofUonly=open('Uonly.csv',"r")
    #ofUall=open('Uall.csv',"r")
    o_list=['o1','o2','o3','o4','o5','o6','o7','o8','o9']
    p_list = ['p0','p1','p2','p3','p4','p5','p6','p7','p8','p9']
    allpos_list = ['Uall','Uonly','C','1B','2B','3B','SS','LF','CF','RF']
    #Initialize these lists
    #Load the files into lists (p0,p1, etc.)
    pdict = dict()
    odict = dict()
    for p, pos in zip(p_list, allpos_list):
        pdict[p] = list(csv.reader(open('tmp/pos/' + pos + '.csv'), delimiter=',',quoting=csv.QUOTE_NONNUMERIC))
    for o in o_list:
        #Initiailize each list by putting in the best hitter (will remove later)
        odict[o] = [pdict['p0'][1]]
    #Remove the header from the Uall list
    header = pdict['p0'].pop(0)
    print(header)
    #Now go through the list in order of players in p0 (Uall) and assign them positions based on the best rank they would be at at each position. Break ties with the defensive spectrum
    #Note that it doesn't actually matter who is in each list. The point is to get replacement values
    for row in pdict['p0']:
        #Get the numbers corresponding to each player's eligible positions
        posnum=get_post_num(row[header.index("positions")])
        #Get the sgp of the player in this row
        sgp=row[header.index("SGP")]
        #now get the rank of the available positions
        posrank=[]
        #Loop over all positions this player is eligible at
        #Get the SGP of all players at each eligible position
        for nums in posnum:
            # try:
                # print(header.index("SGP"))
                # print(nums)
                # print(list(zip(*odict["o"+str(nums)])))
            sgpofcolumn=list(zip(*odict["o" + str(nums)]))[header.index("SGP")]
                #print nums
                # print(sgpofcolumn)
            #Not sure what this error is trying to catch...an empty list?
            # except TypeError:
            #     sgpofcolumn=[]
            #     sgpofcolumn.append(odict["o"+str(nums)][header.index("SGP")])
            #For each eligible position, find out how many players are better (by SGP)
            posrank.append(get_rank(sgpofcolumn,sgp))
            #End position loop
        print(posrank)
        #Get which position the player would be the next best at by finding the one with the least number of better players at it
        indices = [i for i, x in enumerate(posrank) if x == min(posrank)]
        print(indices)
        bestposits=[]
        #Need to sort out how to deal with ties:
        #First initialize a new variable with all tied positions
        for i in indices:
            bestposits.append(posnum[i])
        print(bestposits)
        #In the case of ties, go down the defensive spectrum
        defensive_spectrum=[1, 3, 9, 7, 8, 5, 4, 6, 2]
        #Values overwrite each other so the toughest to fill position is left at the end
        for pp in defensive_spectrum:
            if pp in bestposits: bestpos=pp
        #Finally print the row to the appropriate file
        odict["o"+str(bestpos)].append(row)
        #print(row)
        print(bestpos)
        print('fooya')
        #FINISH looping through all entries in the Uall file
    #Now remove the initialized value of the best hitter in each list
    for o in o_list:
        odict[o].pop(0)
    #Load the previous sgp file to add to it
    sgp_old = list(csv.reader(open('./tmp/sgp_addends.csv'), delimiter=',',
                   quoting=csv.QUOTE_NONNUMERIC))
    sgp_old=sgp_old[0]
    #Get the headers too
    h1file=csv.reader(open('./source_data/sgp_thresh_lastyear_header.csv'),
                      delimiter=',')
    h_sgp=[entry for entry in h1file]
    h_sgp=h_sgp.pop(0)
    indsgpcat=[0]*8
    indsgpcat[0]=header.index("sR")
    indsgpcat[1]=header.index("sHR")
    indsgpcat[2]=header.index("sRBI")
    indsgpcat[3]=header.index("sSB")
    indsgpcat[4]=header.index("sTB")
    indsgpcat[5]=header.index("sAVG")
    indsgpcat[6]=header.index("sOBP")
    indsgpcat[7]=header.index("sSLG")
    #also need to account for the bench hitters. assume every team carries 3. then 42 extra hitters. more than 4 teams owrth
    stardiff=[]
    starthresh=[]
    #We need to normalize SGP so that the total available SGP of all hitters is the number of points that can be gained (i.e., for each category, there are 14 teams, so there are 13 points to be gained in each for each)
    for k in range(0,8): #loop over hitting categories
        star=0
        for i in range(0,N_teams): #Loop over #teams+4
            for j in range(1,10): #Loop over positions
                #Load the sum of SGP for each category for the top N_teams+4 players at each position since this will represent the total number of owned hitters
                star += odict["o"+str(j)][i][indsgpcat[k]]
                print(i, j, star, odict["o"+str(j)][i])
        #We're aiming to minimize this total in order that the sum of points of all the owned players represents the correct
        #Use sum(i=1:N,i)=(N+1)N/2
        #Total SGP available: Team A can gain 13pnts, Team B can gain 12pnts, etc.
        #total number of sgp that can be gained by all teams..each category should have the same # ofthese
        #N_teams not N_teams+4
        staradd = star - N_teams*(N_teams-1)/2 #N_teams-1    #N_teams*(N_teams-1)/2
        #This is the offset threshold that gets added on so that the total number of category points are right
        starthresh.append(staradd)
        #This gets added in to the old values
        #Divide the difference by the total number of active players since all  will be contributing to the category
        staradd=sgp_old[k] + staradd/((N_teams)*N_activehitters)
        stardiff.append(staradd)
        print("endo")
    print(star, "diff", staradd, staradd/(N_teams*N_activehitters))
    #stardiff=staradd/(N_teams*9)
    writer = csv.writer(open('./source_data/sgp_addends.csv',"w"), delimiter=',',
                        quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(stardiff)
    #Write the offsets to each SGP category
    writer2 = csv.writer(open('./source_data/sgp_thresh.csv',"w"), delimiter=',',
                         quoting=csv.QUOTE_NONNUMERIC)
    writer2.writerow(starthresh)
    #Now print the rows in each file
    cnt=0
    sgp_pos_addends=[0]*10
    for cnt in range(0, N_teams): #+4
        print(cnt)
        #print(p9[cnt][0]+" "+str(p9[cnt][header.index("SGP")]))
        if (cnt==N_teams-1): #+4
            sgp_pos_addends[0]=0
            for ii in range(1, 10):
                print(ii)
                sgp_pos_addends[ii] = odict['o' + str(ii)][cnt][header.index("SGP")]
    print(sgp_pos_addends)
    writer3 = csv.writer(open('./tmp/sgp_pos_addends.csv',"w"), delimiter=',',
                         quoting=csv.QUOTE_NONNUMERIC)
    writer3.writerow(sgp_pos_addends)



def get_post_num(posstring):
    """Take the position strin and turns it into a number(s) (3=1B, 4=2B, etc.)"""
    q = posstring.split(',')
    posnum = []
    r_dict = {'C': 2, '1B': 3, '2B': 4, '3B': 5, 'SS': 6, 'LF': 7, 'CF': 8,
              'RF': 9, 'U': 1}
    for r in q:
        posnum.append(r_dict[r])
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
