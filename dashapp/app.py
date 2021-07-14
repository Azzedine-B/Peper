# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd
import yaml
from influxdb import InfluxDBClient, DataFrameClient
import plotly.express as px
from datetime import datetime
from dash.exceptions import PreventUpdate


def config_file_to_tabs(path):    
    with open(path, "r") as file: 
        config = yaml.full_load(file) # convert yaml file to python dictionary

    # converting the dictionary to DataFrame for better handling
    df_sensors = pd.DataFrame(config['sensors'])
    df_database = pd.DataFrame(config['database'])

    # creation of two tables which will allow us to use them in the program
    sensors_number = len(df_sensors.columns)
    databases_number = len(df_database.columns)
    t_sensors = [[None]] * sensors_number
    t_databases = [[None]] * databases_number
    for i in range(sensors_number):
        t_sensors[i][i] = df_sensors.loc["name"][i] # t_sensors[i][i] = ... is suppressing the None value 
        t_sensors[i].append(df_sensors.loc["iplocal"][i])
        t_sensors[i].append(df_sensors.loc["Registre"][i])


    for i in range(databases_number):
        t_databases[i][i] = df_database.loc["name"][i]
        t_databases[i].append(df_database.loc["port"][i])
        t_databases[i].append(df_database.loc["ip"][i])
        t_databases[i].append(df_database.loc["identifiant"][i])
        t_databases[i].append(df_database.loc["mdp"][i])
    

    return t_sensors, t_databases

def get_dropdown_labels(t_sensors):
    # t_sensors, t_databases = config_file_to_tabs(path)
    list_dict_sensor_names = []
    dict_register_names = {}
    for i in range(len(t_sensors)):
        list_dict_sensor_names.append({'label': t_sensors[i][0], 'value' : t_sensors[i][0]})
        register_names = t_sensors[i][2]
        dict_register_names[t_sensors[i][0]] = []
        for j in range(len(register_names)):
            dict_register_names[t_sensors[i][0]].append({'label': register_names[j], 'value': register_names[j]})
    return list_dict_sensor_names, dict_register_names

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

def app_creation(path):
    t_sensors, t_databases = config_file_to_tabs(path)
    list_dict_sensor_names, dict_register_names = get_dropdown_labels(t_sensors)
    
    app = dash.Dash()

    app.layout = html.Div(children=[
        html.H1(children='''
                Registers Graphics
                ''',
                style={'textAlign' : 'center'}
        ),
        html.Label([
                'Sensor(s) :',
                dcc.Dropdown(
                    id='sensors_dropdown',
                    options=list_dict_sensor_names,
                    placeholder="Select a sensor ...",
                    style={'marginBottom' : '8px'},
                )
        ]),
        html.Label([
                'Register(s) : ',
                dcc.Dropdown(
                    id='registers_dropdown',
                    multi=True, 
                    placeholder="Select one or more registers ..."
                )        
        ]),
        html.Br(),
        html.Label([
                'Start : ',
                dcc.Input(
                    id='input_start',
                    type="text",
                    placeholder="YYYY-MM-DD HH:MM:SS",
                    style={'marginRight' : '20px'}
                )
        ]),
        html.Label([
                'End : ',
                dcc.Input(
                    id="input_end",
                    type="text",
                    placeholder="YYYY-MM-DD HH:MM:SS"
                )
        ]),
        dcc.Graph(
            id='register_graph'
        )
    ])

    @app.callback(
        Output(component_id='register_graph', component_property='figure'),
        Input(component_id='registers_dropdown', component_property='value'),
        Input(component_id='input_start', component_property='value'),
        Input(component_id='input_end', component_property='value')
    )
    def update_output_div(registers_dropdown_value,input_start_value, input_end_value):
        if registers_dropdown_value is None or registers_dropdown_value == []: 
            raise PreventUpdate
        else:
            df_tab = [] # store all the df for each register
            client = dbConnexion(t_databases[0][0])
            for register in registers_dropdown_value:
                query_text = f"SELECT \"{register}\" FROM measures WHERE TIME >= '{input_start_value}' AND TIME <= '{input_end_value}'"
                try:
                    response = client.query(query_text)
                except:
                    raise PreventUpdate
                df_tab.append(response.get('measures'))
            for df in df_tab:
                if(df is None):
                    raise PreventUpdate
                else:
                    final_df = df_tab[0] # we take the first df to merge it to the other
                    for i in range(1,len(df_tab)):
                        final_df = df_tab[i].merge(final_df, left_index=True, right_index=True)
                    fig = px.line(final_df, labels=dict(value='Unit', index='Date'))
                    return fig

    @app.callback(
        Output(component_id='registers_dropdown', component_property='options'),
        Input(component_id='sensors_dropdown', component_property='value')
    )
    def update_register_dropdown(sensor_value):
        if sensor_value is None:
            raise PreventUpdate
        else:
            return dict_register_names[sensor_value]


    if __name__ == '__main__':
        app.run_server(debug=False)


app_creation('./config_dash.yml')
