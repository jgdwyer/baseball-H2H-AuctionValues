import csv
import pandas as pd

masterid_file = './source_data/ids.csv'


def add_hitters():
    # Load hitter projection file and write new columns
    hitter_projection_file = './source_data/proj_dc_hitters.csv'
    df = pd.read_csv(hitter_projection_file)
    df['1B'] = df['H'] - (df['2B'] + df['3B'] + df['HR'])
    df['TB'] = df['1B']*1 + df['2B']*2 + df['3B']*3 + df['HR']*4
    # Load the id's
    idkey = pd.read_csv('./source_data/ids.csv', dtype={'cbs_id': str})
    # Merge dataframes (SQL-style)
    out = df.merge(idkey[['fg_id', 'cbs_id']], left_on='playerid',
                 right_on='fg_id', how='left')
    #Manually add cbs ids for certain players
    out.loc[out.playerid=='3711', 'cbs_id'] ='1741019'
    out.loc[out.playerid=='sa737507', 'cbs_id'] = '2066300'
    # Show the best missing hitters that our id file doesn't have
    print("Best hitters without id's. Manually add these guys in:")
    print(out[out['cbs_id'].isnull()][['Name', 'Team','WAR','playerid']].\
        sort_values('WAR')[::-1][:10])
    # Remove rows that are null in fangraph ids
    out = out[out['cbs_id'].notnull()]
    return out



def add_pitchers():
    pitcher_projection_file = './source_data/proj_dc_pitchers.csv'
    info_from_jabostatshtml_P = './tmp/cbs_pitchers.csv'
    ofile = open('tmp/pitch2.csv', 'w')
    writer = csv.writer(ofile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    #Load jabo cbssports data for player (cbsid, name, team, salary, etc.)
    #Load csv data of player cbsid, player name, and mlb team
    p1file = csv.reader(open(info_from_jabostatshtml_P), delimiter=',') #not quoting because the ids should be strings (and they aren't quoted in file)
    pp = [entry for entry in p1file]
    #Now get lists of each entry
    p_cbsid = [entry[0] for entry in pp]
    p_mlbteam = [entry[1] for entry in pp]
    p_jaboteam = [entry[2] for entry in pp]
    p_salary = [entry[4] for entry in pp]
    with open(pitcher_projection_file) as f:
        f_csv=csv.reader(f)
        header = next(f_csv)
        print(header)
        header.append("GNS")
        header.append("SO/BB")
        header.append("IP/GS")
        header.append("W+H")
        header.append("cbsid")
        header.append("sal")
        header.append("mlb")
        header.append("jabo")
        header.append("xsal")
        header.append("dsal")
        extrasize=10
        if "HLD" not in header:
            header.append("HLD")
            extrasize+=1
        #indTB=header.index("TB")
        print(header)
        header[0] = "Name" #For some reason the first entry is sometimes oddly formatted
        writer.writerow(header)
        #Set column types..default is float since most are numerical values
        col_types=[float]*(len(header))
        col_types[0]=str #Set name to be a string
        col_types[header.index("playerid")]=str
        col_types[header.index("cbsid")]=str
        if "Team" in header:
            col_types[header.index("Team")]=str
        e_csv=list(csv.reader(open(masterid_file)))
        e_header=e_csv.pop(0)
        print(e_header)
        #Count the total number of rows not including the header
        row_count = sum(1 for row in e_csv)

        ind_e_fgid=e_header.index("fg_id")
        ind_e_cbsid=e_header.index("cbs_id")
        for row in f_csv:
            row.extend([0]*extrasize) #Fill in the row with blank entries so they can be referenced
            row=list(convert(value) for convert, value in zip(col_types,row))
            #Add new pitching columns
            row[header.index("GNS")] = row[header.index("G")]-row[header.index("GS")] #Games not started
            if row[header.index("BB")]==0:
                row[header.index("SO/BB")] = 0
            else:
                row[header.index("SO/BB")] = row[header.index("SO")]/row[header.index("BB")]
            if row[header.index("GNS")]==0: #INN/dGS
                if row[header.index("GS")]==0:
                    row[header.index("IP/GS")]=0
                else:
                    row[header.index("IP/GS")]=row[header.index("IP")]/row[header.index("GS")]
            else:
                row[header.index("IP/GS")]=0
            #add W+H column
            row[header.index("W+H")] = row[header.index("BB")] + row[header.index("H")]
            #Now start the loop through the conversions to add the cbs id
            mrow=0
            #print(row[header.index("playerid")])
            for masterrow in e_csv:
                if row[header.index("playerid")]==masterrow[ind_e_fgid]: #and not masterrow[ind_e_cbsid]:
                    #print(p_salary[p_cbsid.index(str(masterrow[ind_e_cbsid]))])
                    try:
                        row[header.index("cbsid")] = str(masterrow[ind_e_cbsid])
                        #Now get the index in the jabo file derived from the html
                        ind=p_cbsid.index(str(masterrow[ind_e_cbsid]))
                        #Add cats
                        row[header.index("sal")] = int(p_salary[ind])
                        row[header.index("mlb")] = p_mlbteam[ind]
                        row[header.index("jabo")] =p_jaboteam[ind]
                        row[header.index("xsal")] = 0
                        row[header.index("dsal")] = 0
                        if not row[header.index("HLD")]: #uses implicit booleaness to see if its empty. if it is write zero and take projections from razzball
                            row[header.index("HLD")] = 0
                        writer.writerow(row)
                        break
                    except ValueError as ve:
                        pass
                mrow+=1
                #Print rows where we did not have a cbsid available
                if mrow == row_count:
                     print(str(row[header.index("playerid")]) + " " + str(row[header.index("WAR")]) + " " + row[0])



def separate_SP_RP():
    ofSP=open('./tmp/pos/aSP.csv', "w")
    ofRP=open('./tmp/pos/aRP.csv', "w")
    ofSPRP=open('./tmp/pos/aSPRP.csv', "w")
    ofNG=open('./tmp/NotPitchingin2017.csv', "w")
    wSP=csv.writer(ofSP, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    wRP=csv.writer(ofRP, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    wSPRP=csv.writer(ofSPRP, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    wNG=csv.writer(ofNG, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    with open('./tmp/pitch2.csv') as f:
        f_csv=csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
        pitch=[entry for entry in f_csv ]
    header=pitch.pop(0)
    indGNS=header.index("GNS")
    indGS=header.index("GS")
    SP=[]
    RP=[]
    SPRP=[]
    wSP.writerow(header)
    wRP.writerow(header)
    wSPRP.writerow(header)
    wNG.writerow(header)
    for row in pitch:
        if row[indGS]>0 and row[indGNS]==0:
            SP.append(row)
            wSP.writerow(row)
        elif row[indGS]==0 and row[indGNS]>0:
            RP.append(row)
            wRP.writerow(row)
        elif row[indGS]==0 and row[indGNS]==0:
            wNG.writerow(row)
        else:
            SPRP.append(row)
            wSPRP.writerow(row)

# NOTE that holds are already included in the depth chart projections this year!
# def add_holds():
#     holds_projection_file = './source_data/razzball_holds.csv'
#     of = open('tmp/pitch3.csv',"wb")
#     wof = csv.writer(of, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
#     #Load the main projections file
#     with open('tmp/pitch2.csv') as f:
#         f_csv = csv.reader(f, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
#         main = [entry for entry in f_csv ]
#     header_main = main.pop(0)
#     #Load the razzball holds projections file
#     h=csv.reader(open(holds_projection_file), delimiter=',')
#     razz = [entry for entry in h]
#     header_razz = razz.pop(0)
#     r_name = [entry[header_razz.index('Name')] for entry in razz]
#     r_ip = [entry[header_razz.index('IP')] for entry in razz]
#     r_hd = [entry[header_razz.index('HLD')] for entry in razz]
#     #Check to see if holds are already entered as a field (if they are, we can exit this loop)
#     if sum(zip(*main)[header_main.index("HLD")]) == 0:
#     #If holds aren't included in these projections, add them as an external projection file
#     for row in main:
#         try:
#             ind=r_name.index(row[0])
#             go=1
#         except ValueError:
#             go=0
#         #Normalize by the innings projected by fangraphs..otherwise the projections will be inconsistent
#         if go==1:
#             if float(r_ip[ind])==0:
#                 row[header_main.index("HLD")] = 0
#             else:
#                 row[header_main.index("HLD")] = round(float(row[header_main.index("IP")])*float(r_hd[ind])/float(r_ip[ind]))
#
#     #Write to file
#     wof.writerow(header_main)
#     for row in main:
#         wof.writerow(row)
#
#     #Rename the old file and update the new one to the old one's name (this allows this script to be modular
#     call(["mv","working/pitch2.csv", "working/pitch2_old.csv"])
#     call(["mv","working/pitch3.csv", "working/pitch2.csv"])
