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

from bokeh.palettes import Plasma256

from bokeh.plotting import figure, show
from bokeh.io import output_file, show, output_notebook, push_notebook, curdoc
from bokeh.models import CategoricalColorMapper, HoverTool, ColumnDataSource, Panel, Plot, LinearAxis, Grid
from bokeh.layouts import column


from bokeh.models.widgets import CheckboxGroup, Slider, RangeSlider, Tabs, TextAreaInput, TableColumn, DataTable,DateFormatter, TextInput, Panel, Select

from bokeh.layouts import column, row, WidgetBox
from bokeh.palettes import Category20_16, Category20_20
import colorcet as cc
import matplotlib as plt

from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.models.glyphs import MultiLine
from bokeh.models.widgets import Paragraph


def graph():

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

        xs=[]
        ys=[]
        colors=[]
        labels=[]
    
        client=DataFrameClient(host=L_influx[3],port=L_influx[4], username=L_influx[1], password=L_influx[2])
        client.switch_database(L_influx[0])
        
        #Granularity to avoid to display too much points on the figure
        end=datetime.strptime(text_input_end, "%Y-%m-%d %H:%M:%S")
        start=datetime.strptime(text_input_start, "%Y-%m-%d %H:%M:%S")
        ecartSecondes=(end-start).total_seconds()
     
        if ecartSecondes < 86401:
            groupby=None
        elif ecartSecondes > 86401 and ecartSecondes < 5000000:
            groupby='1m'
        elif ecartSecondes > 5000000  and ecartSecondes < 77000000:
            groupby='15m'
        else:
            groupby='1h'
            
        #print(ecartSecondes, groupby)
        
        #Construction of vectors x and y for each register to be displayed
        for elt in capteur_list:
            
            if groupby==None:
                requete = "SELECT " + '"'+ elt + '"'+ " FROM measure WHERE time >= " + "'" + text_input_start + "'" + " AND " + "time <= " + "'" + text_input_end + "'" + " AND " + "ID=" + "'" + nom_capteur + "'" 
                datasets=client.query(requete)
                df=pd.DataFrame(datasets['measure'])
                df=df.rename_axis('Date')
                df.index=df.index.astype('datetime64[ns]')

                client.close()

                #Convert data in list of lists
                a=[]
                b=[]
                for i in range(df.shape[0]):
                    a.append(df[elt][i])
                    b.append(df.index[i])
                xs.append(a)
                ys.append(b)    

                colors.append(capteur_color[capteur_list.index(elt)])
          
                labels.append(elt)

            else:
                requete = "SELECT MEAN(" + '"'+ elt + '"'+ ") FROM measure WHERE time >= " + "'" + text_input_start +"'" + " AND " + "time <= " + "'" + text_input_end + "'" + " AND " + "ID=" + "'" + nom_capteur + "'" + " GROUP BY time(" + groupby + ") fill(0)"
                datasets=client.query(requete)
                df=pd.DataFrame(datasets['measure'])
                df=df.rename_axis('Date')
                df.index=df.index.astype('datetime64[ns]')

                client.close()

                #Conversion des données en liste de liste
                a=[]
                b=[]
                for i in range(df.shape[0]):
                    a.append(df['mean'][i])
                    b.append(df.index[i])
                xs.append(a)
                ys.append(b)    

                colors.append(capteur_color[capteur_list.index(elt)])
    

                labels.append(elt)

        #Construction of the source of the figure
        new_src = ColumnDataSource(data={'x': xs, 'y': ys,'color': colors, 'label': labels})

        return new_src
    
    
    def make_plot(src):
        # Blank plot with correct labels
        p = figure(plot_width = 1000, plot_height = 700, 
                   title = 'Graph of the registers', x_axis_type="datetime", 
                   x_axis_label = 'Date', y_axis_label = 'Unit', output_backend='webgl')
        
        
        p.multi_line('y', 'x', color = 'color', legend = 'label', 
                     line_width = 3,
                     source = src)
        
        # Hover tool with next line policy
        hover = HoverTool(tooltips=[('Capteur', '@label')],line_policy = 'next')
        
        # Add the hover tool and styling
        p.add_tools(hover)
        
        # Styling
        p = style(p)

        return p
   

    # Update function takes three default parameters
    def update(attr, old, new):
        #clear_plot(old)
        
        # Get the list of carriers for the graph
        capteur_to_plot = [capteur_selection.labels[i] for i in 
                            capteur_selection.active]
        
        l=text_input.value
        L_text=[]
        for val in l.split('\n'):
            L_text.append(val)

        text_input_start=L_text[1]
        text_input_end=L_text[4]

        nom_capteur=select.value
        
        # Make a new dataset based on the selected sensors
        new_src = make_dataset(capteur_to_plot,text_input_start,text_input_end, nom_capteur, L_influx)
        
    
        # Update the source used the quad glpyhs
        src.data.update(new_src.data)
        
        
    def style(p):
        # Title 
        p.title.align = 'center'
        p.title.text_font_size = '20pt'
        p.title.text_font = 'serif'

        # Axis titles
        p.xaxis.axis_label_text_font_size = '14pt'
        p.xaxis.axis_label_text_font_style = 'bold'
        p.yaxis.axis_label_text_font_size = '14pt'
        p.yaxis.axis_label_text_font_style = 'bold'

        # Tick labels
        p.xaxis.major_label_text_font_size = '12pt'
        p.yaxis.major_label_text_font_size = '12pt'
        
        return p
    
    #Select 
    """
    WARNING : you need to change the path to your config file to run this code
    """
    (available_name, available_capteur, L_influx) = reading_config("/home/rsm/Desktop/Arnaud_Debar/bokehapp_final/config/config.yml")
    select = Select(title="Select one sensor:", value=available_name[0], options=available_name)
    select.on_change('value',update)
    

    available_capteur.sort()
    
    #capteur_color=Category20_20
    capteur_color=[]
    for val in cc.glasbey_hv:
        capteur_color.append(plt.colors.to_hex(val))
    #capteur_color.sort()
    
    #Capteur to plot
    capteur_selection = CheckboxGroup(labels=available_capteur, active = [0, 1])
    capteur_selection.on_change('active', update)
    
    #Date input
    text_input = TextAreaInput(value='Start:\n2019-08-08 18:20:00\n  \nEnd:\n2019-08-09 10:27:00\n ', rows=5, title="Date: Year-Month-Day Hour:Minute:Second")
    text_input.on_change('value', update)

    
    l=text_input.value
    L_text_input=[]
    for val in l.split('\n'):
        L_text_input.append(val)
        
    initial_text_input_start=L_text_input[1]
    initial_text_input_end=L_text_input[4]

    #Initial register display
    initial_capteur = [capteur_selection.labels[i] for i in capteur_selection.active]
    
    #Make the initial dataset
    src = make_dataset(initial_capteur,initial_text_input_start,initial_text_input_end, available_name[0], L_influx)
    
    #Make the plot
    p = make_plot(src)
    
    # Add style to the plot
    p = style(p)
    
    # Put control in a single element
    controls = WidgetBox(select,capteur_selection,text_input)
    
    layout = row(controls, p)
    
    tab = Panel(child = layout, title = 'Summary Graph')

    return tab

