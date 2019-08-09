#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 16:46:32 2019

@author: Arnaud DEBAR 
"""


import pandas as pd
import urllib.request
import webbrowser
from lxml import etree
import xml.etree.ElementTree as ET
import numpy as np
import time
from datetime import datetime
from influxdb import InfluxDBClient
from influxdb import DataFrameClient
import sys
import yaml
from threading import Timer
import datetime as dt

def reading_config(path):
    
    #Reading the configuration file
    file = open(path,"r") 

    dictio=yaml.full_load(file) 
    #dictio=yaml.load(file, Loader=yaml.FullLoader)

    file.close()
    
    #Exctraction of the sensors part and the database part
    dictio_sensors =dictio['sensors']
    dictio_database = dictio['database']
    
    #Transformation in DataFrame to allow an easy read
    df_sensors = pd.DataFrame(dictio_sensors)
    df_databases= pd.DataFrame(dictio_database)
    
    return(df_sensors,df_databases)
    
def data_sensors(L_init, L_influx):
    
    #Connect to InfluxDb
    client=InfluxDBClient(host=L_influx[3] ,port=L_influx[4], username=L_influx[1], password=L_influx[2])
    
    #Check if the Database exists, if not we create it. And the request is simply to get the last five minutes data
    if not ({'name': L_influx[0]} in client.get_list_database()):
        client.create_database(L_influx[0])
        requete = '-show?S&s=0&n=341'
    
    #If the Database already exists, we get the last timestamp in the database and fill the data from the last timestamp until the current time        
    else:
        client=DataFrameClient(host=L_influx[3] ,port=L_influx[4],username=L_influx[1], password=L_influx[2],database=L_influx[0])
        requete_base1="SHOW FIELD KEYS"
        datasets=client.query(requete_base1)
        df=pd.DataFrame(datasets['measure'])
        champ=df['fieldKey'][0]
        
        requete_base2="SELECT last("+ champ + ")FROM measure" + " WHERE " + "ID=" + "'" + L_init[0] + "'"
        datasets=client.query(requete_base2)
        df=pd.DataFrame(datasets['measure'])
        df=df.rename_axis('Date')
        df.index=df.index.astype('datetime64[ns]')
        last_date=str(df.index[0])
        last_date=datetime.strptime(last_date, "%Y-%m-%d %H:%M:%S")
        if((dt.datetime.now()-last_date).total_seconds())>2700:
            last_date=dt.datetime.now()-dt.timedelta(minutes=45)
        last_date=(time.mktime(last_date.timetuple()))
        last_date=int(last_date)
        last_date=str(last_date)
        #requete = '-show?S&s=0&n=10'
        requete='-show?S&s=0&t='+last_date
        
        
    eGauge = L_init[0]
    
    """
    URL creation
    WARNING : you need to change the part http://eGaugexxxx.egauge/es if you have change the basic url to access to you eGauge sensor.
    """
    url = "http://" + eGauge + ".egaug.es/cgi-bin/egauge" + requete

    #Data recovery
    html=urllib.request.urlopen(url)

    #XML tree recovery
    tree = ET.parse(html)

    #Root creation
    root=tree.getroot()

    data=tree.find('data')
    columns=data.get('columns')
    time_stamp=data.get('time_stamp')
    time_delta=data.get('time_delta')
    epoch=data.get('epoch')

    #Column names
    list_name=[]
    for name in root.iter('cname'):
        list_name.append(name.text)

    length=len(L_init)+1
    #Calculation of the number of values to be recovered
    l=0
    for tstep in root.iter('r'):
        l=l+1

    #List containing the raw values
    list_value=np.zeros((l,int(columns)+length))
    i=0
    j=length
    for tstep in root.iter('r'):
        for c in tstep.findall('c'):
            list_value[i,j]=c.text
            j=j+1
        i=i+1
        j=length

    #Recovery of values in Rate-of-Change-Unit
    time_stamp_dec=time_stamp[2:]
    time_stamp_dec=int(time_stamp_dec,16)

    time_delta_dec=int(time_delta)


    (lig,col)=np.shape(list_value)


    for l in range(lig-1):
        for c in range(length,col):
            list_value[l,c]=(list_value[l,c]-list_value[l+1,c])/(time_delta_dec*1000)

    list_value=np.delete(list_value,(lig-1),axis=0)

    Date=[datetime.fromtimestamp(time_stamp_dec - i*time_delta_dec) for i in range(0,lig-1)]

    return(list_value,list_name,col,lig,Date)


def multiple_storage(L_init, L_influx):

    #Get the Data to store   
    (list_value,list_name,col,lig,Date)=data_sensors(L_init,L_influx)
    
    #Creation of one list with the register names and antoher one with the corresponding units 
    list_registre=L_init[len(L_init)-1]
    list_registre_name=[]
    list_registre_unit=[]
    length=len(L_init)+1
    for val in list_registre:
        caractere = "="
        x=val.split(caractere)
        list_registre_name.append(x[0])
        list_registre_unit.append(x[1])
        
 
    #Loop over all registers
    for indice in range(length,col):
        
        capteur=list_value[:,indice]
        nulle=list_value[:,:length]
        #print(capteur)
        #print(nulle)
        list_capteur=np.column_stack((nulle,capteur))
        
        #list_capteur=list_capteur.reshape(10,1)
        
        name=list_name[indice-length]
        indice_unit=list_registre_name.index(name)

        if list_registre_unit[indice_unit]=='W':
            list_capteur[:,-1]=list_capteur[:,-1]*1000
        """
        WARNING : you can remove TAGS you don't need just below. You also have to modify the loop_function and remove the lines with TAGS you don't 		want to use
        """

        L=['Date', 'ID','IP','GPS_lat','GPS_long','Ville','CP','Rue','Unit']
        L=L+[list_name[indice-length]]

        ID=[L_init[0] for i in range(0,lig-1)]
        IP=[L_init[1] for i in range(0,lig-1)]
        GPS_lat=[L_init[2] for i in range(0,lig-1)]
        GPS_long=[L_init[3] for i in range(0,lig-1)]
        Ville=[L_init[4] for i in range(0,lig-1)]
        CP=[L_init[5] for i in range(0,lig-1)]
        Rue=[L_init[6] for i in range(0,lig-1)]
        Unit=[list_registre_unit[indice_unit] for i in range(0, lig-1)]
        
     
        df=pd.DataFrame(list_capteur, columns=L)

        df['Date']=Date
        df['ID']=ID
        df['IP']=IP
        df['GPS_lat']=GPS_lat
        df['GPS_long']=GPS_long
        df['Ville']=Ville
        df['CP']=CP
        df['Rue']=Rue
        df['Unit']=Unit
        
        df=df.set_index('Date')
    
        #Connexion and insertion in the database
        client=InfluxDBClient(host=L_influx[3] ,port=L_influx[4], username=L_influx[1], password=L_influx[2])
    
        if not ({'name': L_influx[0]} in client.get_list_database()):
            client.create_database(L_influx[0])
    
        client=DataFrameClient(host=L_influx[3] ,port=L_influx[4],username=L_influx[1], password=L_influx[2],database=L_influx[0])

        try:
            client.write_points(df,'measure',tag_columns=['ID','IP','GPS_lat','GPS_long','Ville','CP','Rue','Unit'],database=L_influx[0])
        except:
            print('Erreur dans l\'insertion des données dans la base InfluxDB')

    client.close()
            
def loop_function(path):
    
    (df_sensors,df_databases)=reading_config(path)
    
    for i in range(0, df_sensors.shape[1]):
        L=[]
        L_influx=[]
        L.append(df_sensors.loc['name'][i])
        L.append(df_sensors.loc['iplocal'][i])
        L.append(df_sensors.loc['GPS_lat'][i])
        L.append(df_sensors.loc['GPS_long'][i])
        L.append(df_sensors.loc['Ville'][i])
        L.append(df_sensors.loc['CP'][i])
        L.append(df_sensors.loc['Rue'][i])
        L.append(df_sensors.loc['Registre'][i])
         
        L_influx.append(df_databases.loc['name'][i])
        L_influx.append(df_databases.loc['identifiant'][i])
        L_influx.append(df_databases.loc['mdp'][i])
        L_influx.append(df_databases.loc['ip'][i])
        L_influx.append(df_databases.loc['port'][i])
        multiple_storage(L, L_influx)


def get_next_5min(dtime=None):
    dtime=dt.datetime.now()
    
    time_delta=dt.timedelta(minutes=5)
    
    return(dtime+time_delta)
    
def main():
    while True:
        #print('insertion  ', dt.datetime.now())
        """
        WARNING : you need to change the path to your own configuration file
        """
        loop_function("/home/rsm/Desktop/Arnaud_Debar/eGauge_code_final/config.yml")
        
        next_hour=get_next_5min(dt.datetime.now())
        
        while (time.time() < next_hour.timestamp()):
            time.sleep(1)
            
        assert abs((next_hour - dt.datetime.now()).total_seconds()) < 10
        
main()
