# grovepi_lcd_dht.py

# from grovepi import *
import grovepi

from grove_rgb_lcd import *

sensor = 6		# Connect the DHt Pro sensor to port 6

while True:
	try:
		[ temp,hum ] = grovepi.dht(sensor,1)		#Get the temperature and Humidity from the DHT sensor
		print "temp =", temp, "C\thumadity =", hum,"%" 	
		t = str(temp)
		h = str(hum)
		
		setRGB(0,128,64)
		setRGB(0,255,0)
		setText("Temp:" + t + "C      " + "Humidity :" + h + "%")			
	except (IOError,TypeError) as e:
		print "Error"



