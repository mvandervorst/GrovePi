# GrovePi + SantSmart TGS2600
# http://www.seeedstudio.com/wiki/Grove_-_Air_Quality_Sensor

import time
import grovepi
import math
from grove_rgb_lcd import *
from grove_barometer_lib import barometer  # lib copied from ./grove_barometer/basic


#----------------------------------------------------------------------------
#  subroutines, eventually will be a module with class to do ininialization
#----------------------------------------------------------------------------
def T_dew_point(T,RH):  # in degrees C  -30<T<35
  # T is temperature (drybulb) in degrees C
  # RH is relative humidity in percent 1<RH<100
  a=6.112  # millibar or hPa
  b=18.678
  c=257.14 # degrees C
  d=234.5  # degrees C

  a=6.112  # millibar or hPa
  b=17.67
  c=243.5 # degrees C
  # Magnus approximation
  #gamma=log(RH/100) + b*T/(c+T)
  #Tdp=c*gamma/(b-gamma)
  #
  Pst=a*math.exp(b*T/(c+T))  #  saturated water vapor pressure
  Pat=(RH/100.)*Pst     #  water vapor presure
  gamma = math.log(PsT/a)
  Tdp=c*gamma/(b-gamma)
  return(Tdp)
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
  if Pat > 0:
    gam = math.log(Pat/a)
    Tdp=c*gam/(b-gam)
    return(Tdp)
  else:
    return(-T)

def current_milliamps(it,pin_in,wait):
  amax=analog_max(it, pin_in, wait)
  # print "current_amps ave, it, pin_in, wait ", ave, it, pin_in, wait
  if amax >= 0.:
        # Get sensor value
        grove_vcc=5.0  # grove voltage
        # Calculate amplitude current (mA)
        amplitude_current = (amax / 1024. * grove_vcc / 800. * 2000000.)

        # Calculate effective value (mA)
        effective_value = amplitude_current / 1.414

        # minimum_current = 1 / 1024 * grove_vcc / 800 * 2000000 / 1.414 = 8.6(mA)
        # Only for sinusoidal alternating current
        milliamps = effective_value
        # print "current raw_ave", ave
        return(milliamps)
  else:
    return(-1)
  # endif
#end def

def voltage(it,pin_in,wait,divider):
  ave=analog_ave(it, pin_in, wait)
  if ave > 0.:
      v=5.0*ave*divider/1023.
      # print "voltage raw_ave", v, ave
      return(v)
  else:
    return(-1)
  # endif
#end def

def H2ppm(it,a,wait):
  air=analog_ave(it, a, wait)
  return (air)
          
def analog_ave(it, a, wait):
# read it values of data from analog pin a and average
# wait is number of seconds between reads
# returns negative number if error
  i=0
  ierr=0
  s=0.
  tcall=0.
#  print "raw_aiir_ave it, a, wait ", it, a,  wait
  while i<it and ierr<it:
    try:
        # Get sensor value from gas sensor
        time.sleep(wait)
        t0=time.time()
        raw = grovepi.analogRead(a)
        dt=time.time() - t0
        tcall=tcall+dt
        s=s + raw
        i=i+1
#       print "sum i ierr ", s, i, ierr
    except IOError:    
        ierr=ierr+1
        # print "IOError analog ave", ierr
#   end try
# end while
  if i>0:
      ave=s/i
      tcall=tcall/i
      # print "analog read time: ", tcall
      # print "result s i", ave, s, i
      return(ave);
  else:
      return(-ierr)
# endif
#end def

def analog_max(it, a, wait):
# read it values of data from analog pin a and maximise
# wait is number of seconds between reads
# returns negative number if error
# this is slow, it must take a long time to interface between the GrovePi and Rpi
  i=0
  ierr=0
  amax=0
  #print "analog_max it, a, wait ", it, a,  wait
  while i<it and ierr<it:
    try:
        # Get sensor value from analog sensor
        # time.sleep(wait)
        raw = grovepi.analogRead(a)
        i=i+1
        if raw > amax:
          amax=raw
        # time.sleep(wait)
        # print "max i ierr ", amax, i, ierr
    except IOError:    
        ierr=ierr+1
        # print "IOError analog max", ierr
#   end try
# end while
  if i>0:
      #print "result amax i ierr", amax, i, ierr
      return(amax);
  else:
      return(-ierr)
# endif
#end def
#
#------------------------------------------------------------------------
# start of main program
#------------------------------------------------------------------------
debug=False

# 4 digit LED
# Connect the Grove 4 Digit Display to digital port D5
# CLK,DIO,VCC,GND
display = 5
grovepi.pinMode(display,"OUTPUT")
#print "Test 1) Initialise"
grovepi.fourDigit_init(display)
# set to lowest brightness level
grovepi.fourDigit_brightness(display,0)


b = barometer()  #  Grove I2C high precision barometer sensor on 0x76

# Wait 2 minutes for the sensor to heat-up
# Connect the MQ-8 H2 Sensor to analog port A0
# SIG,NC,VCC,GND
air_sensor = 0
itair=50  # number of averaging iteration for air sensor
wait=0.2 # seconds to wait between air sensor readings


# Connect the Grove Electricy Sensor to analog port A1
# SIG,NC,VCC,GND
electricity_sensor = 1
itmax_elec=500
wait_elec=0.001  # 1 ms

# Connect the Grove Voltage Divider Sensor to analog port A2
# SIG,NC,VCC,GND
voltage_divider_sensor = 2
vdiv=3   # voltage divider switch setting
#        sensor board divides voltage by 3 or 10,
#        e.g if 3, 0-15 volts becomes, 0 to 5 volts to analog pin
vwait=0.1 # seconds to wait between readings
itmaxv=30 # number of readings to average

#Connect the Grove Temperature & Humidity Sensor Pro to digital port D6
# SIG,NC,VCC,GND
digital_temp_humidity_sensor = 6

# Initialize analog sensors to input

# air sensor
grovepi.pinMode(air_sensor,"INPUT")
# Grove electricity sensor
grovepi.pinMode(electricity_sensor,"INPUT")
# Grove voltage divider sensor
grovepi.pinMode(voltage_divider_sensor,"INPUT")

lines_data=24
lines=lines_data

while True:
    humidity=-100.
    while humidity < 0 :
      try:
        [tempC,humidity] = grovepi.dht(digital_temp_humidity_sensor,1)
        temp=9./5.*tempC + 32.       # convert from C to F
      except IOError:
        # print "dht Error"
        temp=-100.
        humidity=-100.
      # end try
      time.sleep(0.5)
    # end while
    if debug:
      print "temp, humidity ",temp, humidity
    try:
        b.update()  # update barometer, I2C sensor
        tbar = b.temperature/100.  # deg C
        tbarF=1.8*tbar + 32.
        bar_pres= b.pressure/100.  # millibars or hPa  (hundred of Pascals)
        bar_alt= b.altitude/100.   # meters
        if debug:
          print "Temp:",tbar," C, Pressure:",bar_pres," khPa, Altitude:", \
             bar_alt, "m"
        # Get H2 raw sensor value from MQ-8 analog sensor
        air = H2ppm(itair,air_sensor,wait)
        if debug:
          print "H2 ", air, "ppm"
        amps=current_milliamps(itmax_elec,electricity_sensor,wait_elec)
        if debug:
          print "Current ", amps, "mA"
        volts=voltage(itmaxv, voltage_divider_sensor, vwait, vdiv)
        if debug:
          print "voltage ", volts, "v"
        Tdp = T_dew_point(tempC,humidity)
        DewPointF = 1.8*Tdp + 32.

        if lines >= lines_data:
          print " Date       Time     Year T(F) H(%) H2(ppm)C(mA) volt Tb(F) P(hPa) Al(m) Dew(F)"
          lines=0
        lines=lines+1
        print "%25s" % time.ctime(),
        
        print "%4.0f %3.0f %6.0f %5.0f %6.2f %4.0f %6.1f %5.0f %4.0f" % \
          (temp, humidity, air,  amps, volts, tbarF, bar_pres, bar_alt, DewPointF )
        
        a = str(air)
        t = str(temp)
        h = str(humidity)
	
#       setRGB(0,128,64)
#       setRGB(0,255,0)
        setRGB(0,0,0)
        
        setText("T:" + t + "C " + "Hum: " + h + "% " + "Gas: " + a + " raw")
#       print "Test 9) Monitor analog pin"
        seconds = 1
        grovepi.fourDigit_monitor(display,air_sensor,seconds)

        
        time.sleep(60.)  # about one sample per 2 minute

    except IOError:
        print "IOError in main loop"



