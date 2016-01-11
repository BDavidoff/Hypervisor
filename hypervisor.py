'''
dev channel
hypervisor Script.
Script that interperts Sequence XML and uses that to preform tasks to move sequences through routines.
The interperter script is flexible and allows for abstracted Sequence configuration and layman
input.

Created by Brett Davidoff October 2015

Version 2.2.0
'''

from xml.etree.ElementTree import parse
import os 
from os import system
from sys import exit
import pyautogui as gui
import Action
from Action import log
from time import sleep
import datetime
import sys

sys.path.insert(0, '/mnt/hypervisor/scripts')

class Sequence():
	name           = None
	xml            = None
	startUrl       = None
	search		   = None
	
	#methods
	startScript    = None
	turnScript     = None
	
	#images
	activeImages   = None
	adImages       = None
	startImages    = None
	
	#status'	
	status         = 0
	no_clicks      = 0
	
	#window IDs 
	startWindow  = None
	activeWindow = None
	adWindow     = None
		
	def __init__(self, xmlNode):
		self.name         = xmlNode.attrib['name']
		self.startUrl     = xmlNode.find('./startUrl').text
		
		self.activeImages = tuple(map(lambda x: x.text, xmlNode.findall('./activeImages/activeImage')))
		self.adImages     = tuple(map(lambda x: x.text, xmlNode.findall('./adImages/adImage'        )))
		self.startImages  = tuple(map(lambda x: x.text, xmlNode.findall('./startImages/startImage'  )))
		
		self.search       = xmlNode.attrib['search']
		
		self.startScript  = __import__(xmlNode.find("./scripts/startScript").text)
		self.turnScript   = __import__(xmlNode.find("./scripts/turnScript").text)
		
		self.xml          = xmlNode		
	
	def start(self):
		return self.startScript.start(self)
	
	def turn(self):
		return self.turnScript.turn(self)
	
	def isIdle(self, pic):
		log("checking for idleness with %s" % pic)
		sleep(3)
		if Action.doesExist(pic):
			log("%s might be idle..." % self.name)
			sleep(3)
			if Action.doesExist(pic):
				log("%s is idle" % self.name, "warn")
				return True
		return False
	
	def closeAll(self):
		log("restarting %s" % self.name)
		Action.close(self.startWindow)
		sleep(1)
		Action.close(self.activeWindow)
		sleep(1)
		Action.close(self.adWindow)
		log("all %s windows closed" % self.name)
		
		#Reset all counters and Sequence variables
		self.no_clicks      = 0
		self.startWindow    = None
		self.activeWindow   = None
		self.adWindow       = None
			
def getAllSequences():
	xmlRoot = parse("sampleSequences.xml").getroot()
	return filter(lambda x: x.name in userSetSequences, map(lambda x: Sequence(x), xmlRoot.findall('./Sequence')))

def startSequences(Sequences):
	log("Activating Sequences")
	for Sequence in Sequences:
		while 0 <= Sequence.status < 4:
			log("starting %s" % Sequence.name)
			if Sequence.start():
				Sequence.status = -1
				log("windows for %s ready\n" % Sequence.name)
			else:
				log("failed to start %s" % Sequence.name)
				Sequence.closeAll()
				Sequence.status += 1
			Action.wait()
		if Sequence.status > 0:
			log("ending attempts to start %s" % Sequence.name, "warn")
	
	log("all Sequences have been started")
		
def warmUp():
	Action.openUrl("www.yahoo.com")
	sleep(20)
	system("pkill -9 chrome")
	
def run():
	log("Hypervisor script has been started")
	
	crit_errors = 0
	Sequences = getAllSequences()
	
	while True:
		log("outter loop started")
		if crit_errors > 4:
			log("Total number of critical errors has been exceeded, system SHUTTING DOWN", "warn")
			break
		log("stopping all currently running windows")
		system("pkill -9 chrome")
		Action.wait()
		
		#Inital startup of all Sequences
		startSequences(Sequences)
		
		log("inner loop started")
		while len(filter(lambda x: x.status < 0, Sequences)) > 0:
			for Sequence in filter(lambda x: x.status < 0, Sequences):	
				log("turning %s" % Sequence.name)
				
				turnedPic = Sequence.turn()
				if turnedPic is not False:
					log("turned pic is %s" % turnedPic)
					if Sequence.isIdle(turnedPic):
						log("%s is idle, deactivating..." % Sequence.name, "warn")
						Sequence.closeAll()
						Sequence.status += 1
					else:
						log("%s turned.\n" % Sequence.name)
						Sequence.no_clicks = 0
				elif Sequence.no_clicks > 5:
					log("%s exceeds maximum number of missed clicks, deactivating..." % Sequence.name, "warn")
					Sequence.closeAll()
					Sequence.status += 1
				else:
					log("no buttons detected for %s" % Sequence.name)
					Sequence.no_clicks += 1
			log("all Sequences have been turned.")	
			
			for Sequence in filter(lambda x: 0 <= x.status < 8, Sequences):
				log("attempting to reactivate %s" % Sequence.name)
				if Sequence.start():
					log("%s successfully started" % Sequence.name)
					Sequence.status = -1
				else:
					log("failed to start %s" % Sequence.name)
					Sequence.status += 1
					
userSetSequences = open("userSequences.txt", "r").read().split("\n")
# userSetSequences = ["ngage"]

warmUp()
run()
log("Python script terminated")