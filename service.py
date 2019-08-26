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
	option_rearcam = True	#Funktion Ruckfahrkamera aktiv
	rearcam_trigger = FALSE
	lightswitch_trigger = FALSE
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
			xbmc.log("Service CarPCButler stopped! %s" %time.time(), level=xbmc.LOGNOTICE)
		
		
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
				GPIO.output(OUT_LED_RUN_PIN, 0)
				xbmc.log("CarPCButler: Car IGN turned off! Shut down will be prepare... %s" %time.time(), level=xbmc.LOGNOTICE)
				self.power_is_off()	
			self.rearcam
			self.daynight
			
			time.sleep(0.1)

		
		self.stopped = True
		
	def power_is_on(self):
		self.ignore_ign = False
		if self.power_dialog:
			self.power_dialog.close()
			self.power_dialog = NONE
	
	def power_is_off(self):
		self.power_dialog = xbmcgui.Dialog()
		self.power_dialog_create = power_dialog.yesno("$ADDON[plugin.service.carpcButler 30000]", "$ADDON[plugin.service.carpcButler 30001]", "$ADDON[plugin.service.carpcButler 30002]", "$ADDON[plugin.service.carpcButler 30003]", "$ADDON[plugin.service.carpcButler 30004]", "$ADDON[plugin.service.carpcButler 30005]", 10000) 
		self.ignore_ign = TRUE
		power_back = FALSE
		
		if self.power_dialog == TRUE: #Wenn "Ja warte" gedruckt wird warte 10Min mit dem herrunterfahren
			xbmc.log("shut down paused by User! %s" %time.time(), level=xbmc.LOGNOTICE)
			#self.power_dialog.close()
			self.power_dialog = NONE
			GPIO.output(OUT_PWR_DISPLAY, 0)
			p = 0
			while self.wait_time < p:
				if GPIO.input(IN_IGN_PIN) == TRUE: #Wenn die Zundung innerhalb der 10Min wieder da ist, breche die Schleife ab
					xbmc.log("CarPCButler: Car IGN turn on! %s" %time.time(), level=xbmc.LOGNOTICE)
					power_back = TRUE
					break
				else:
					p = p + 1
					time.sleep(1)
			if power_back == FALSE:
				self.shut_down
			else:
				GPIO.output(OUT_PWR_DISPLAY, 1)
				self.ignore_ign = FALSE
				wb_dialog = xbmc.Dialog()
				wb_dialog.notification("$ADDON[plugin.service.carpcButler 30000]", "$ADDON[plugin.service.carpcButler 30006]", xbmcgui.NOTIFICATION_INFO, 5000)
				
		elif self.power_dialog == FALSE and power_back == FALSE: #Wenn "Nein" gedruckt wird, fahre das System sofort herunter
			self.shut_down
					
	def shut_down(self):
		xbmc.log("CarPCButler: Shut down Pi! %s" %time.time(), level=xbmc.LOGWARNING)
		os.system("sudo shutdown -h now")
		#GPIO.output(OUT_BACKUP_IGN_PIN, 0)
		GPIO.output(OUT_PWR_DISPLAY, 0)
		
	def rearcam(self):
		if xbmc.getCondVisibility('System.HasAddon(%s)' %plugin.program.pidash) == 1:
			addon_rear = xbmcaddon.Addon(id='plugin.program.pidash')
			addon_rear_path = addon_rear.getAddonInfo('path').decode("utf-8")
			reverse_switch = GPIO.input(IN_IGN_PIN)
			if reverse_switch == TRUE and self.rearcam_trigger == FALSE:
				xbmc.executebuiltin("XBMC.RunScript(" + addonrear_path + "/addon.py)")
				self.rearcam_trigger = TRUE
				xbmc.log("CarPCButler: Reverse gear in detected! Start Plugin Pidash %s" %time.time(), level=xbmc.LOGNOTICE)
				time.sleep(0.1)
			elif reverse_switch == FALSE and self.rearcam_trigger == TRUE:
				xbmc.executebuiltin("XBMC.StopScript(" + addonrear_path + "/addon.py)")
				self.rearcam_trigger = FALSE
				xbmc.log("CarPCButler: Reverse gear out detected! Stop Plugin Pidash %s" %time.time(), level=xbmc.LOGNOTICE)
				time.sleep(0.1)
				
		else:
			fault_dialog = xbmc.Dialog()
			fault_dialog.notification("$ADDON[plugin.service.carpcButler 30000]", "$ADDON[plugin.service.carpcButler 30007]", xbmcgui.NOTIFICATION_ERROR, 5000)
			xbmc.log("CarPCButler: Plugin piDash not installed! Please install the Plugin for more information visit https://raspicarprojekt.de/showthread.php?tid=861 %s" %time.time(), level=xbmc.LOGWARNING)

	def daynight(self):
		if xbmc.getCondVisibility('System.HasAddon(%s)' %plugin.program.carpc-xtouch')) == 1:
			addon_xtouch = xbmcaddon.Addon(id='plugin.program.carpc-xtouch')
			addon_xtouch_path = addon_xtouch.getAddonInfo('path').decode("utf-8")
			autoswitch = addon_xtouch.getSetting('autoswitch') # Wenn Zeit gesteuerte Umschaltung aktiv funktion überbrücken
			light_switch = GPIO.input(IN_LIGHT_PIN)
			if light_switch == TRUE and self.lightswitch_trigger == FALSE andnot autoswitch:
				xbmc.executebuiltin("XBMC.RunScript(" + addon_xtouch_path + "/addon.py,loadnight)")
				self.lightswitch_trigger = TRUE
				xbmc.log("CarPCButler: Light turn on! Switch Skin to night! %s" %time.time(), level=xbmc.LOGNOTICE)
			elif light_switch == FALSE and self.lightswitch_trigger == TRUE andnot autoswitch:
				xbmc.executebuiltin("XBMC.RunScript(" + addon_xtouch_path + "/addon.py,loadday)")
				self.lightswitch_trigger = FALSE
				xbmc.log("CarPCButler: Light turn off! Switch Skin to day! %s" %time.time(), level=xbmc.LOGNOTICE)
			elif light_switch == TRUE and autoswitch:
				xbmc.log("CarPCButler: Light turn on but X-Touch is in time based auto mode.... I do nothing! %s" %time.time(), level=xbmc.LOGNOTICE)
		else:
			fault_dialog = xbmc.Dialog()
			fault_dialog.notification("$ADDON[plugin.service.carpcButler 30000]", "$ADDON[plugin.service.carpcButler 30008]", xbmcgui.NOTIFICATION_ERROR, 5000)
			xbmc.log("CarPCButler: Plugin xTouch not installed! Please install the Plugin for more information visit https://raspicarprojekt.de %s" %time.time(), level=xbmc.LOGWARNING)
				
					  
if __name__ == '__main__':
	xbmc.log("Service CarPCButler started! %s" %time.time(), level=xbmc.LOGNOTICE)
	main = Main()
	main.start()
	
