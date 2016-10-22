#Jasper-Domoticz
[Domoticz](https://domoticz.com/) home automation module for [Jasper](http://jasperproject.github.io/).
Allows the ability to command devices, scenes and groups individually or per roomplan through the Domoticz JSON [API](https://www.domoticz.com/wiki/Domoticz_API/JSON_URL's).

###Steps to install Jasper-Domoticz:
- Make sure the Domoticz server is running by going to the `server_url`,
e.g. `https://server_ip` or `http://server_ip:port`.
- Add the Domoticz server url, username and password to `profile.yml`:
```
domoticz:
  server: <server_url>
  username: <username>
  password: <password>
```
- Download Jasper-Domoticz:
```
cd <path to jasper/client/modules>
git clone https://github.com/nlooije/Jasper-Domoticz.git .
```
You have installed the Domoticz module for Jasper!

###Usage:
Assuming a dinnertable light, a movie scene, a night group and
a thermostat are defined in Domoticz, the following commands can be issued:
```
YOU: Turn on the dinnertable light
JASPER: Turning dinnertable light on
YOU: Turn off the dinnertable light
JASPER: Turning dinnertable light off
YOU: Activate movie mode
JASPER: Activating the movie scene
YOU: Activate the night group
JASPER: Switching on the night group
YOU: Activate the night group
JASPER: The night group is already on
YOU: What is the current temperature?
JASPER: Inside the house, it is 19.3 degrees celsius and 46 percent humidity
YOU: Increase the temperature
JASPER: Increasing the temperature to 20.3
```

##To-do:
- [ ] write unittests
- [ ] implement other devices
- [ ] improve performance of json calls to Domoticz
- [ ] refactor to generalize device calls
- [ ] refactor thermostat calls

##Contributions from the following people:
```
```
