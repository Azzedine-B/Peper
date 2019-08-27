#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 16:46:32 2019

@author: Arnaud DEBAR 
"""

import pandas as pd
import webbrowser
import numpy as np
import time
import yaml
from datetime import datetime
from influxdb import InfluxDBClient
from influxdb import DataFrameClient
from threading import Timer
from os.path import dirname, join
from bokeh.palettes import Plasma256

from bokeh.plotting import figure, show
from bokeh.io import output_file, show, output_notebook, push_notebook, curdoc
from bokeh.models import CategoricalColorMapper, HoverTool, ColumnDataSource, Panel, Plot, LinearAxis, Grid,CustomJS
from bokeh.layouts import column


from bokeh.models.widgets import CheckboxGroup, Slider, RangeSlider, Tabs, Button, TextAreaInput, TableColumn, DataTable,DateFormatter, TextInput, Panel, Select, NumberFormatter

from bokeh.layouts import column, row, WidgetBox
from bokeh.palettes import Category20_16, Category20_20

from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.models.glyphs import MultiLine
from bokeh.models.widgets import Paragraph
from bokeh.models import CDSView, IndexFilter


def table():
    
    def reading_config(path):

        #Reading the configuration file
        file = open(path,"r") 

        #dictio=yaml.full_load(file) 
        dictio=yaml.load(file, Loader=yaml.FullLoader)

        file.close()

        #Exctraction of the sensors part and the database part
        dictio_sensors =dictio['sensors']
        dictio_database = dictio['database']

        #Transformation in DataFrame to allow an easy read
        df_sensors = pd.DataFrame(dictio_sensors)
        df_databases= pd.DataFrame(dictio_database)

        list_sensor_name=[]
        for i in range(0, df_sensors.shape[1]):
            list_sensor_name.append(df_sensors.loc['name_sensor'][i])
        
        L=[]
        L.append(df_sensors.loc['Registre'][0])
            
        list_registre_name=L[len(L)-1]
            
        L_influx=[]    
        L_influx.append(df_databases.loc['name'][i])
        L_influx.append(df_databases.loc['username'][i])
        L_influx.append(df_databases.loc['password'][i])
        L_influx.append(df_databases.loc['ip'][i])
        L_influx.append(df_databases.loc['port'][i])
            
        return(list_sensor_name, list_registre_name, L_influx)
    

    
    def make_dataset(capteur_list,text_input_start,text_input_end,nom_capteur, L_influx):
        
        client=DataFrameClient(host=L_influx[3],port=L_influx[4], username=L_influx[1], password=L_influx[2])
        client.switch_database(L_influx[0])

        src=pd.DataFrame()
        
        for elt in capteur_list:
            requete = "SELECT " +  '"'+ elt + '"'+ " FROM measure WHERE time >= " + "'" + text_input_start + "'" + " AND " + "time <= " + "'" + text_input_end + "'" + " AND " + "ID=" + "'" + nom_capteur + "'"
            datasets=client.query(requete)
            df=pd.DataFrame(datasets['measure'])
            df=df.rename_axis('Date')
            df.index=df.index.astype('datetime64[ns]')
            src=pd.concat([df, src], axis = 1)

        client.close()
        src['Date']=src.index
        Index=[i for i in range(0, df.shape[0])]
        src.index=Index
        
        cols = src.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        src = src[cols]
        
        return(src)

    
    def make_table(source,src):
        table_columns =[TableColumn(field='Date', title='Date',formatter=DateFormatter(format="%m/%d/%Y %H:%M:%S"))]
        colonne=src.columns
        colonne=colonne.delete(0)
        table_columns += [TableColumn(field=col, title=col) for col in colonne]
        liste=[k for k in range(0,10)]
        longueur= src.shape[0]
        for k in range(longueur-10, longueur):
            liste.append(k)
    
        view1 = CDSView(source=source, filters=[IndexFilter(indices=liste)])
        #table_source = ColumnDataSource(src)
        datatable = DataTable(source=source,
                               columns=table_columns,
                               width=1200,
                               height=1000, view=view1)

        #print(datatable.fit_columns)
        return datatable
   

    # Update function takes three default parameters
    def update(attr, old, new):
        

        capteur_to_plot = [capteur_selection.labels[i] for i in 
                            capteur_selection.active]
        l=text_input.value
        L_text=[]
        for val in l.split('\n'):
            L_text.append(val)

        text_input_start=L_text[1]
        text_input_end=L_text[4]

        nom_capteur=select.value
        
        new_src = make_dataset(capteur_to_plot, text_input_start,text_input_end, nom_capteur, L_influx)
        new_source = ColumnDataSource(new_src)
        dictio={}
        for i in range(0,len(new_src.columns)):
            dictio[new_src.columns[i]]=new_src[new_src.columns[i]]
            
        source.data=dictio
        
        
        table_columns =[TableColumn(field='Date', title='Date',formatter=DateFormatter(format="%m/%d/%Y %H:%M:%S"))]
        colonne=new_src.columns
        colonne=colonne.delete(0)
        table_columns += [TableColumn(field=col, title=col) for col in colonne]
        datatable.columns = table_columns
        
        liste=[k for k in range(0,10)]
        longueur= new_src.shape[0]
        for k in range(longueur-10, longueur):
            liste.append(k)
        view1 = CDSView(source=new_source, filters=[IndexFilter(indices=liste)])
        datatable.view=view1
        
    #Select
    """
    WARNING : you need to change the path to your config file to run this code
    """
    (available_name, available_capteur, L_influx) = reading_config("/home/rsm/Desktop/bokehapp_final/config/config.yml")
    select = Select(title="Select one sensor:", value=available_name[0], options=available_name)
    select.on_change('value',update)
    
    available_capteur.sort()
    
    
    #Capteur to plot
    capteur_selection = CheckboxGroup(labels=available_capteur, active = [0])
    capteur_selection.on_change('active', update)
    

    text_input = TextAreaInput(value='Start:\n2019-08-08 18:20:00\n  \nEnd:\n2019-08-08 18:27:00\n ', rows=5, title="Date: Year-Month-Day Hour:Minute:Second")
    text_input.on_change('value', update)
    

    
    initial_capteur = [capteur_selection.labels[i] for i in capteur_selection.active]
    l=text_input.value
    L_text_input=[]
    for val in l.split('\n'):
        L_text_input.append(val)
        
    initial_text_input_start=L_text_input[1]
    initial_text_input_end=L_text_input[4]
    
    
    src = make_dataset(initial_capteur, initial_text_input_start, initial_text_input_end, available_name[0], L_influx)
    source = ColumnDataSource(src)
    #Make the plot
    datatable = make_table(source,src)
    
    #a=source.column_names
    #a=src.to_dict('series')
    #print(a)
    
    #Download part
    button = Button(label='Download', button_type='success')
    button.callback = CustomJS(args=dict(source=source), code=open(join(dirname(__file__), "download.js")).read())
    #text_banner = Paragraph(text='To download the displayed data, please indicate the name you want to give to the file in the box below. The file will be automatically created in CSV format in the "Folder_CSV" folder as soon as you click on the "Download" button', width=250, height=130)
    #path_input=TextInput(value="Name", title="Name of the file :")
    
    # Put control in a single element
    controls = WidgetBox(select, capteur_selection,text_input,button)
    
    layout = row(controls, datatable)
    
    tab = Panel(child = layout, title = 'Summary Table')

    return tab
