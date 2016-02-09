# -*- coding: utf-8-*-
# Based on script v1.6.2 by Chopper_Rob:https://www.chopperrob.nl/domoticz/5-report-devices-online-status-to-domoticz
# Version: 1.0
import re
import urllib2
import json
import base64

DEBUG = False

WORDS = [
    "LIGHT", "LIGHTS",
    "THERMOSTAT", "TEMPERATURE", "HUMIDITY", 
    "SCENE", "GROUP", "ROOM", "MODE"
]

def handle(text, mic, profile):
    """
        Responds to user-input, typically speech text, with the result of
        a command given by the user to control devices, scenes and/or groups
        in different rooms through the Domoticz JSON API.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., Domoticz
                   server address, username and password)
        
        Returns:
        The result of a command issued to Domoticz through Jasper
    """
    def get_credentials():
        """
            Get the server, username and password from profile

            Returns:
            Server url and encoded credentials for Domoticz server
        """
        server = profile['domoticz']['server']
        username = profile['domoticz']['username']
        password =  profile['domoticz']['password']
        encoded_creds = encode_credentials(username, password)
        return server, encoded_creds

    def encode_credentials(username, password):
        """
            Encode the credentials into a base64 encoded string

            Arguments:
            username -- a username for the Domoticz server
            password -- a password corresponding to the username

            Returns:
            Encoded string of credentials
        """
        return base64.encodestring('%s:%s' % (username, password)).replace('\n', '')

    def send_request(url):
        """
            Sends a json request to the Domoticz server
            The request is appended to the server url and
            the encoded credentials are added to the header

            Arguments:
            url -- json url which request a json object

            Returns:
            Response to json request
        """
        server, encoded_creds = get_credentials()
        request = urllib2.Request(server + url)
        request.add_header("Authorization", "Basic %s" % encoded_creds)
        response = urllib2.urlopen(request)
        return response.read()

    def get_json_obj(type, arg):
        """
            Gets a json object from a json url

            Arguments:
            type -- type of json request
            arg -- additional settings for json request

            Returns:
            If response from send_request() contains field
            `result`, `results` is returned, else None is returned
            If an invalid json request was made, an error is raised.
        """
        url = '/json.htm?type=' + type + arg
        if DEBUG: print url
        obj = json.loads(send_request(url))
        if not is_status_ok(obj):
            raise Error('Object not retrieved from Domoticz')
        if 'result' in obj:
            return obj['result']

    def is_status_ok(obj):
        """
            Check if json object was properly retrieved

            Arguments:
            obj -- json object to check

            Returns:
            Boolean result of status check 
        """
        return obj['status'] == 'OK'

    def send_command(param, arg):
        """
            Send a command to the Domoticz server

            Arguments:
            param -- parameters of the command
            arg -- additional settings for the command

            Returns:
            Result of get_json_obj() of type `command`
        """
        return get_json_obj('command', '&param=' + param + arg)

    def send_light_command(idx, cmd):
        """
            Send a light command to the Domoticz server

            Arguments:
            idx -- index of light to command
            cmd -- switch command ['on', 'off', 'toggle']
            
        """
        send_command('switchlight', '&idx=' + idx + '&switchcmd=' + cmd.title())

    def send_thermostat_command(idx, sp):
        """
            Send a thermostat command to the Domoticz server

            Arguments:
            idx -- index of thermostat to command
            sp -- new setpoint of thermostat
            
        """
        send_command('setsetpoint', '&idx=' + idx + '&setpoint=' + sp)

    def send_scene_command(idx, cmd):
        """
            Send a scene/group command to the Domoticz server
            Scenes can only be turned on but devices in 
            scenes can have mixed states. Groups can be toggled
            nut all devices in the group have the same state.
            
            Arguments:
            idx -- index of scene/group to command
            cmd -- scene/group command ['on', 'off']
        """
        send_command('switchscene', '&idx=' + idx + '&switchcmd=' + cmd.title())

    def get_rooms(order='name', used='true'):
        """
            Returns a list of all roomplans

            Arguments:
            order -- sort by order
            used -- currently active

            Returns:
            List of all roomplans
        """
        return get_json_obj('plans', '&order=' + order + '&used=' + used)

    def get_scenes():
        """
            Returns a list of all scenes/groups

            Returns:
            List of all scenes/groups
        """
        return get_json_obj('scenes', '')

    def get_device(idx):
        """
            Returns json data for specific device

            Arguments:
            idx -- index of device

            Returns:
            json data for device
        """
        return get_json_obj('devices', '&rid=' + idx)

    def get_devices(filter='all', used='true', order='Name'):
        """
            Returns a list of all devices

            Arguments:
            filter -- filter by ['all', 'light', 'weather', 'temp', 'utility']
            used -- currently active
            order -- order devices by ['Name']

            Returns:
            List of all devices
        """
        return get_json_obj('devices', '&filter=' + filter + '&used=' + used + '&order=' + order)

    def get_devices_in_room(idx, filter='all'):
        """
            Returns a list of all devices in a roomplan

            Arguments:
            idx -- index of roomplans
            filter -- filter by ['all', 'light', 'weather', 'temp', 'utility']

            Returns:
            A list of all devices in room
        """
        return send_command('getplandevices', '&idx=' + idx + '&filter=' + filter)

    def get_devices_in_scene(idx, filter='all'):
        """
            Returns a list of all devices in a scene/group

            Arguments:
            idx -- index of scene/group
            filter -- filter by ['all', 'light', 'weather', 'temp', 'utility']

            Returns:
            A list of all devices in scene/group
        """
        return send_command('getscenedevices', '&idx=' + idx + '&isscene=true' + '&filter=' + filter)

    def get_lights():
        """
            Call to `get_devices()` with filter `light` 
            and returns a list of all lights

            Returns:
            A list of all lights
        """
        return get_devices(filter='light')

    def get_thermostats():
        """
            Calls get_devices() with filter `temp` to get all thermostats
            and `utility` to get all setpoints. If the `hardwarename` of
            thermostat and setpoint coincide then setpoint and its idx are
            added to the thermostat dictionary.
            
            Returns:
            Dictionary of thermostats
        """
        thermostats = get_devices('temp')
        setpoints = get_devices('utility')
        for thermostat in thermostats:
            for setpoint in setpoints: 
                if thermostat['HardwareName'] == setpoint['HardwareName']:
                    thermostat['SetPoint'] = setpoint['SetPoint']
                    thermostat['SetPointIdx'] = setpoint['idx']
        return thermostats

    def get_timers_in_scene(idx):
        return get_json_obj('scenetimers', '&idx' + idx)

    # Helper methods:
    def add_log_message(msg):
        """
            Adds a message in the Domoticz log

            Arguments:
            msg -- string to add as message
        """
        send_command('addlogmessage', '&message=' + msg)

    def get_sunrise_sunset():
        """
            Retrieve sun-rise/set times from Domoticz

            Returns:
            Dictionary of sun-rise/set times
        """
        return send_command('getSunRiseSet', '')
        
    def jsonprettyprint(obj):
        """
            Formats json object into human-readable print

            Arguments:
            obj -- json object to format

            Returns:
            String with pretty printed json object
        """
        return json.dumps(obj, sort_keys=True, 
                          indent=2, separators=(',', ': '))

    def timeit(ref_t=None):
        """
            Method to determine elapsed time between calls
            If reference time is provided, the elapsed time 
            since the reference time is printed.
            
            Arguments:
            ref_t -- reference time to calculate elapsed time

            Returns:
            Current time
        """
        import time
        t = time.time()
        # t = time.clock()
        if ref_t: print 'elapsed time:', t-ref_t
        return t
        
    # Methods used for testing/debugging:
    # currently not used directly but could be if desired
    def add_room(name):
        send_command('addplan', '&name=' + name)

    def delete_room(idx):
        send_command('deleteplan', '&idx=' + idx)

    def add_scene(name, group=False):
        get_json_obj('addscene', '&name=' + name + '&scenetype=' + str(int(group)))

    def delete_scene(idx):
        get_json_obj('deletescene', '&idx=' + idx)

    def add_device_to_scene(devidx, idx, group=False, cmd='on', 
                            lvl='100', hue='0', ondelay='', offdelay=''):
        send_command('addscenedevice', 
                     '&idx=' + idx + '&isscene=' + str(not group).lower() 
                     + '&devidx=' + devidx + '&command=' + cmd.title() 
                     + '&level=' + lvl + '&hue=' + hue + '&ondelay=' + ondelay 
                     + '&offdelay=' + offdelay)

    def delete_device_from_scene(idx):
        send_command('deletescenedevice', '&idx=' + idx)

    def add_timer_to_scene(idx, timertype, cmd, date='', hour='', min='', randomness='', level='', days='', active='true'):
        send_command('addscenetimer', 
                     '&idx=' + idx + '&active=' + active + '&timertype=' + timertype + 
                     '&date=' + date + '&hour=' + hour + '&min=' + min + 
                     '&randomness=' + randomness + '&command=' + cmd + 
                     '&level=' + level + '&days=' + days)

    # To-do: possible to refactor all device calls?
    def handle_device(device):
        pass
    
    def handle_devices():
        pass

    def handle_light(light):
        """
            Contains the logic to handle light switches.
            Switches can be `on`, `off`, or `toggled`.
            
            Usage: 
            'Turn on/off the test light'
            'Toggle the test light'

            Returns:
            The result of a `light` command issued to Domoticz through Jasper
        """
        lightname = light['Name'].lower()
        if lightname in text:
            idx = light['idx']
            type = light['idx'].lower() # `is` will fail as type is unicode type
            status = light['Status'].lower() # `is` will fail as type is unicode type
            if DEBUG: print 'name: ' + name + ', idx: ' + idx + \
                            ', type: ' + type + ', status: ' + status
            for command in ['on', 'off', 'toggle']:
                if command in text:
                    if command == status:
                        return "The %s light is already %s" % (lightname, command)
                    else:
                        send_light_command(idx, command)
                        if command is 'toggle':
                            return 'Toggling light'
                        else:
                            return 'Turning %s light %s' % (lightname, command)
            return 'I cannot execute that %s command' % type
        return None

    def handle_lights():
        """
            Wrapper function for `light` commands
            
            To-do: 
            performace  -- Improve by moving `get_devices()` out of handle call.
                           Alternatively, make `lights` global and have a function periodically update `lights`.
        """
        lights = get_lights()
        if lights:
            for light in lights:
                response = handle_light(light)
                if response: return response
            return 'That specific light is not defined'
        else:
            return 'There are no lights defined'

    def handle_thermostat(thermostat):
        """
            Contains the logic to handle the thermostat.
            Thermostat can be used to set or get temperature related settings.
            Currently only the Nest thermostat is implemented.
            
            Usage: 
            'Increase/decrease the temperature'
            'What is the temperature and humidity?'
            'What is the temperature in the living room?'

            To-do:
            implement -- home/away setting for thermostat
                      -- other thermostats beside Nest?

            Returns:
            The result of a `thermostat` command issued to Domoticz through Jasper
            
        """
        thermostatname = thermostat['Name']
        setpoint = thermostat['SetPoint']
        idx = thermostat['SetPointIdx']
        if any(word in text for word in ["up", "increase"]):
            sp = str(float(setpoint) + 1)
            send_thermostat_command(idx, sp)
            return "Increasing the temperature to %s." % sp
        elif any(word in text for word in ["down", "decrease"]):
            sp = str(float(setpoint) - 1)
            send_thermostat_command(idx, sp)
            return "Decreasing the temperature to %s." % sp
        elif any(word in text for word in ["what", "is", "temperature", "humidity"]):
            temp, humid = str(round(thermostat['Temp'],1)), str(thermostat['Humidity'])
            return "Inside the house, it is %s degrees celsius and %s percent humidity." % (temp, humid)
        else:
            return "I did not understand your thermostat command."

    def handle_thermostats():
        """
            Wrapper function for thermostat commands
            
            To-do: 
            implement -- multiple thermostat
        """
        thermostats = get_thermostats()
        if thermostats:
            for thermostat in thermostats:
                response = handle_thermostat(thermostat)
                if response: return response
            return 'That specific thermostat is not defined'
        else:
            return 'There are no thermostats defined'                     
                     

    def handle_scene(scene):
        """
            Contains the logic to handle scenes and groups. Scenes can only be activated but devices in the scene can have mixed states. Groups have an on/off state but all devices within the group have the same state.

            Usage: 
            'Activate the test scene'
            'Turn on/off the test group'
            'Deactivate the test group'

            Arguments:
            scene -- json object for scene

            Returns:
            The result of a `scene` command issued to Domoticz through Jasper
        """
        scenename = scene['Name'].lower()
        if scenename in text:
            idx = scene['idx']
            type = scene['Type'].lower()
            status = scene['Status'].lower()
            if DEBUG: print 'name: ' + scenename + ', idx: ' + idx + \
                            ', type: ' + type + ', status: ' + status
            for command in ['on', 'off', 'activate', 'deactivate']:
                if command in text:
                    if type == 'scene': 
                        if command in ['on', 'activate']:
                            send_scene_command(idx, 'on')
                            return 'Activating the %s %s' % (scenename, type)
                        else:
                            return 'I can only activate scenes.'
                    elif type == 'group':
                        command = 'on' if command in ['on', 'activate'] else 'off' 
                        if command == status:
                            return 'The %s %s is already %s' % (scenename, type, command)
                        else:
                            send_scene_command(idx, command)
                            return 'Switching %s the %s %s' % (command, scenename, type)
                    else:
                        return 'I cannot control %s types' % type
            return 'I cannot execute that %s command' % type
        return None

    def handle_scenes():
        """
            Wrapper function for scene commands

            To-do: 
            performance  -- Improve by moving `get_scenes()` out of handle call.
                            Alternatively, make `scenes` global and have a function periodically update `scenes`.
        """
        scenes = get_scenes()
        if scenes:
            for scene in scenes:
                response = handle_scene(scene)
                if response: return response
            return 'That specific scene or group is not defined'
        else:
            return 'There are no scenes or groups defined'                     
                     
    def handle_room(room):
        """
            Responds to user-input, typically speech text, with the result of
            a command given by the user to control devices, scenes and/or groups
            in different rooms through the Domoticz JSON API.

            Usage:

            To-do: 
            performance -- `get_devices_in_room()` is probably relatively costly.
            floorplans -- implement if requested

            Arguments:
            room - json object of room

            Returns:
            The result of a command issued to Domoticz through Jasper
        """
        roomname = room['Name'].lower()
        if roomname in text:
            idx = room['idx']
            devices = get_devices_in_room(idx)
            if DEBUG: print 'roomname: ' + roomname + ', idx: ' + idx + \
                            ', no. of devices in room: ' + len(devices)
            for device in devices:
                devname = device['Name'].lower()
                if devname in text:
                    idx = device['idx'].lower()
                    status = device['Status'].lower()
                    if DEBUG: print 'devname: ' + devname + ', idx: ' + idx + \
                                    ', status: ' + status
                    for command in ['on', 'off', 'toggle']:
                        if command in text:
                            if command == status:
                                return 'The %s device in the %s is already turned %s' % (devname, roomname, command)
                            else:
                                return 'Turning %s the %s device in the %s' % (command, devname, roomname)
                    return 'That command is undefined for device %s in the %s' % (devname, roomname)
            return 'That device is not defined in the %s' % roomname
        return None

    def handle_rooms():
        """
            Wrapper function for room commands

            To-do: 
            performance -- Improve by moving `get_rooms()` out of handle call.
                           Alternatively, make `rooms` etc. global and have a function periodically update `rooms` etc. 
        """
        rooms = get_rooms()
        if rooms:
            for room in rooms:
                response = handle_room(room)
                if response: return response
            return 'That specific room is not defined.'
        else:
            return 'There are no rooms defined.'

    text = text.lower().split()
    if any(word in text for word in ["room"]):
        response = handle_rooms()
    elif any(word in text for word in ["scene", "group", "mode"]):
        response = handle_scenes()
    elif any(word in text for word in ["light", "lights"]):
        response = handle_lights()
    elif any(word in text for word in ["temperature", "humidity", "thermostat"]):
        response = handle_thermostats()
    else:
        response = 'Your command is not defined in Domoticz'
    mic.say(response)

def isValid(text):
    """
        Returns True if the input is related to home automation.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return bool(re.search(r'\b(room|scene|group|mode|light|thermostat|temperature|humidity)\b', text, re.IGNORECASE))
