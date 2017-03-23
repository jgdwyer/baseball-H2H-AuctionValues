from os.path import join
import re
import csv

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
