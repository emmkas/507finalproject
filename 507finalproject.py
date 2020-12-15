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
import plotly.graph_objs as go
from collections import Counter


BASE_URL = 'http://www.nuforc.org/webreports/'
TYPE_DATA_URL = 'http://www.nuforc.org/webreports/ndxshape.html' 
CACHE_FILENAME = "nuforc_cache.json"
CACHE_DICT = {}
STATE_DICT = {"Alabama":"AL", "Alaska":"AK", "Arizona":"AZ", "Arkansas":"AR", "California":"CA", "Colorado":"CO","Connecticut":"CT", "Delaware":"DE", "District of Columbia":"DC", "Florida":"FL", "Georgia":"GA", "Hawaii":"HI", "Idaho":"ID", "Illinois":"IL", "Indiana":"IN", "Iowa":"IA", "Kansas":"KS", "Kentucky":"KY", "Louisiana":"LA", "Maine":"ME", "Maryland":"MD", "Massachusetts":"MA", "Minnesota":"MN", "Michigan":"MI", "Mississippi":"MS", "Missouri":"MO", "Montana":"MT", "Nebraska":"NE", "Nevada":"NV", "New Hampshire":"NH", "New Jersey":"NJ", "New Mexico":"NM", "New York":"NY", "North Carolina":"NC", "North Dakota":"ND", "Ohio":"OH", "Oklahoma":"OK", "Oregon":"OR", "Pennsylvania":"PA", "Rhode Island":"RI", "South Carolina":"SC", "South Dakota":"SD", "Tennessee":"TN", "Texas":"TX", "Utah":"UT", "Vermont":"VT", "Virginia":"VA", "Washington":"WA", "West Virginia":"WV", "Wisconsin":"WI", "Wyoming":"WY"}
DATABASE = 'NUFORC_Data.sqlite'

def create_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    drop_reports_sql = 'DROP TABLE IF EXISTS "Reports"'

    drop_ufos_sql = 'DROP TABLE IF EXISTS "UFO_Types"'

    create_reports_sql = '''
        CREATE TABLE IF NOT EXISTS "Reports" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Date" DATE,
            "Time" TIME (0),
            "City" TEXT NOT NULL,
            "State" TEXT NOT NULL,
            "UFOTypeId" INTEGER
        )
    '''

    create_ufos_sql = '''
        CREATE TABLE IF NOT EXISTS "UFO_Types" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Shape" TEXT
        )
    '''
    cur.execute(drop_reports_sql)
    cur.execute(drop_ufos_sql)
    cur.execute(create_ufos_sql)
    cur.execute(create_reports_sql)
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

def get_ufo_type_data(site_url):
    '''Populates a SQL table with HTML data from the NUFORC Report Index by Shape of Craft.
    
    Parameters
    ----------
    site_url: string
        The URL for the page listing UFO shapes
    
    Returns
    -------
    none
    '''

    url_text = url_request_with_cache(site_url, CACHE_DICT)     
    soup = BeautifulSoup(url_text, 'html.parser') 

    table = soup.find('table')
    table_data = table.find('tbody', recursive=False)
    table_rows = table_data.find_all('tr', recursive=False)
    
    ufos_list = []

    for row in table_rows:
        ufo_type_dict = {}
        shape_cell = row.find_all('td')[0]
        shape = shape_cell.text.strip()
        ufo_type_dict['shape'] = shape
        ufos_list.append(ufo_type_dict)

    init_ufos_json = json.dumps(ufos_list)
    ufos_json = json.loads(init_ufos_json)

    insert_ufos_sql = '''
        INSERT INTO UFO_Types
        VALUES (NULL, ?) 
    '''

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    for u in ufos_json:
        cur.execute(insert_ufos_sql,
        [
            u['shape']
        ]
        )

    conn.commit()
    conn.close()


def get_report_data_by_state(site_url):
    '''Populates a SQL table with HTML data from the NUFORC Report Index by State/Province.
    
    Parameters
    ----------
    site_url: string
        The URL for a state index page
    
    Returns
    -------
    none
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
            date_time.strip('[]')
            try:
                date_time.strip()
            except:
                continue
        except:
            continue
        try:
            date_time = date_time.split()
            date = str(date_time[0])
            time = str(date_time[1])
            try:
                date.strip('[]')
            except:
                continue
            try:
                date.replace("'", "")
            except:
                continue
            try:
                date.strip()
            except:
                continue
        except IndexError:
            try:
                date = str(date_time).strip('[]')
            except:
                date = str(date_time).strip()
            try:
                date.replace("'", "")
            except:
                date = str(date_time).strip()
        try:
            if str(date)[0].isdigit():
                date = date
            else:
                date = None
        except:
            continue
        try:
            if str(time)[0].isdigit():
                time = time
            else:
                time = None
        except:
            continue

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

    select_ufotypeid_sql = '''
        SELECT Id FROM UFO_Types
        WHERE Shape = ?
    '''

    insert_reports_sql = '''
        INSERT INTO Reports
        VALUES (NULL, ?, ?, ?, ?, ?) 
    '''

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    for r in reports_json:
        try:
            cur.execute(select_ufotypeid_sql, [r['shape']])
            shape_id = cur.fetchone()[0]
        except TypeError:
            shape_id=None

        cur.execute(insert_reports_sql,
        [
            r['date'],
            r['time'],
            r['city'],
            r['state'],
            shape_id
        ])

    conn.commit()
    conn.close()


def add_records_to_db():
    baseurl = (BASE_URL + 'ndxl')

    state_list = []
    for i in STATE_DICT.values():
        state_list.append(i)
    
    for s in state_list:
        page_url = (baseurl + s + ".html")
        get_report_data_by_state(page_url)
        time.sleep(10)


if __name__ == "__main__":
    # CACHE_DICT = open_cache()
    # create_db()
    # get_ufo_type_data(TYPE_DATA_URL)
    # add_records_to_db()

    print('\nWelcome!') 
    print('\nThis program pulls data from the National UFO Report Center to display information about UFO sightings across the United States.\n')

    searchable_dict = {k.lower(): v for k, v in STATE_DICT.items()}

    while True:
        user_input = input("\nEnter the name of a state to see data for UFO reports in that area, or 'quit' to exit the program: ").lower()

        if user_input == 'quit':
            exit()

        if user_input in searchable_dict:
            state_abbr = searchable_dict[user_input]
            connection = sqlite3.connect(DATABASE)
            cur = connection.cursor()
            result = cur.execute("SELECT Date, City FROM Reports WHERE State=? AND Date IS NOT NULL ORDER BY Id DESC", (state_abbr,)).fetchall()
            connection.close()

            all_date_data = []
            all_town_data = []

            for r in result:
                date = r[0]
                all_date_data.append(date)
                town = r[1]
                all_town_data.append(town)

            date_report_count_dict = Counter(all_date_data)
            dates_count = []
            for i in date_report_count_dict.values():
                dates_count.append(i)

            town_report_count_dict = Counter(all_town_data)
            towns_count = []
            for i in town_report_count_dict.values():
                towns_count.append(i)

            dates = list(dict.fromkeys(all_date_data))
            towns = list(dict.fromkeys(all_town_data))

            display_input = input("\nWould you like to see this data sorted by date or by city? Enter 'date' or 'city': ")

            if user_input == 'quit':
                exit()
        
            if display_input == "date":
                year_input = input("\nEnter a four-digit year (after 1940): ")[-2:]
                year_data = []
                for d in dates:
                    if d[-2:]==year_input:
                        year_data.append(d)

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    mode='markers',
                    x=year_data, 
                    y=dates_count,
                    marker={'symbol':'circle', 'size':12, 'color':'blue'}
                    )
                )
                    
                fig.update_layout(
                    title=("UFO Reports by Date in " + user_input.title()),
                    xaxis_title="Date",
                    yaxis_title="Number of Reports",
                    xaxis_range=[(year_input + '-01-01'),(year_input + '-12-31')],
                    font=dict(
                        family="Courier New, monospace",
                        size=14,
                        color="Black")
                    )
                
                ## The following code is from a Plotly example: https://plotly.com/python/time-series/
                fig.update_xaxes(
                    rangeslider_visible=True,
                    tickformatstops = [
                        dict(dtickrange=[86400000, 604800000], value="%e. %b d"),
                        dict(dtickrange=[604800000, "M1"], value="%e. %b w"),
                        dict(dtickrange=["M1", "M12"], value="%b '%y M"),
                        dict(dtickrange=["M12", None], value="%Y Y")]
                )
                ##
                
                fig.show()

            if display_input == "city":
                town_data = []
                for t in towns:
                    shortened_name = (t[:15] + '...') if len(t) > 15 else t
                    town_data.append(str(shortened_name).title())
                
                town_data.sort()

                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    mode="markers",
                    x=town_data, 
                    y=dates_count,
                    marker={'symbol':'circle', 'size':12, 'color':'green'}
                    )
                )
                    
                fig.update_layout(
                    title=("UFO Reports by Date in " + user_input.title()),
                    xaxis_title="City",
                    yaxis_title="Number of Reports",
                    font=dict(
                        family="Courier New, monospace",
                        size=14,
                        color="Black"),
                    margin=dict(
                        l=50,
                        r=50,
                        b=100
                    )
                    )

                # The following code is from a Plotly example: https://plotly.com/python/time-series/
                fig.update_xaxes(
                    rangeslider_visible=True,
                    tickformatstops = [
                        dict(dtickrange=[86400000, 604800000], value="%e. %b d"),
                        dict(dtickrange=[604800000, "M1"], value="%e. %b w"),
                        dict(dtickrange=["M1", "M12"], value="%b '%y M"),
                        dict(dtickrange=["M12", None], value="%Y Y")]
                )
                #
                
                fig.show()

        else:
            user_input = input("\nInvalid entry. Please enter the name of a U.S. state (e.g. Connecticut or connecticut), or 'quit': ")
            if user_input == 'quit':
                exit() 
        
        continue