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
	ignore_ign = False	#BOOL Ignoriere Herrunterfahren	
	run = True		#BOOL thread soll laufen
	stopped = False		#BOOL thread beendet 
	power_dialog = None	#Meldefenster in Kodi
	power_display = True	#BOOL Display AN
	monitor = xbmc.Monitor()
	wait_time = 600
	
	def __init__(self):
		pass
	
	def start(self):
		self.thread = Thread(target=self.gpio_checker)
		self.thread.setDaemon(True)
		self.thread.start()
		monitor.waitForAbort() #laut Wiki bleibt hier die Schleife stehen bis Kodi beendet wird
		self.run = False
		#Hier konnte man noch eine Resume-Funktion einfugen
		if self.stopped == True: #warten bis thread beendet ist und danach weiter
			GPIO.cleanup()
			xbmc.log("Service CarPCButler beendet! %s" %time.time(), level=xbmc.LOGNOTICE)
		
		
	def gpio_checker(self):	
		xbmc.log("CarPCButler: Checker Thread started! %s" %time.time(), level=xbmc.LOGNOTICE)
		GPIO.setmode(GPIO.BCM)
		#Setup der GPIOs
		#Inputs
		GPIO.setup(IN_IGN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(IN_REVERSE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(IN_LIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		#Outputs
		GPIO.setup(OUT_BACKUP_IGN_PIN, GPIO.OUT)
		GPIO.output(OUT_BACKUP_IGN_PIN, 1)
		GPIO.setup(OUT_PWR_DISPLAY, GPIO.OUT)
		GPIO.output(OUT_PWR_DISPLAY, 1)
		GPIO.setup(OUT_LED_RUN_PIN, GPIO.OUT)
		GPIO.output(OUT_LED_RUN_PIN, 0)
		
		while self.run:
			power = GPIO.input(IN_IGN_PIN)
			if power == True:
				GPIO.output(OUT_LED_RUN_PIN, 1)
				self.power_is_on()	
			elif power == False:
				xbmc.log("Car IGN turned off! %s" %time.time(), level=xbmc.LOGNOTICE)
				self.power_is_off()	
			time.sleep(0.1)
		
		self.stopped = True
		
	def power_is_on(self):
		self.ignore_ign = False
		if self.power_dialog:
			self.power_dialog.close()
			self.power_dialog = NONE
	
	def power_is_off(self):
		self.power_dialog = xbmcgui.Dialog()
		self.power_dialog_create = power_dialog.yesno("CarPCButler", "Zündung ist Aus!", "Machen sie einen Tankstopp?", "Soll ich auf Sie warten?", "Ja Warte", "Nein", 10000) #Stringdatei für andere Sprachen erstellen
		power_back = FALSE
		shut_it_down = FALSE
		
		if self.power_dialog == TRUE: #Wenn "Ja warte" gedruckt wird warte 10Min mit dem herrunterfahren
			#self.power_dialog.close()
			self.power_dialog = NONE
			GPIO.output(OUT_PWR_DISPLAY, 0)
			p = 0
			while self.wait_time < p:
				if GPIO.input(IN_IGN_PIN) == TRUE: #Wenn die Zundung innerhalb der 10Min wieder da ist, breche die Schleife ab
					power_back = TRUE
					break
				else:
					p = p +1
					time.sleep(1)
			if power_back == FALSE:
				self.shut_down
			else:
				GPIO.output(OUT_PWR_DISPLAY, 1)
				wb_dialog = xbmc.Dialog()
				wb_dialog.notification('CarPCButler', 'Willkommen zuück!', xbmcgui.NOTIFICATION_INFO, 5000)
				
		elif self.power_dialog == FALSE and not power_back: #Wenn "Nein" gedruckt wird, fahre das System sofort herunter
			self.shut_down
					
	def shut_down(self):
		xbmc.log("CarPCButler turn off Pi! %s" %time.time(), level=xbmc.LOGWARNING)
		os.system("sudo shutdown -h now")
		GPIO.output(OUT_BACKUP_IGN_PIN, 0)
		GPIO.output(OUT_PWR_DISPLAY, 0)


if __name__ == '__main__':
	xbmc.log("Service CarPCButler started! %s" %time.time(), level=xbmc.LOGNOTICE)
	main = Main()
	main.start()
	
