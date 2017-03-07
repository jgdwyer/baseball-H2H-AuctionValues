import csv

masterid_file = './source_data/ids.csv'


def add_hitters():
    """This script loops through out hitter's projections and adds cbs ids to
    each player. It also categorizes each entry as floats or strings and adds
    two more derived categories (singles and total bases). Finally when piped
    out, it writes to file the players for which I don't have a cbs id """

    hitter_projection_file = './source_data/proj_dc_hitters.csv'

    #The id file we will use to add the cbsids to each players entry
    #master id file is loaded from namelist
    #The hitter projections we will loop through
    #This file is loaded from the namelist

    ofile = open('tmp/hits2.csv', 'w')
    writer = csv.writer(ofile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    #Open the projections file and loop through it
    with open(hitter_projection_file) as f:
        f_csv = csv.reader(f)
        # Get the header from the hitter projections
        header = next(f_csv)
        # Loop through the header and determine whether each entry is a float or str
        # Start off by defining them all as floats and then convert some to strings
        col_types = [float]*(len(header) - 1 + 4)
        #Add these three entries to the header file
        header.append("1B")
        header.append("TB")
        header.append("cbsid")
        #First entry is the name, but there is some weird stuff (e.g. \xef)..get rid of that
        header[0] = "Name"
        col_types[0] = str #Set the name column to be a string
        #Define certain column entries as strings
        col_types[header.index("playerid")] = str
        col_types[header.index("cbsid")] = str
        if "Team" in header:
            col_types[header.index("Team")] = str
        # Perform list comprehension on the data to find any columns with "-1" as
        # the header..the data fields in this column are empty strings
        indices = [i for i, x in enumerate(header) if x == "-1"]
        for entry in indices:
            col_types[entry] = str
        #Write the header row to the output file
        writer.writerow(header)
        #Open the file that has all of the IDs
        id_csv = list(csv.reader(open(masterid_file)))
        #Get the header line of the id file
        id_header = id_csv.pop(0)
        #Count the total number of rows in the eligibility file not including the header
        row_count = sum(1 for row in id_csv)
        #Get the list index value of where the following id values are in the id file
        ind_id_fgid=id_header.index("fg_id")
        ind_id_cbsid=id_header.index("cbs_id")

        #Loop over rows in our projections file
        for row in f_csv:
    	#Turn the data in each row into its proper datatype (string or float)
            row=list(convert(value) for convert, value in zip(col_types,row))
            #Add new hitting columns: 1B & TB
            row.append(row[header.index("H")] - row[header.index("2B")] - row[header.index("3B")] - row[header.index("HR")])
            row.append(row[header.index("1B")]*1 + row[header.index("2B")]*2 + row[header.index("3B")]*3 + row[header.index("HR")]*4)

            #Now loop through each row in our id master file to find the one with the matching fangraphs id
            mrow = 0 #initialize this variable
            for idrow in id_csv:
                if row[header.index("playerid")] == idrow[ind_id_fgid]: #and not idrow[ind_id_cbsid]:
                    try:
                        #Add the cbsid to the end of this row
                        row.append(str(idrow[ind_id_cbsid]))
                        #Write this row to file
                        writer.writerow(row)
                        break #exit loop
                    except ValueError as ve:
                        pass
                #Increment row by one
                mrow += 1
                #Print rows where we did not have a cbsid available
                if mrow == row_count:
                    #Manually add in some key players who were unlisted for some reason
                    #if 1==2:
                    #    print "just a placeholder"
                    if row[header.index("playerid")]=="18717":
                        row.append("2210864") #byung-ho park
                        writer.writerow(row)
                    elif row[header.index("playerid")]=="18718":
                        row.append("2215560") #Hyun-soo Kim
                        writer.writerow(row)
                    #Write to a different file (actually print to screen, but when this script is called will be saved)
                    else:
                        print(str(row[header.index("playerid")]) + " " + str(row[header.index("WAR")]) + " " + row[0])



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
