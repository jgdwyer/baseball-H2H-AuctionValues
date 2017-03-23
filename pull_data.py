import urllib.request
import getpass
import requests
import shutil

def pull_ids():
    url = 'http://crunchtimebaseball.com/master.csv'
    filename = './source_data/ids.csv'
    # Download the file from `url` and save it locally under `file_name`:
    with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
        data = response.read() # a `bytes` object
        out_file.write(data)

def pull_fangraphs():
    url1 = 'http://www.fangraphs.com/projections.aspx?pos=all&stats='
    url2 = '&type=fangraphsdc&team=0&lg=all&players=0'
    print('Go to: ' + url1 + 'bat' + url2 + ' and click export data')
    print('Go to: ' + url1 + 'pit' + url2 + ' for the pitcher data')

def pull_cbs():
    urlhit = 'http://jabo.baseball.cbssports.com/stats/stats-main/all:C:1B:2B:3B:SS:LF:CF:RF:U/period-1:p/z8/?print_rows=9999'
    urlpit = 'http://jabo.baseball.cbssports.com/stats/stats-main/all:SP:RP/tp:p/foo2016_2/?print_rows=9999'
    print('Click on the following links and save as html:')
    print(urlhit)
    print(urlpit)
