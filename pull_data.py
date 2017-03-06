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

# def _pull_hitters():
#     """Returns html file corresponding to year-to-date team scoring stats page"""
#     # Prompt user for league name and user name
#     league = 'jabo'
#     user   = input('Enter user name: ')
#     # Prompt user for their password (but don't display it)
#     password = getpass.getpass()
#     # Desired html page
#     # myurl = ('http://' + league + '.baseball.cbssports.com/stats/' +
#     #          'stats-main/teamtotals/ytd:f/scoring/stats')
#     myurl = 'http://' + league + '.baseball.cbssports.com/stats/stats-main/' + \
#             'all:C:1B:2B:3B:SS:LF:CF:RF:U/period-1:p/z8/?print_rows=9999'
#     # Authenticating page
#     loginurl = 'https://auth.cbssports.com/login/index'
#     # The post data (found using chrome developer tools)
#     # See http://stackoverflow.com/q/20415751/4846823
#     payload = {
#        'dummy::login_form': 1,
#        'form::login_form': 'login_form',
#        'xurl': myurl,
#        'master_product': 150,
#        'vendor': 'cbssports',
#        'userid': user,
#        'password': password,
#        '_submit': 'Sign in' }
#     # Make a request to the login page to make sure login info is correct
#     try:
#         response = requests.get(loginurl)
#     except requests.exceptions.ConnectionError as e:
#         print("Bad Domain - Could not log in")
#     # Note that we submit to the authenticating url, not the desired url
#     session = requests.session()
#     p = session.post(loginurl, data=payload)
#     r = session.get(myurl) # now get desired url
#     # with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
#     #     shutil.copyfileobj(response, out_file)
#     filename = './source_data/hitters.html'
#     with open(filename, 'wb') as f:
#         f.write(r.content)
#     return r.content
