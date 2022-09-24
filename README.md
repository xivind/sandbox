# Background
The code in this repo is meant for experimenting and learning basic programming, with emphasis on containers, messagebrokers, data visualisation and git as a bonus. Some of the sources that are used are [strava.com](https://www.strava.com), [fitbit.com](https://www.fitbit.com), [yr.no](https://www.yr.no) and [nilu.no](https://www.nilu.no). Some of the products that are used to handle data from those sources are Docker, InfluxDB, MariaDB, MQTT and Grafana. InfluxDB and MariaDB are used to store the data. MQTT is used to move data across the containers. The scripts that interacts with the data sources are all python. Everything runs in docker containers.

The code in this repo does not produce a complete system. Its more like a toolbox, and hopefully parts and bits of the code samples here can be useful for others.

More documentation on the different code snippets can be found in the sub catalogues. Currently there are code examples for:
- [Pimoroni Blinkt!](/blinkt/)
- [Strava](/strava/)
- [Fitbit](/fitbit/)
- [Nilu](/nilu/)
- [Yr](/yr/)
- [Brønnøysund Enhetsregisteret](/br_enhetsregisteret/)
- [Grafana](/grafana/)
- [MariaDB](/mariadb/)

**All comments, suggestions and pull requests to improve the code is very welcome, see open issues. Please note that this is a learning effort, so expect many strange choices and errors in the code, waiting to be corrected**