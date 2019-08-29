# Peper project - Bokeh app linked to a InfluxDB database

This code has been developed during the summer 2019 as part of the [Peper](https://dataia.eu/recherche/le-projet-peper-prediction-de-la-prosommation-denergie-renouvelable) project. This code provides a graphical interface thanks to the interactive vizualization library [Bokeh](https://bokeh.pydata.org/en/latest/).
The data are time-series data which come from eGauge sensors and are stored in a InfluxDB database. The bokeh app performs requests on the database to produce plots and tables. 

This app is divided in 2 pages:
- The first one consists of a Datatable. On the right side a drop-down menu allows to select wich eGauge sensor you want to choose. Then you can chose which register of the sensor you want to display and also the time interval, ie the starting and ending dates. A button allows to download the displayed data in CSV format 

![new_capture_donwload](https://user-images.githubusercontent.com/52416887/63927725-90604980-ca4e-11e9-913d-c97b78e60e35.png)

- The second one has a plot. Like in the fisrt page you have the possibility to choose: the sensor, the register and the time interval.  

![readme_screenshot_plot](https://user-images.githubusercontent.com/52416887/62783112-00b52400-babc-11e9-9de6-e96e6565cb6e.png)

## Demo


## Getting started

Things you need to install before running the code

### Bokeh

You need to install the bokeh library to be able to display the graphical interface
If you are already using Anaconda you can simply run
```
$ conda install bokeh
```
Or if you don't have Anaconda you can use the pip command
```
$ pip install bokeh
```

### Configuration file

This project use as input a configuration file in YML.
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
  Rue: 5 rue Pierre,
  Registre: [CT15_Amperage, CT14_Amperage, CT13_Amperage, CT12_Amperage, CT11_Amperage, CT10_Amperage, CT9_Amperage, CT8_Amperage, CT7_Amperage, CT6_Amperage, CT5_Amperage, CT4_Amperage, CT3_Amperage, CT2_Amperage, CT1_Amperage, TEST_YK, L1_Voltage,  L2_Voltage, L3_Voltage]
 }

database:
 database: {
  name: Essai ,
  port: 8086 ,
  ip: localhost ,
  username: admin_influx,
  password: admin
 }
 
```

There are two parts in this configuration : 
- One part is about your sensors, the two main components are the name of your sensor and the registers which correspond to the FIELD keys in the influxDB database. The name of the sensor is use as the main TAG to make the request on the database and make the difference between various sensors. The other components (iplocal, GPS ...) are also used as TAGS in the InfluxDB database to distinguish between several eGauge sensors. There are not used in this code but you can need it if you want to change SELECT requests and use one of this TAGS rather than the name of the sensor.
- The second part is about your database. You just have to put the name of the database, the port, the ip_address and also the username and the associated password

Once you have modified your configuration file, you need to change the path to your configuration file in the python code. See the 'WARNING' comment at the end of the python code (line 227)


## Start the program

You need to change directory to be on the directory which contains your *bokehapp* folder with the main function, the scripts folder, the Folder_CSV and the config folder (in the example below the bokeh app is located under /path/to/your/project_Peper/bokehapp). Then run a bokeh serve command to launch your python program. A web page at the address localhost:5006/bokehapp should open and you can interract with it (changing the FIELD, the time interval ...)

```
$ cd /path/to/your/project_Peper 
$ bokeh serve --show bokehappy
```

Good luck with the implementation. Feel free to contact me if there is any issues


## License

[![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](http://badges.mit-license.org)

- **[MIT license](http://opensource.org/licenses/mit-license.php)**



