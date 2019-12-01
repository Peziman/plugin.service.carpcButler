import os, time
import xbmc, xbmcgui, xbmcaddon
import RPi.GPIO as GPIO
import subprocess
from threading import Thread

__addon__	= xbmcaddon.Addon()
__addonid__	= __addon__.getAddonInfo('id').decode( 'utf-8' )
__addonname__	= __addon__.getAddonInfo('name').decode("utf-8")
__addonpath__ = __addon__.getAddonInfo('path').decode("utf-8")
addon = xbmcaddon.Addon(id='plugin.service.carpcButler')

OUT_LED_RUN_PIN		= int(addon.getSetting('out_led_run_pin'))		#Anzeige Pi lauft  
IN_IGN_PIN		= int(addon.getSetting('in_ign_pin'))			#Signal Zundung ist an
IN_LIGHT_PIN		= int(addon.getSetting('in_light_pin'))			#Signal Dammerungsschalter
IN_REVERSE_PIN		= int(addon.getSetting('in_reverse_pin'))		#Signal Ruckwartsgang
OUT_BACKUP_IGN_PIN	= int(addon.getSetting('out_backup_ign_pin'))	#Ausgang Uberbruckung Spannungsversorgung
OUT_PWR_DISPLAY		= int(addon.getSetting('out_pwr_display'))		#Display Hintergrundbeleuchtung -> Soll nach gewisser Zeit ausschalten wenn in uberbruckung
OUT_AMP_CONTROL		= int(addon.getSetting('out_amp_control'))		#Ausgang fur Verstarker remote

class Main(object):
	ignore_ign = False				#BOOL Ignoriere Herrunterfahren	
	run = True					#BOOL thread soll laufen
	stopped = False					#BOOL thread beendet 
	power_dialog = None				#Meldefenster in Kodi
	power_dialog_pass = False
	power_display = True				#BOOL Display AN
	rearcam_trigger = False				#Ruckfahrkamera ist aktiv
	lightswitch_trigger = False			#Licht ist aktiv
	wait_time = int(addon.getSetting('wait_time'))	#Wartezeit bei Tankstop in Sekunden
	laststate_play = False
	
	def __init__(self):
		pass
	
	def start(self):
		self.thread = Thread(target=self.gpio_checker)
		self.thread.setDaemon(True)
		self.thread.start()
		self.output_control("amp_control", "on", OUT_AMP_CONTROL)
		monitor = xbmc.Monitor()
		monitor.waitForAbort() #laut Wiki bleibt hier die Schleife stehen bis Kodi beendet wird
		self.run = False
		#Hier konnte man noch eine Resume-Funktion einfugen
		self.thread.join()
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
		GPIO.setup(OUT_PWR_DISPLAY, GPIO.OUT)
		GPIO.setup(OUT_LED_RUN_PIN, GPIO.OUT)
		GPIO.setup(OUT_AMP_CONTROL, GPIO.OUT)
		
		while self.run:
			power = GPIO.input(IN_IGN_PIN)
			if power == True:
				self.output_control("option_power_led", "on", OUT_LED_RUN_PIN)
				self.power_is_on()	
			elif power == False and self.power_dialog_pass == False:
				self.output_control("option_power_led", "off", OUT_LED_RUN_PIN)
				xbmc.log("CarPCButler: Car IGN turned off! Shut down will be prepare... %s" %time.time(), level=xbmc.LOGNOTICE)
				self.checkplayer()
				self.power_is_off()
			else:
				pass
			
			if str(addon.getSetting('option_rearcam')) == "true":
				self.rearcam()
			if str(addon.getSetting('option_light')) == "true":
				self.daynight()
			
			time.sleep(0.1)

		
		self.stopped = True
		
	def power_is_on(self):
		self.ignore_ign = False
		self.power_dialog_pass = False
		if self.power_dialog:
			self.power_dialog.close()
			self.power_dialog = None
	
	def power_is_off(self):
		power_dialog = xbmcgui.Dialog().yesno("$ADDON[plugin.service.carpcButler 30000]", "$ADDON[plugin.service.carpcButler 30001]", "$ADDON[plugin.service.carpcButler 30002]", "$ADDON[plugin.service.carpcButler 30003]", autoclose = 10000) 
		self.ignore_ign = True
		self.power_dialog_pass = True
		self.power_back = False
		
		if power_dialog: #Wenn "Ja warte" gedruckt wird warte 10Min mit dem herrunterfahren
			xbmc.log("shut down paused by User! %s" %time.time(), level=xbmc.LOGNOTICE)
			self.display_control("off")
			self.output_control("amp_control", "off", OUT_AMP_CONTROL)
			p = 0
			while self.wait_time > p:
				if GPIO.input(IN_IGN_PIN) == True: #Wenn die Zundung innerhalb der 10Min wieder da ist, breche die Schleife ab
					xbmc.log("CarPCButler: Car IGN turn on! %s" %time.time(), level=xbmc.LOGNOTICE)
					self.power_back = True
					self.power_is_on()
					break
				else:
					self.output_control("option_power_led", "toggle", OUT_LED_RUN_PIN)
					p = p + 1
				time.sleep(1)
			if self.power_back == False:
				xbmc.log("Timeout.... shutdown! %s" %time.time(), level=xbmc.LOGNOTICE)
				self.shut_down()
			else:
				self.display_control("on")
				self.output_control("amp_control", "on", OUT_AMP_CONTROL)
				self.ignore_ign = False
				wb_dialog = xbmcgui.Dialog()
				wb_dialog.notification("$ADDON[plugin.service.carpcButler 30000]", "$ADDON[plugin.service.carpcButler 30006]", xbmcgui.NOTIFICATION_INFO, 5000)
				self.player_resume()
				
		else:		#Wenn "Nein" gedruckt wird, fahre das System sofort herunter
			if GPIO.input(IN_IGN_PIN) == False: #Wenn die Zundung sofort wieder da ist schalte CarPC nicht ab.
				xbmc.log("shut down by User! %s" %time.time(), level=xbmc.LOGNOTICE)
				self.shut_down()
			else:
				pass
					
	def shut_down(self):
		xbmc.log("CarPCButler: Shut down Pi! %s" %time.time(), level=xbmc.LOGWARNING)
		self.output_control("amp_control", "off", OUT_AMP_CONTROL)
		self.display_control("off")
		os.system("sudo shutdown -h now")

		
	def rearcam(self):
		if xbmc.getCondVisibility('System.HasAddon(plugin.program.pidash)') == 1:
			addon_rear = xbmcaddon.Addon(id='plugin.program.pidash')
			addon_rear_path = addon_rear.getAddonInfo('path').decode("utf-8")
			reverse_switch = GPIO.input(IN_REVERSE_PIN)
			if reverse_switch == True and self.rearcam_trigger == False:
				xbmc.executebuiltin("XBMC.RunScript(" + addon_rear_path + "/addon.py)")
				self.rearcam_trigger = True
				xbmc.log("CarPCButler: Reverse gear in detected! Start Plugin Pidash %s" %time.time(), level=xbmc.LOGNOTICE)
				time.sleep(0.1)
			elif reverse_switch == False and self.rearcam_trigger == True:
				#xbmc.executebuiltin("StopScript(plugin.program.pidash)")
				#xbmc.executebuiltin("Dialog.Close(all)")
				self.rearcam_trigger = False
				xbmc.log("CarPCButler: Reverse gear out detected! Stop Plugin Pidash %s" %time.time(), level=xbmc.LOGNOTICE)
				time.sleep(0.1)
			elif reverse_switch == True and self.rearcam_trigger == True:
				pass
				
		else:
			fault_dialog = xbmcgui.Dialog()
			fault_dialog.notification("$ADDON[plugin.service.carpcButler 30000]", "$ADDON[plugin.service.carpcButler 30007]", xbmcgui.NOTIFICATION_ERROR, 5000)
			xbmc.log("CarPCButler: Plugin piDash not installed! Please install the Plugin. For more information visit https://raspicarprojekt.de/showthread.php?tid=861 %s" %time.time(), level=xbmc.LOGWARNING)
			addon.setSetting(id='option_rearcam', value='false')

	def daynight(self):
		if xbmc.getCondVisibility('System.HasAddon(plugin.program.carpc-xtouch)') == 1:
			addon_xtouch = xbmcaddon.Addon(id='plugin.program.carpc-xtouch')
			addonpath_xtouch = addon_xtouch.getAddonInfo('path').decode("utf-8")
			autoswitch = addon_xtouch.getSetting('autoswitch') # Wenn Zeit gesteuerte Umschaltung aktiv funktion uberbrucken
			light_switch = GPIO.input(IN_LIGHT_PIN)
			if autoswitch == "false":
				if light_switch == True and self.lightswitch_trigger == False:
					xbmc.executebuiltin("XBMC.RunScript(" + addonpath_xtouch + "/addon.py,loadnight)")
					self.lightswitch_trigger = True
					xbmc.log("CarPCButler: Light turn on! Switch Skin to night! %s" %time.time(), level=xbmc.LOGNOTICE)
				elif light_switch == False and self.lightswitch_trigger == True:
					xbmc.executebuiltin("XBMC.RunScript(" + addonpath_xtouch + "/addon.py,loadday)")
					self.lightswitch_trigger = False
					xbmc.log("CarPCButler: Light turn off! Switch Skin to day! %s" %time.time(), level=xbmc.LOGNOTICE)
			else:
				if light_switch == True and self.lightswitch_trigger == False:
					self.lightswitch_trigger = True
					xbmc.log("CarPCButler: Light turn on but X-Touch is in time based auto mode.... I do nothing! %s" %time.time(), level=xbmc.LOGNOTICE)
				elif  light_switch == False and self.lightswitch_trigger == True:
					self.lightswitch_trigger = False
					xbmc.log("CarPCButler: Light turn off but X-Touch is in time based auto mode.... I do nothing! %s" %time.time(), level=xbmc.LOGNOTICE)
		else:
			fault_dialog = xbmcgui.Dialog()
			fault_dialog.notification("$ADDON[plugin.service.carpcButler 30000]", "$ADDON[plugin.service.carpcButler 30008]", xbmcgui.NOTIFICATION_ERROR, 5000)
			xbmc.log("CarPCButler: Plugin xTouch not installed! Please install the Plugin. For more information visit https://raspicarprojekt.de/showthread.php?tid=913 %s" %time.time(), level=xbmc.LOGWARNING)
			addon.setSetting(id='option_light', value='false')
			
	def checkplayer(self):
		player = xbmc.Player()
		if player.isPlaying():
			self.laststate_play = True
			player.pause()
		else:
			pass

	def player_resume(self):
		player = xbmc.Player()
		if self.laststate_play == True:
			self.laststate_play = False	
			player.pause()
		else:
			pass	
			
	def output_control(self, output_setting, output_mode, output_no):
		if str(addon.getSetting(output_setting)) == "true":
			if output_mode == "on" and GPIO.input(output_no) == False:
				GPIO.output(output_no, GPIO.HIGH)
			if output_mode == "off" and GPIO.input(output_no) == True:
				GPIO.output(output_no, GPIO.LOW)
			if output_mode == "toggle" and GPIO.input(output_no) == True:
				GPIO.output(output_no, GPIO.LOW)
			if output_mode == "toggle" and GPIO.input(output_no) == False:
				GPIO.output(output_no, GPIO.HIGH)
		else:
			pass
		
	def display_control(self, display_mode):
		if str(addon.getSetting('display_hard_mode')) == "true":
			if display_mode == "off" and GPIO.input(OUT_PWR_DISPLAY) == True:
				GPIO.output(OUT_PWR_DISPLAY, GPIO.LOW)
			if display_mode == "on" and GPIO.input(OUT_PWR_DISPLAY) == False:
				GPIO.output(OUT_PWR_DISPLAY, GPIO.HIGH)
		else:
			if display_mode == "off" and self.power_back == False:
				subprocess.call(["vcgencmd", "display_power", "0"])
			if display_mode == "on" and self.power_back == True:
				subprocess.call(["vcgencmd", "display_power", "1"])

	
if __name__ == '__main__':
	xbmc.log("Service CarPCButler started! %s" %time.time(), level=xbmc.LOGNOTICE)
	main = Main()
	main.start()
	
