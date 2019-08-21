import os, time
import xbmc, xbmcgui, xbmcaddon
import RPi.GPIO as GPIO
from threading import Thread

__addon__	= xbmcaddon.Addon()
__addonid__	= __addon__.getAddonInfo('id').decode( 'utf-8' )
__addonname__	= __addon__.getAddonInfo('name').decode("utf-8")

OUT_LED_RUN_PIN		= 14	#Anzeige Pi lauft  
IN_IGN_PIN		= 16	#Signal Zundung ist an
IN_LIGHT_PIN		= 17	#Signal Dammerungsschalter
IN_REVERSE_PIN		= 18	#Signal Ruckwartsgang
OUT_BACKUP_IGN_PIN	= 22	#Uberbruckung Herrunterfahren
OUT_PWR_DISPLAY		= 24	#Display Hintergrundbeleuchtung -> Soll nach gewisser Zeit ausschalten wenn in uberbruckung

class Main(object):
	ignore_ign = False		
	run = True		#BOOL thread lauft
	stopped = False		#BOOL thread beendet wurde (ob ich das brauche?) 
	power_dialog = None	#Meldefenster in Kodi
	power_display = True	#BOOL Display AN
	rear_thread = NONE	#Ich werde wohl eine Thread brauchen wegen der Rückfahrkamera
	
	def __init__(self):
		pass
	
	def start(self):
		self.thread = Thread(target=self.gpio_checker)
		self.thread.setDaemon(True)
		self.thread.start()
		
	def gpio_checker(self):	
		GPIO.setmode(GPIO.BCM)
		
		#Hier gehts weiter!!!



if __name__ == '__main__':
	dialog = xbmcgui.Dialog()
	main = Main()
	main.start()
	
