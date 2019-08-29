# Peper project - eGauge data recovery and storage in InfluxDB database

This code has been developed during the summer 2019 as part of the [Peper](https://dataia.eu/recherche/le-projet-peper-prediction-de-la-prosommation-denergie-renouvelable) project. This code performs request(s) on one or several eGauge sensors every 5min. After collecting this time-series data, those are pushed into an InfluxDB database in order to store them. 

## Getting started

Things you need to install before running the code

### Installing InfluxDB


InfluxDB is a database spezialised to store time-series data. 

You need to install the influxDB database in order to properly running the code. Please find the installation instructions to perform on your computer on this link : [Installing InfluxDB](https://docs.influxdata.com/influxdb/v1.7/introduction/installation/)

After installing the database you need to create a user with all the privileges on the database. See [Authentification and authorization](https://docs.influxdata.com/influxdb/v1.7/administration/authentication_and_authorization/) or the example below.
In my code, I choose to call this user "admin_influx" with a password "admin". If you choose another name or another password, you just have to change it in the configuration file (see next section).

```
$ influx
Connected to http://localhost:8086 version1.7.6
InfluxDB shell version: 1.7.6
Enter an InfluxQL query

> CREATE DATABASE Peper
> Use Peper
> CREATE USER admin_influx with PASSWORD 'admin' WITH ALL PRIVILEGES
```

Then you need to change the HTTP configuration of your influxdb database. In Linux this file is located under the path /etc/influxdb/influxdb.conf. Open this file with a text editor and go to the http part to modify the file like the below screenshot. You have to replace the IP address '157.159.124.184' by your IP address or if you only want to run the program locally just put ':8086' or '127.0.0.1:8086'. You also have to modify the configuration file with your ip adress or with localhost (see next section).

![readme_screen](https://user-images.githubusercontent.com/52416887/62783181-26422d80-babc-11e9-9add-e95af5c4e123.png)

### Configuration file

This project uses as input a configuration file in YML.
You can see an example below :

```
sensors:
 sensor1: {
  name: eGaugexxxxx ,
  iplocal: xxx.xxx.xxx.xxx ,
  GPS_lat: xx ,
  GPS_long: xx ,
  Ville: Paris ,
  CP: 75000 ,
  Rue: 5 rue Pieerre,
  Registre: [CT15_Amperage=A, CT14_Amperage=A, CT13_Amperage=A, CT12_Amperage=A, CT11_Amperage=A, CT10_Amperage=A, CT9_Amperage=A, CT8_Amperage=A, CT7_Amperage=A, CT6_Amperage=A, CT5_Amperage=A, CT4_Amperage=A, CT3_Amperage=A, CT2_Amperage=A, CT1_Amperage=A, TEST_YK=P, L1_Voltage=V,  L2_Voltage=V, L3_Voltage=V]
 }

database:
 database: {
  name: Essai ,
  port: 8086 ,
  ip: localhost ,
  identifiant: admin_influx,
  mdp: admin
 }
```
There are two parts in this configuration : 
- One part is about your sensor(s), the two main components are the name of your eGauge which is needed to make the XML request and the registers which are present in your eGauge. For the registers, I choose the format 'name_of_the_register=unit_of_the_register', so you have to put them in this way. The other components (iplocal, GPS ...) are used as TAGS in the InfluxDB database to distinguish between several eGauge sensors. You can remove them in the config file but then you also have to remove them in the python code (see 'WARNING' comment in the function *multiple_storage*).
- The second part is about your database. You just have to put the name of the database, the port, the ip_address and also the id and the associated password

Once you have modified your configuration file, you need to change the path to your configuration file in the python code. See the 'WARNING' comment in the function *main()*


## How it works : code explanations


This python code is composed of several functions
- **reading_config** : this function is in charge to load the configuration file and return two Panda DataFrames including information about the sensors and the database
- **Loop_function** : this function takes as input the path to the YML config file and produces the two DataFrames thanks to the function reading_config. Then the function loops over all eGauge : For each sensor two lists are build linked to the IDs of the eGauge and to the database and the function multiple_storage is called to allow the storage of the data in InfluxDB
- **data_sensors** : the purpose of this function is to make the API request on the sensor, recover the XML file, parse it and give a Dataframe as output. One thing to notice is the format of the request. The URL to access my eGauge was *http://eGaugeName.egauge.es/*  In case you decide to choose another address than the basic one, just change this part and keep the request after the new IP address (see 'WARNING' comment in the function *data_sensorse*). An example of request is : */cgi-bin/egauge-show?S&s=0&n=300* This request will display the values over the last 5min with a step of one second. If you need to change the request refer to the 
[eGauge API XML manual](https://www.egauge.net/media/support/docs/egauge-xml-api.pdf)
- **multiple_storage** : this function aims to store the sensor values in the Database. For that, it retrieves the DataFrame containing the values of the sensor thanks to the function data_sensors and stores this DataFrame in the influxDB database.

**Main()** : the purpose of the main function is to get the current time and run insertions in the database every 5 min thanks to the previous functions.

## Forever : run the program continuously

The purpose of our program is to run insertions of the eGauge values every 5min in the InfluxDB database over a long time period. I choose to install a CLI tool to ensure that our script will run continuously (and not be interrupted by some internet microswitch-off ...) : [forever](https://www.npmjs.com/package/forever). 
To install this CLI you need first to install node.js 

```
$ sudo apt-get install -y nodejs npm
$ [sudo] npm install forever -g
```
Then you need to change directory to be on your project's path and run a forever command to launch your python program. The program will be continuously executed and automatically restarted in case of any failure error.

```
$ cd /path/to/your/project_Peper
$ forever start -c python3 Peper_project_final.py
```


Good luck with the implementation. Feel free to contact me if there is any issues


## License

[![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](http://badges.mit-license.org)

- **[MIT license](http://opensource.org/licenses/mit-license.php)**






