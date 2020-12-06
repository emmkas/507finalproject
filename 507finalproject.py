#################################
##### Name: Emmeline Kaser
##### Uniqname: ekaser
#################################

from bs4 import BeautifulSoup
import requests
import json
import time
from datetime import datetime
import sqlite3
import plotly


BASE_URL = 'http://www.nuforc.org/webreports/' 
CACHE_FILENAME = "nuforc_cache.json"
CACHE_DICT = {}
DATABASE = 'NUFORC_Reports.sqlite'

class Report:
    '''a reported instance of a UFO sighting

    Instance Attributes
    -------------------
    date: date object
        the date of the sighting in MM/DD/YY format, converted from a string to a date object
    
    city: string
        the name of the city where the reported event happened

    state: string
        the 2-letter acronym for the state where the reported event happened

    shape: string
        the UFO shape

    '''
    def __init__ (self, date="no date", time="no time", city="no city", state="no state", shape="none"):
        self.date = date
        self.time = time
        self.city = city
        self.state = state
        self.shape = shape
    
    def info(self):
        '''Prints the report information as a single string

    Parameters
    ----------
    none

    Returns
    -------
    str
        Formatted print statement
    '''
        return (f"{self.date} in {self.city}, {self.state}")

def create_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    drop_reports_sql = 'DROP TABLE IF EXISTS "Reports"'

    drop_ufos_sql = 'DROP TABLE IF EXISTS "UFO_Types"'

    create_reports_sql = '''
        CREATE TABLE IF NOT EXISTS "Reports" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Date" DATE NOT NULL,
            "Time" TIME (0) NOT NULL,
            "City" TEXT NOT NULL,
            "State" TEXT NOT NULL
        )
    '''
            #"ShapeID" INTEGER NOT NULL


    create_ufos_sql = '''
        CREATE TABLE IF NOT EXISTS "UFO_Types" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Shape" TEXT NOT NULL
        )
    '''
    cur.execute(drop_reports_sql)
    cur.execute(drop_ufos_sql)
    cur.execute(create_reports_sql)
    cur.execute(create_ufos_sql)
    conn.commit()
    conn.close()


def open_cache():
    ''' Checks to see if the cache file exists. If it does, it loads the JSON into the CACHE_DICT dictionary.
    If it doesn't exist, it creates a new cache dictionary.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    cache: dict
        The opened cache
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache = json.loads(cache_contents)
        cache_file.close()
    except:
        cache = {}
    
    return cache


def save_cache(cache):
    ''' Saves the current cache.
    
    Parameters
    ----------
    cache: dict
        The dictionary of information to be saved
    
    Returns
    -------
    None
    '''
    cache_file = open(CACHE_FILENAME,"w")
    info_to_write = json.dumps(cache)
    cache_file.write(info_to_write)
    cache_file.close() 


def url_request_with_cache(url, cache):
    ''' Checks to see if the provided URL exists in the cache. If it does, it returns the cached information.
    If it doesn't, it fetches the information from the website.

    Parameters
    ----------
    url: str
        The web address with the requested information
    
    cache: dict
        The saved cache

    Returns
    -------
    dict
        
    '''
    if url in cache:
        print("Using Cache")
        return cache[url]
    
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]


def create_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from the NUFORC Report Index by State/Province

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is the name of a state, value is a url
    '''
    

    report_index_url = 'http://www.nuforc.org/webreports/ndxloc.html'
    response = requests.get(report_index_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    state_list_div = soup.find('table')
    state_table = state_list_div.find('tbody', recursive=False)
    state_items = state_table.find_all('tr', recursive=False)

    state_url_dict= {}

    for state in state_items:
        state_name = state.find('td')
        state_name_text = state_name.text.strip().lower()
        page_link_tag =state.find('a')
        state_page_path = page_link_tag['href']
        state_page_url = BASE_URL + state_page_path
        state_url_dict[state_name_text] = state_page_url
        
    return state_url_dict


def get_report_data_by_state(site_url):
    '''Makes a list of report instances from a state page index.
    
    Parameters
    ----------
    site_url: string
        The URL for a state index page
    
    Returns
    -------
    instance
        a report instance
    '''

    url_text = url_request_with_cache(site_url, CACHE_DICT)     
    soup = BeautifulSoup(url_text, 'html.parser') 

    table = soup.find('table')
    table_data = table.find('tbody', recursive=False)
    table_rows = table_data.find_all('tr', recursive=False)
    
    reports_list = []

    for row in table_rows:
        report_info_dict = {}
        date_time_cell = row.find_all('td')[0]
        date_time = date_time_cell.text.strip()
        try:
            date_time = date_time.split()
            date = str(date_time[0])
            time = str(date_time[1])
        except IndexError:
            date = str(date_time)
        city_cell = row.find_all('td')[1]
        city = city_cell.text.strip()
        state_cell = row.find_all('td')[2]
        state = state_cell.text.strip()
        shape_cell = row.find_all('td')[3]
        shape = shape_cell.text.strip()

        report_info_dict['date'] = date
        report_info_dict['time'] = time
        report_info_dict['city'] = city
        report_info_dict['state'] = state
        report_info_dict['shape'] = shape
        reports_list.append(report_info_dict)

    init_reports_json = json.dumps(reports_list)
    reports_json = json.loads(init_reports_json)

    insert_reports_sql = '''
        INSERT INTO Reports
        VALUES (NULL, ?, ?, ?, ?) 
    '''
        ##ADD BACK QUESTION MARK FOR SHAPE WHEN REINSERTED

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    for r in reports_json:
        cur.execute(insert_reports_sql,
        [
            r['date'],
            r['time'],
            r['city'],
            r['state']
            #r['shape']
        ]
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    STATE_DICT = create_state_url_dict()
    CACHE_DICT = open_cache()

    create_db()

    get_report_data_by_state('http://www.nuforc.org/webreports/ndxlDE.html')


    # state_search = input("Enter the name of a state or 'quit': ").lower()

    # while True:
    #     if input == 'quit':
    #         exit()

    #     if state_search in STATE_DICT:
    #         state_url = STATE_DICT[state_search]
    #         sites = get_reports_for_state(state_url)
    #         print(sites)
    #         break

    #     else:
    #         user_input = input("Invalid entry. Please enter the name of a U.S. state (e.g. Connecticut or connecticut): ")


###datetime conversion:
# try:
#             date = datetime.strptime(date_str, '%m/%d/%y %H:%M')
#         except ValueError:
#             try:
#                 date = datetime.strptime(date_str, '%m/%d/%y')
#             except ValueError:
#                 try:
#                     date = datetime.strptime(date_str, '%m/%d/%Y %H:%M')
#                 except ValueError:
#                     try:
#                         date = datetime.strptime(date_str, '%m/%d/%Y')
#                     except ValueError:
#                         print("ERROR")