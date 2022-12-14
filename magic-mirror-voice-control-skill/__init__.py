from adapt.intent import IntentBuilder
from mycroft import intent_handler
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

import os
from os.path import dirname, join
import requests
import ipaddress
import json
import datetime
import re
import time
import mycroft.version
from threading import Thread, Lock
from mycroft.messagebus.client import MessageBusClient
from mycroft.messagebus.message import Message
from mycroft.util.log import LOG
from mycroft.tts import TTS
from mycroft.client.speech.listener import RecognizerLoop

from .googleCal import addEvent, defaultFormat, deleteEvent

LOGGER = getLogger(__name__)

class MagicMirrorVoiceControlSkill(MycroftSkill):

    def __init__(self):
        super(MagicMirrorVoiceControlSkill, self).__init__(name="MagicMirrorVoiceControlSkill")

    def initialize(self):
        self.url = 'http://0.0.0.0:8080/remote'
        self.voiceurl ='http://0.0.0.0:8080/kalliope'
        self.mycroft_utterance=''
        self.moduleData = ''
        self.connectionStatus = ''
        self.kalliopeStatus = ''
        self.ipAddress = ''
        self._dir = '/opt/mycroft/skills/magic-mirror-voice-control-skill'
 
        # In this project is used localhost as default IP address
        try:
            ipAddress = '127.0.0.1'
            self.ipAddress = ipAddress
            self.url = 'http://' + ipAddress + ':8080/remote'
            self.voiceurl = 'http://' + ipAddress + ':8080/kalliope'
            self.mycroft_utterance = ''
            payload = {'action': 'MODULE_DATA'}
            # Following line of code requests the module data so Mycroft knows which modules are installed
            # If the MagicMirror is not reached, this request will cause an exception
            r = requests.get(url=self.url, params=payload)
            data = r.json()

            # Open a list of Available Modules. (This should be updated occasionally based on new available modules)
            # Submit a PR if you'd like me to add new modules to the 'AvailableModules.json'
            with open (join(self._dir, 'AvailableModules.json')) as f:
                AvailableData = json.load(f)

            # Check to see which of the Available Modules have an 'identifier' by checking the 'data' requested from the mirror.
            # Modules with 'identifiers' are installed and configured in the MagicMirror's config.js. As new modules are added to the
            # config.js, module identifiers may change. If you add new modules to the MagicMirror, this skill needs to be restarted
            # to update the module identifiers or odd things are possible
            for moduleData in AvailableData['moduleData']:
                for item in data['moduleData']:
                    if moduleData['name'] == item['name']:
                        moduleData['identifier'] = item['identifier']
            self.moduleData = AvailableData

            # Added code to see if kalliope module is installed. if not, there is no need to send events to kalliope module
            data = self.moduleData
            for moduleData in data['moduleData']:
                mycroftname = moduleData['mycroftname']
                identifier = moduleData['identifier']
                if mycroftname == 'kalliope':
                    if identifier != '':
                        self.kalliopeStatus = 'installed'
                    else:
                        self.kalliopeStatus = 'not installed'
            # Set connection status to connected and inform the user
            self.connectionStatus = 'connected'
            self.speak('I have successfully connected to the magic mirror.')

        except requests.exceptions.ConnectionError:
            # If the connection error is because the ip address has not changed from the default
            if ipAddress == '0.0.0.0':
                self.connectionStatus = 'disconnected'
                self.speak('I was unable to connect to the magic mirror at the default ip address. To activate the magic-mirror-voice-control-skill I need to know the I P address of the magic mirror. What is the I P address of the magic mirror you would like to control with your voice?', expect_response=True)

            else:
                self.connectionStatus = 'disconnected'
                self.speak_dialog('notConnected')

        except IOError:
            self.connectionStatus = 'disconnected'
            self.speak('To activate the magic-mirror-voice-control-skill I need to know the I P address of the magic mirror. What is the I P address of the magic mirror you would like to control with your voice', expect_response=True)

        self.add_event('recognizer_loop:wakeword', self.handle_listen)
        self.add_event('recognizer_loop:utterance', self.handle_utterance)
        self.add_event('speak', self.handle_speak)
        self.add_event('recognizer_loop:audio_output_start', self.handle_output)
        self.add_event('recognizer_loop:audio_output_end', self.handle_output_end)

    def handle_listen(self, message):
        if self.connectionStatus == 'connected':
            if self.kalliopeStatus == 'installed':
                voice_payload = {"notification":"KALLIOPE", "payload": "Listening"}
                r = requests.post(url=self.voiceurl, data=voice_payload)

    def handle_utterance(self, message):
        if self.connectionStatus == 'connected':
            if self.kalliopeStatus == 'installed':
                utterance = message.data.get('utterances')
                voice_payload = {"notification":"KALLIOPE", "payload": utterance}
                r = requests.post(url=self.voiceurl, data=voice_payload)

    def handle_speak(self, message):
        if self.connectionStatus == 'connected':
            if self.kalliopeStatus == 'installed':
                self.mycroft_utterance = message.data.get('utterance')
                voice_payload = {"notification":"KALLIOPE", "payload": self.mycroft_utterance}
                r = requests.post(url=self.voiceurl, data=voice_payload)

    def handle_output(self, message):
        if self.connectionStatus == 'connected':
            if self.kalliopeStatus == 'installed':
                voice_payload = {"notification":"KALLIOPE", "payload": self.mycroft_utterance}

    def handle_output_end(self, message):
        if self.connectionStatus == 'connected':
            if self.kalliopeStatus == 'installed':
                voice_payload = {"notification":"REMOVE_MESSAGE", "payload": "REMOVE_MESSAGE"}
                r = requests.post(url=self.voiceurl, data=voice_payload)

    def handle_not_connected(self):
        if self.ipAddress == '0.0.0.0':
            self.speak('I was unable to connect to the magic mirror at the default ip address. To activate the magic-mirror-voice-control-skill I need to know the I P address of the magic mirror. What is the I P address of the magic mirror you would like to control with your voice?', expect_response=True)

        else:
            self.speak_dialog('notConnected')

# The following intent handler is used to set the ip address of the MagicMirror by saving it to a file ip.json
# The file is saved into the skill's directory which causes Mycroft to reload the skill. After the skill reloads
# the above initialize self code will find the ip.json file and load the MagicMirror ip address. If it is not the
# correct address, or if the MagicMirror is not accessible the initilize self code will prompt the user to check the ip address

    @intent_handler(IntentBuilder('SetMirrorIpAddress').require('SetIpKeywords').optionally('IpAddress'))
    def handle_Set_Ip_command(self, message):
        keywords = message.data.get('SetIpKeywords')
        utterance = message.data['utterance']
        utterance = utterance.replace(keywords, '')
        utterance = utterance.replace(' ', '')
        self.speak('I am setting the I P address to {}'.format(utterance))
        try:
            ipaddress.ip_address(utterance)
            ip = {'ipAddress': utterance}
        except:
            self.speak('Im sorry that is not a valid ip address. please try again', expect_response=True)

# This code builds the SystemActionIntent which are commands that are not directed at a specific module

    @intent_handler(IntentBuilder('SystemActionIntent').require('SystemActionKeywords').require('SystemKeywords'))
    def handle_System_command(self, message):
        if self.connectionStatus == 'connected':

            system_action = message.data.get('SystemActionKeywords')
            if system_action in ('hide', 'conceal'):
                system_action = 'HIDE'
            if system_action in ('show', 'display'):
                system_action = 'SHOW'

            System = message.data.get('SystemKeywords')

    # This part of the SystemActionIntent handles one word remote System actions like shutdown, reboot, restart, refresh and update
    # if commands do not make sense as far as 'raspberry pi', 'pi', 'mirror', 'screen',
    # errors will result in mycroft asking the user to rephrase

            if System in ('raspberry pi', 'pi', 'mirror', 'screen'):
                if system_action in ('shutdown', 'reboot', 'restart', 'refresh', 'update', 'save'):
                    system_action = system_action.upper() # MMM-Remote-Control wants actions in uppercase
                    payload = {'action': system_action}
                if system_action == 'turn off':
                    if System in ('raspberry pi', 'pi'):
                        system_action = 'SHUTDOWN'
                        payload = {'action': system_action}
                if System in ('raspberry pi', 'pi'):
                    if system_action in ('turn on', 'SHOW', 'HIDE', 'save'):
                        self.speak_dialog('incorrectCommand', expect_response=True)

    # This part of the SystemActionIntent turns on/off the monitor

            if System in ('monitor', 'mirror', 'screen', 'modules'):
                if system_action in ('turn on','wake up', 'SHOW'):
                    system_action = 'MONITORON'
                    payload = {'action': system_action}
                if system_action in ('turn off', 'go to sleep', 'HIDE'):
                    system_action = 'MONITOROFF'
                    payload = {'action': system_action}

    # This part of the SystemActionIntent will show/hide neewsfeed article details.
    # It defaults to hide article details

            if System == 'article details':
                if system_action in ('SHOW', 'turn on', 'refresh'):
                    system_action = 'NOTIFICATION'
                    System = 'ARTICLE_MORE_DETAILS'
                else:
                    system_action = 'NOTIFICATION'
                    System = 'ARTICLE_LESS_DETAILS'
                payload = {'action': system_action, 'notification': System}

            r = requests.get(url=self.url, params=payload)
            status = r.json()
            self.speak_dialog('success')
        else:
            self.handle_not_connected()

# This intent will have mycroft read the installed modules 'mycroftname' so that the user knows which mdules are installed

    @intent_handler(IntentBuilder('ListInstalledModulesIntent').require('ListInstalledKeywords').require('SingleModuleKeywords'))
    def handle_list_installed_modules_command(self, message):
        if self.connectionStatus == 'connected':
            data = self.moduleData
            installed_modules = ''
            for moduleData in data['moduleData']:
                mycroftname = moduleData['mycroftname']
                identifier = moduleData['identifier']
                if identifier != "":
                    installed_modules = installed_modules + ', ' + mycroftname
            self.speak('The currently installed modules are{}'.format(installed_modules))
        else:
            self.handle_not_connected()

# This intent handles change page commands to be used with the MMM-pages module. The MMM-pages module must be installed
# for this intent to work. Find it on github @ https://github.com/edward-shen/MMM-pages

    @intent_handler(IntentBuilder('ChangePagesIntent').require('PageActionKeywords').require('PageKeywords'))
    def handle_change_pages_command(self, message):
        if self.connectionStatus == 'connected':
            page = message.data.get('PageKeywords')
            if page in ('one', '1', 'home'):
                integer = 0
            if page in ('two', '2'):
                integer = 1
            if page in ('three', '3'):
                integer = 2
            if page in ('four', '4', 'for'):
                integer = 3
            if page in ('five', '5'):
                integer = 4
            if page in ('six', '6'):
                integer = 5
            if page in ('seven', '7'):
                integer = 6
            if page in ('eight', '8'):
                integer = 7
            if page in ('nine', '9'):
                integer = 8
            if page in ('ten', '10'):
                integer = 9
            notification = 'PAGE_CHANGED'
            action = 'NOTIFICATION'
            payload = {'action': action, 'notification': notification, 'payload': integer}
            r = requests.get(url=self.url, params=payload)
            status = r.json()
            self.speak_dialog('success')
        else:
            self.handle_not_connected()

# This intent handles swipe commands to be used with the MMM-pages module. The MMM-pages module must be installed
# for the swipe intent to work. Find it on github @ https://github.com/edward-shen/MMM-pages

    @intent_handler(IntentBuilder('HandleSwipeIntent').require('SwipeActionKeywords').require('LeftRightKeywords'))
    def handle_pages_command(self, message):
        if self.connectionStatus == 'connected':
            direction = message.data.get('LeftRightKeywords')
            if direction == 'right':
                System = 'PAGE_DECREMENT'
            if direction == 'left':
                System = 'PAGE_INCREMENT'
            action = 'NOTIFICATION'
            payload = {'action': action, 'notification': System}
            r = requests.get(url=self.url, params=payload)
            self.speak_dialog('success')
        else:
            self.handle_not_connected()

# This intent handles a number of different user utterances for the brightness value, including
# numbers, numbers followed by %, numbers as words, numbers as words including the word percent.
# Not all references need to include (%|percent), this can be a value between 10 - 200

    @intent_handler(IntentBuilder('AdjustBrightnessIntent').require('BrightnessActionKeywords').require('BrightnessValueKeywords'))
    def handle_adjust_brightness_command(self, message):
        if self.connectionStatus == 'connected':
            action = 'BRIGHTNESS'
            value = message.data.get('BrightnessValueKeywords')
            value_without_spaces = value.replace(' ', '')
            iswords = str.isalpha(value_without_spaces)
            # Sometimes Mycroft recognizes numbers as words, if that is the case, this code recognizes the words and looks
            # in the 'numberwords.json' file for the corresponding number value. It also checks to see if the user uttered
            # the word 'percent' and handles adjusting the value as a percentage.
            if iswords == True:
                percent_present = re.search('percent', value)
                if percent_present is not None:
                    value = value.replace(' percent', '')
                    with open(join(self._dir, 'numberwords.json')) as f:
                        data = json.load(f)
                        for item in data['numberwords']:
                            if value == item['word']:
                                value = item['number']
                                break
                    value = ((value/100)*200)
                else:
                    # If the user does not use the word percent, and Mycroft recognized the numbers as words.
                    with open(join(self._dir, 'numberwords.json')) as f:
                        data = json.load(f)
                        for item in data['numberwords']:
                            if value == item['word']:
                                value = item['number']
                                break

            else:
                # This else handles numbers including numbers with the '%' sign
                percent_present = (re.search('%', value))
                if percent_present is not None:
                    value = (re.sub('[%]', '', value))
                    value = int(value)
                    value = ((value/100)*200)
                    action = 'BRIGHTNESS'
                    if value < 10:
                        value = 10
                else:
                    value = int(value)
            payload = {'action': action, 'value': value}
            r = requests.get(url=self.url, params=payload)
            status = r.json()
            self.speak_dialog('success')
        else:
            self.handle_not_connected()

    # This intent handles commands directed at specific modules. Commands include: hide
    #  show, display, conceal, install, add, turn on, turn off, update.

    @intent_handler(IntentBuilder('ModuleActionIntent').require('ModuleActionKeywords').require('ModuleKeywords'))
    def handle_module_command(self, message):
        if self.connectionStatus == 'connected':
            module_action = message.data.get('ModuleActionKeywords')
            if module_action in ('hide', 'conceal', 'turn off'):
                module_action = 'HIDE'
            if module_action in ('show', 'display', 'turn on'):
                module_action = 'SHOW'

            module = message.data.get('ModuleKeywords')
            data = self.moduleData
            for item in data['moduleData']:
                if module == item['mycroftname']:
                    module_id = item['identifier']
                    module_url = item['URL']
                    module_name =item['name']

            if module_action in ('HIDE', 'SHOW'):
                module_action = module_action.upper()
                payload = {'action': module_action, 'module': module_id}
            if module_action in ('install', 'add'):
                module_action = 'INSTALL'
                payload = {'action': module_action, 'url': module_url}
            if module_action == 'update':
                module_action = module_action.upper()
                payload = {'action': module_action, 'module': module_name}

            r = requests.get(url=self.url, params=payload)
            status = r.json()
            self.speak_dialog('success')
        else:
            self.handle_not_connected()

    @intent_handler('AddEvent.intent')
    def handle_calendar_add_event(self, message):
        if self.connectionStatus == 'connected':      
            title = message.data.get('title')
            if title == None:
                self.speak('No title specified. Action dismissed.')
                return 0

            eventDate = message.data.get('date')
            if eventDate == 'today':
                eventDate = datetime.datetime.today().strftime('%Y-%m-%d')
            if eventDate == 'tomorrow':
                today = datetime.datetime.today()
                eventDate = today + datetime.timedelta(days=1)
                eventDate = datetime.datetime.strftime(eventDate, '%Y-%m-%d')
            startTime = message.data.get('start_time', '00:00').replace(' ', ':')
            endTime = message.data.get('end_time')
            try:
                start = defaultFormat(eventDate + ' ' + startTime + ':00')
                if endTime is None:
                    end = ''
                else:
                    end = defaultFormat(eventDate + ' ' + endTime + ':00')
            except ValueError:
                self.speak('Invalid date.')
                return 0

            description = message.data.get('description')
            if description is None:
                response = addEvent(title, start, end)
            else:
                response = addEvent(title, start, end, description)
            self.speak(response)
            time.sleep(6)
            # payload = {'action': 'UPDATE', 'notification': 'module_3_calendar'}
            payload = {'action': 'REFRESH'}
            r = requests.get(url=self.url, params=payload)
        else:
            self.handle_not_connected()

    @intent_handler('DeleteEvent.intent')
    def handle_calendar_delete_event(self, message):
        if self.connectionStatus == 'connected':      
            title = message.data.get('title')
            if title == None:
                self.speak('No title specified. Action dismissed.')
                return 0

            eventDate = message.data.get('date')
            if eventDate == 'today':
                eventDate = datetime.datetime.today().strftime('%Y-%m-%d')
            if eventDate == 'tomorrow':
                today = datetime.datetime.today()
                eventDate = today + datetime.timedelta(days=1)
                eventDate = datetime.datetime.strftime(eventDate, '%Y-%m-%d')
            eventTime = message.data.get('time', '00:00').replace(' ', ':')
            try:
                if eventDate is None:
                    eventDatetime = ''
                else:
                    eventDatetime = defaultFormat(eventDate + ' ' + eventTime + ':00')
            except ValueError:
                self.speak('Invalid date.')
                return 0

            response = deleteEvent(title, eventDatetime)
            self.speak(response)
            time.sleep(6)
            payload = {'action': 'REFRESH'}
            r = requests.get(url=self.url, params=payload)
        else:
            self.handle_not_connected()

    def stop(self):
        pass


def create_skill():
    return MagicMirrorVoiceControlSkill()
