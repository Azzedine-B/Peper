# Peper

Theses codes have been developed during the summer 2019 as part of the [Peper](https://dataia.eu/recherche/le-projet-peper-prediction-de-la-prosommation-denergie-renouvelable) project. The objective of the project is to collect relevant data on the different actors of the electricity network, and to use learning techniques to develop algorithms for predicting the production and consumption of each actor. 

Therefore one part of the project is to collect electricity data consumption in several buildings. The first Python code collects data from [eGauge](https://www.egauge.net/) sensors and stored them in an [InfluxDB](https://docs.influxdata.com/influxdb/v1.7/) database. The second one offers a graphical interface to display and download in CSV format the data stored in the database. Please see the Readme file of each code for more information.
