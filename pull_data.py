import urllib.request

def pull_ids():
    url = 'http://crunchtimebaseball.com/master.csv'
    filename = './source_data/ids.csv'
    # Download the file from `url` and save it locally under `file_name`:
    with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
        data = response.read() # a `bytes` object
        out_file.write(data)
