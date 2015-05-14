# grovepi_lcd_dht.py

from grovepi import *
from grove_rgb_lcd import *
import time

dht_sensor_port = 7		# Connect the DHt sensor to port 7

#this doesnt'w work for v1,2 sensor???

while True:
	try:
		[ temp,hum ] = dht(dht_sensor_port,1)		#Get the temperature and Humidity from the DHT sensor
		print "temp =", temp, "C\thumadity =", hum,"%" 	
		t = str(temp)
		h = str(hum)
		
		setRGB(0,128,64)
		setRGB(0,255,0)
		setText("Temp:" + t + "C      " + "Humidity :" + h + "%")
		time.sleep(1.5)
	except (IOError,TypeError) as e:
		print "Error"



