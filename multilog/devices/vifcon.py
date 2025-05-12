# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Verbindung mit Vifcon
- Vorlage für die Verknüpfung stammt von Vincent Funke, IKZ 2024
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtCore import (
    QObject,
)

## Algemein:
import logging
import socket                       # TCP-Verbindungen
import json                         # Dicts zu String
import time

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++

logger = logging.getLogger(__name__)

class Vifcon(QObject):
    def __init__(self, ip, ports, trigger, VifconDevices):
        ''' Erstellung einer Verbindung zum IKZ
        '''
        super().__init__()

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        ## Init:
        self.sprache                    = 0
        self.portList                   = ports
        self.ip                         = ip
        self.trigger                    = trigger          
        self.VifconDevices              = VifconDevices
        ## Weitere:
        self.done                       = False                 # Ende der Endlosschleife, wenn True
        error                           = False                 # Fehler beim Aufbau!

        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Logging:                             
        self.Log_Text_186_str   =   ['VIFCON-Verbindungs Objekt',                                                     'VIFCON connection object']
        self.Log_Text_187_str   =   ['Erstellung!',                                                                     'Creation!']
        self.Log_Text_188_str   =   ['Port-Liste (genutzte Ports):',                                                    'Port list (ports used):']
        self.Log_Text_189_str   =   ['Trigger-Liste (genutzte Trigger aus der Konfigurationsdatei):',                   'Trigger list (used triggers from the configuration file):']
        self.Log_Text_190_str   =   ['Der folgende Trigger existiert mehr als einmal:',                                 'The following trigger exists more than once:']
        self.Log_Text_191_str   =   ['Der folgende Port existiert mehr als einmal:',                                    'The following port exists more than once:']
        self.Log_Text_192_str   =   ['-Port hat folgende Objekt-Parameter:',                                            '-Port has the following object parameters:']
        self.Log_Text_193_str   =   ['und folgende Endverbindung:',                                                     'and the following end connection:']
        self.Log_Text_194_str   =   ['Bearbeitung von Trigger:',                                                        'Editing triggers:']
        self.Log_Text_195_str   =   ['an Verbindung',                                                                   'to connection']
        self.Log_Text_196_str   =   ['Sende Daten:',                                                                    'Send data:']
        self.Log_Text_197_str   =   ['Trigger-Fehler: Unbekannter Trigger von VIFCON ->',                             'Trigger error: Unknown trigger from VIFCON ->']
        self.Log_Text_198_str   =   ['Existieren tun folgende Trigger in Multilog:',                                      'The following triggers do exist in Multilog:']
        self.Log_Text_199_str   =   ['Verbindung beendet mit VIFCON!',                                                'Connection terminated with VIFCON!']
        self.Log_Text_200_str   =   ['Multilog sendet Leere String als Trigger -> Beende Kommunikation!',               'Multilog sends empty string as trigger -> end communication!']
        self.Log_Text_201_str   =   ['Sende Fehler:',                                                                   'Send error:']
        self.Log_Text_202_str   =   ['Aufgrund eines falschen Triggers, wird die Verbindung gelöscht:',                 'Due to an incorrect trigger, the connection is deleted:']
        self.Log_Text_209_str   =   ['ACHTUNG: Multilog starten, wenn noch nicht erfolgt!! Aufbau Verbindung zu Port',  "ATTENTION: Start multilog if it hasn't already happened!! Establishing a connection to port"]
        self.Log_Text_210_str   =   ['VIFCON-Link wird nicht erstellt, da Fehler!',                                   "VIFCON link is not created because error!"]
        self.Log_Text_211_str   =   ['Anzahl:',                                                                         "Amount:"]

        #--------------------------------------- 
        # Informationen 1:
        #---------------------------------------

        ## Logging-Infos:
        logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_187_str[self.sprache]}")
        logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_188_str[self.sprache]} {self.portList}")
        find_List = []
        for n in self.portList:
            z = self.portList.count(n)
            if z > 1:
                if not n in find_List:
                    find_List.append(n)
                    logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_191_str[self.sprache]} {n} - {self.Log_Text_211_str[self.sprache]} {z}")
                    error = True

        logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_189_str[self.sprache]} {self.trigger}")
        find_List = []
        for n in self.trigger:
            z = self.trigger.count(n)
            if z > 1:
                if not n in find_List:
                    find_List.append(n)
                    logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_190_str[self.sprache]} {n} - {self.Log_Text_211_str[self.sprache]} {z}")
                    error = True

        #--------------------------------------------------
        # Multilog Verbindungsaufbau 1 & Informationen 2:
        #--------------------------------------------------
        self.connectList = []
        self.portList.sort()                                             # Liste der Ports muss sortiert sein!
        if not error:
            for port in self.portList:
                s = socket.socket()
                s.connect((ip, port))
                self.connectList.append(s)                          # Verbindung zu einer Liste hinzufügen
                time.sleep(0.1)
        else:
            logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_210_str[self.sprache]}")
            self.done = True
            
##########################################
# Daten besorgen und weitersenden:
##########################################
    def sendData(self, c, trigger):
        '''Hole und Sende Daten
        
        Args:
            c (<class 'socket.socket'>):        Verbindung
            trigger (str):                      Trigger Wort
        '''
        logger.debug(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_194_str[self.sprache]} {trigger} {self.Log_Text_195_str[self.sprache]} {c}")

        # Trigger ist in Liste:
        if trigger in self.trigger:
            deviceJSON = ""
            for device in self.VifconDevices:
                if trigger == device.name:
                    data = device.getLatestSample() # letzte gespeichertes Sample abfragen.
                    deviceJSON += json.dumps({device.name:data}) 

            data = bytes(deviceJSON,encoding="utf-8")       # Dict zu String zu Bianry
            c.sendall(data)                                 # Dict senden
        # Client (Multilog) wurde beendet bzw. die Verbindung wurde getrennt --> Leerer Stirng:
        elif trigger == '' and not self.done:
            logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_200_str[self.sprache]}")
            self.ende()
        # Trigger ist nicht in Liste:
        elif not trigger in self.trigger and not self.done:
            logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_197_str[self.sprache]} {trigger}")
            logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_198_str[self.sprache]} {self.trigger}")
            logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_202_str[self.sprache]} {c}")
            self.connectList.remove(c)                      # Entfernt Verbindung des falschen Triggers!

    ##########################################
    # Endlosschleife und Endfunktion:
    ##########################################
    def event_Loop(self):
        '''Endlosschleife: Empfang der Trigger und Senden der Daten'''
        while not self.done:
            try:
                for c in self.connectList:                  # gehe jede Verbindung die besteht durch
                    trigger = c.recv(1024).decode('utf-8')  # warte auf Triggerwort und lese dieses
                    self.sendData(c, trigger)               # erstelle und sende die Daten
            except Exception as e:
                logger.exception(f'{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_201_str[self.sprache]}')
            time.sleep(0.1)
    
    def ende(self):
        '''Setzt While-Schleifen Bedingung auf True und beendet so Endlosschleife!'''
        self.done = True
        logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_199_str[self.sprache]}")
