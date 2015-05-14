# GrovePi + Grove Temperature & Humidity Sensor Pro
# http://www.seeedstudio.com/wiki/Grove_-_Temperature_and_Humidity_Sensor_Pro

import grovepi
import time
import math

def T_dew_point(T,RH):  # in degrees C  -30<T<35
  # T is temperature (drybulb) in degrees C
  # RH is relative humidity in percent 1<RH<100

  # a=6.112  # millibar or hPa
  # b=17.67
  # c=243.5 # degrees C
  # Magnus approximation
  # gam=math.log(RH/100.) + b*T/(c+T)
  # more complex
  # Bogel modification
  a=6.1121  # millibar or hPa
  b=18.678
  c=257.14 # degrees C
  d=234.5  # degrees C
  # Pst=a*math.exp(b*T/(c+T))  #  saturated water vapor pressure
  Pst = a*math.exp((b-T/d)*(T/(c+T)))
  Pat=(RH/100.)*Pst          #  water vapor presure
  gam = math.log(Pat/a)
  Tdp=c*gam/(b-gam)
  return(Tdp)


# Connect the Grove Temperature & Humidity Sensor Pro to digital port D6
# SIG,NC,VCC,GND
sensor = 6

while True:
    try:
        [tempC,humidity] = grovepi.dht(sensor,1)
        temp=9./5.*tempC + 32.       # convert from C to F
        Tdp=10.
        Tdp = T_dew_point(tempC,humidity)
        print "temp =", tempC, " humidity =", humidity, " dew point ", Tdp
        time.sleep(0.2)
    except IOError:
        print "Error"
