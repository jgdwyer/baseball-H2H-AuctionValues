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
