import csv
import numpy as np

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
