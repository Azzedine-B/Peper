import requests # library needed to make HTTP requests
import yaml
import pandas as pd
import numpy as np
from influxdb import InfluxDBClient, DataFrameClient
from lxml import etree # library needed to process xml files
from xml.etree import ElementTree
from datetime import datetime, time
import time

# database connection 
# return DataFrameClient object 
def dbConnexion(dbname, host='localhost', port=8086):
    exist = False # booleen allowing us to test the existing database
    client = InfluxDBClient(host=host, port=port)
    database_list = client.get_list_database() 
    for i in range(len(database_list)): 
        if(database_list[i]['name'] == dbname): # is this database in the list?
            exist = True # it is
    if(exist == False): # it's not
        client.create_database(dbname) # we create it
    client=DataFrameClient(host=host, port=port, database=dbname) # we use it as a DataFrameClient
    return client

def getInterval(dbname, host='localhost', port=8086):
    client = dbConnexion(dbname, host=host, port=port)
    query_body = 'SELECT last(Value) FROM \"measures\" ORDER BY time LIMIT 1'
    response = client.query(query_body, database='egauge')
    for name in response.keys():
        df_query_response = response[name]
    if(df_query_response.empty == False):
        interval = 301 # 5 minutes in seconds
    else:
        time_isoformat = str(df_query_response.index[0])
        last_timestamp = int(datetime.fromisoformat(time_isoformat).timestamp())
        current_time = int(time.time())
        interval = 2700 if current_time - last_timestamp > 2700 else current_time - last_timestamp # current_time - last_time_db greater than 45 minutes? the interval is equal to 45 minutes otherwise the interval
    return interval

# we get the xml data via an HTTP request
# n = {interval} means that we recover the last {interval} measurements per second
def getXMLTree(egaugeName, interval): 
    url = f'http://{egaugeName}.egaug.es/cgi-bin/egauge-show?S&s=0&n={interval}'
    res = requests.get(url)
    if(res == False):
        print("request error")
        return
    else:
        root = ElementTree.fromstring(res.content)
    return root

# convert hexadecimal to decimal
def getDecimalTimestamp(hexTimestamp):
    return int(hexTimestamp, 16)

def value_processing(line, columns, root):
    # we add the data without having done the operations beforehand
    data = root.find('data')
    timedelta = getDecimalTimestamp(data.get('time_delta')) 
    measures = np.zeros((line, columns))
    l = 0
    c = 0
    for register in root.iter('r'):
        for calculation in register.findall('c'):
            measures[l][c] = int(calculation.text)
            c = c + 1
        l = l + 1
        c = 0
    
    # we carry out the operations in order to have the right values
    for l in range(line - 1):
        for c in range(columns):
            measures[l][c] = (measures[l][c] - measures[l + 1][c]) / (timedelta * 1000)

    
    # we delete the last lines because we cannot retrieve its true value
    measures = np.delete(measures,(line-1),axis=0)
    
    return measures


def addPoints(dbname, egaugeName, host='localhost', port= 8086):
    
    interval = getInterval(dbname, host=host, port=port)
    root = getXMLTree(egaugeName, interval)

    list_ports = []
    measures_list = []
    for port in root.iter('cname'):
        list_ports.append(port.text)
        measures_list.append(port.get('t'))
    data = root.find('data')
    columns = int(data.get('columns'))
    timestamp = getDecimalTimestamp(data.get('time_stamp'))
    timedelta = getDecimalTimestamp(data.get('time_delta')) 
    epoch = getDecimalTimestamp(data.get('epoch'))

    line = 0
    for register in root.iter('r'):
        line = line + 1

    measures = value_processing(line, columns, root)

    # the different timestamps
    Date = [datetime.fromtimestamp(timestamp - (i * timedelta)) for i in range(0, line - 1)]


    try:
        client = dbConnexion(dbname, host='localhost', port=8086)
        print('succesfully connected')
    except:
        print('error when connecting to the database') # voir ce qu'on peux faire pour renvoyer l'exception

    for i in range(columns):
        df = pd.DataFrame()
        df['Date'] = Date
        df['Port'] = list_ports[i]
        df['Measure'] = measures_list[i]
        if(measures_list[i] == 'P'):
            measures[:,i] = measures[:,i] * 1000
        df[list_ports[i]] = measures[:,i]
    
        df = df.set_index('Date')
        
        try:
            client.write_points(df,'measures', tag_columns =['Port', 'Measure'], database='egauge')
            print('succesfully printed')
        except:
            print('error when writing points to the database')
    

def main():
    while(True):
        addPoints('egauge', 'egauge47536')
        time.sleep(5*60)

main()