#!/usr/bin/env python
# *******************Demo for MQ-8 Gas Sensor Module V1.0**********************
# Modifications by Michael Vander Vorst
# History:
#    2015-05-14 convert to Python for GrovePi
# Originally written for aruino
# Author: Tiequan Shao: tiequan.shao[at]sandboxelectronics.com
# Peng Wei: peng.wei[at]sandboxelectronics.com

# Lisence: Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)
# Note: This piece of source code is supposed to be used as a demostration ONLY.
# sophisticated calibration is required for industrial field application.

# Sandbox Electronics 2011-04-25
# ****************************************************************************/
# Hydrogen properties by volume:
#   Source: Wikipedia
#  In air nominally 1 ppm = 1.e-4% = 1.e-6 volume fraction
#    Can reach 100 ppm in closed enviroments such as submarines
#  Explosive at 40,000 ppm = 4%

import time
import grovepi
import math
debug = True

#*****************************Globals***********************************************/
H2Curve = [2.3, 0.93,-1.44] # two points are taken from the curve in datasheet.
#       = log(200), log[Rs/Ro(200ppm)], slope) where
#   slope=(log[Rs/Ro(10000) - log[Rs/Ro(200)]/(log(10,000)-log(200))
#        = (log(0.03) - 0.93)/(4 - 2.3) = -1.44
# with these two points, a line is formed which is "approximately equivalent"
# to the original curve.
# data format:{ x, y, slope}; point1: (lg200, 0.47), point2: (lg10000, -0.92)
# ************************Hardware Related Globals************************************/
MQ_PIN = 0      # define which analog input channel you are going to use
RL_VALUE= 10 # define the load resistance on the board, in kilo ohms
# RO_CLEAN_AIR_FACTOR= (10.) #  was 9.21,RO_CLEAR_AIR_FACTOR=(Sensor resistance in clean air)/RO,
RO_CLEAN_AIR_FACTOR= 10.3 #  was 9.21,RO_CLEAR_AIR_FACTOR=(Sensor resistance in clean air)/RO,
# which is derived from the chart in datasheet
# ***********************Software Related Macros************************************/
CALIBRATION_SAMPLE_TIMES = 10 # define how many samples you are going to take in the calibration phase
CALIBRATION_SAMPLE_INTERVAL = 10. # //define the time interval(in second) between each samples in the
# cablibration phase
READ_SAMPLE_INTERVAL = 10. # define the time interal(in second) between each samples in
READ_SAMPLE_TIMES = 10     # define how many samples you are going to take in normal operation
# normal operation
#**********************Application Related Macros**********************************/
#define GAS_H2 (0)

RoH2 = 1.   # Calibration constant for H2 in clean air
RawH2 = 100. # Average raw value in calabration for H2

debug = True

class MQxSensor(object):
    GasID="H2"
    SensorName="MQ8"
    Ro=RoH2
    ppm=-1.
    RawAve=-1.

    def __init__(self, gasid, sensor_number=MQ_PIN, Debug=False, Rload=RL_VALUE, \
                 rawCleanAir=0, RoCleanAirFactor=RO_CLEAN_AIR_FACTOR, \
                 Ro=RoH2, GasCurve=H2Curve,\
                 ReadWait=READ_SAMPLE_INTERVAL, \
                 ReadIter=READ_SAMPLE_TIMES, \
                 ReadWaitCal=CALIBRATION_SAMPLE_INTERVAL, \
                 ReadIterCal=CALIBRATION_SAMPLE_TIMES ):
       self.gasid = gasid       # e.g MQ8, but is arbitrary name
       self.pin = sensor_number # analog sensor number on GrovePI
       self.debug = Debug
       self.rload = Rload
       self.rawCleanAir = rawCleanAir
       self.RoCleanAirFactor = RoCleanAirFactor
       self.Ro = Ro
       self.GasCurve = GasCurve
       self.ReadWait = ReadWait
       self.ReadIter = ReadIter
       self.ReadWaitCal = ReadWaitCal
       self.ReadIterCal = ReadIterCal
       if self.debug:
           print self.gasid
           print self.pin
           print self.debug
           print self.rload
           print self.rawCleanAir
           print self.Ro
           print self.GasCurve
           print self.ReadWait
           print self.ReadIter
       try:
         grovepi.pinMode(sensor_number,"INPUT")
       except IOError as e:
         print "__init error", e
         
    def Calibrate(self):
     if self.debug: print "Calibrating sensor ", self.gasid
     Ro, RawAve = MQCalibration(self.pin, self.rload, self.RoCleanAirFactor, \
                                self.ReadIterCal, self.ReadWaitCal)
     # Calibrating the sensor. Please make sure the sensor is in clean air
     # when you perform the calibration
     self.Ro = Ro
     self.rawCleanAir = RawAve
     if self.debug: print "Calibration is done.  Ro ", self.gasid," = ", Ro , " kohm, RawAve = ", RawAve
     time.sleep(1.)

    def ReadGas(self):
       rs_ro_ratio = MQRead(self.pin)/self.Ro
       Gas_ppm=MQGetGasPercentage(rs_ro_ratio,self.GasCurve)
       self.Gas_ppm = Gas_ppm
       if self.debug: print "Gas ", self.gasid, ": ",self.Gas_ppm, " ppm"
    time.sleep(10.)


#****************** MQResistanceCalculation ****************************************
#Input: raw_adc - raw value read from adc, which represents the voltage
#Output: the calculated sensor resistance
#Remarks: The sensor and the load resistor forms a voltage divider. Given the voltage
#across the load resistor and its resistance, the resistance of the sensor
#could be derived.
#************************************************************************************/ 
def MQinv(raw_adc):
  voltage = float(raw_adc) / 1024. * 5.
  Inv=float( (1024.-float(raw_adc))/float(raw_adc) )
  if debug:
      print"MQinv, raw ", raw_adc, " Inv ", Inv
  return (Inv)

# /***************************** MQCalibration ****************************************
# Input: mq_pin - analog channel
# Output: Ro of the sensor
# Remarks: This function assumes that the sensor is in clean air. It use
# MQResistanceCalculation to calculates the sensor resistance in clean air
# and then divides it with RO_CLEAN_AIR_FACTOR. RO_CLEAN_AIR_FACTOR is about
# 10, which differs slightly between different sensors.
#************************************************************************************/ 
def MQCalibration(mq_pin,itmax,wait,RL,RoCleanAirFactor):
  val=0
  i=0
  ierr=0
  raw=-1;
  if debug: print "MQCalibration mq_pin ", mq_pin
  while raw < 0 and ierr < 5:
    raw = analog_ave(itmax, mq_pin, wait)
    if raw > 0:
      val = RL*MQinv(raw)/RoCleanAirFactor
    else:
      if debug: print "MQCleanAirFactor IOError: "
      time.sleep(wait)
      ierr += 1
      raw = -ierr
      val=raw
    #endif
  #end while
  if debug: print "MQCalibration: Val,raw ", val, raw
  # val = raw_ave/RO_CLEAN_AIR_FACTOR #  divided by RO_CLEAN_AIR_FACTOR yields the Ro
                                    #  according to the chart in the datasheet
  return(val,raw)

#****************** MQResistanceCalculation ****************************************
#Input: raw_adc - raw value read from adc, which represents the voltage
#Output: the calculated sensor resistance
#Remarks: The sensor and the load resistor forms a voltage divider. Given the voltage
#across the load resistor and its resistance, the resistance of the sensor
#could be derived.
#************************************************************************************/ 
def MQResistanceCalculation(raw_adc):

  Res=float(RL_VALUE)*(1024.-float(raw_adc))/float(raw_adc)
  if debug:
      print"MQResistanceCalculation, raw ", raw_adc, " value ", Res
  return (Res)


# /***************************** MQRead *********************************************
# Input: mq_pin - analog channel
# Output: Rs of the sensor
# Remarks: This function use MQResistanceCalculation to caculate the sensor resistenc (Rs).
# The Rs changes as the sensor is in the different consentration of the target
# gas. The sample times and the time interval between samples could be configured
# by changing the definition of the macros.
# ************************************************************************************/
def MQRead(mq_pin):

  ierr=0
  rs=-1;
  if debug: print "MQRead mq_pin ", mq_pin
  while rs < 0 and ierr < 5:
    rawave = analog_ave(READ_SAMPLE_TIMES, mq_pin, READ_SAMPLE_INTERVAL)
    if rawave > 0:
      rs = MQResistanceCalculation(rawave)
    else:
     if debug: print "MQRead IOError: ", e
     time.sleep(READ_SAMPLE_INTERVAL)
     ierr += 1
     rs = -ierr
  #end while
#  while i<READ_SAMPLE_TIMES:
#    try:
#     i=i+1
#     raw=grovepi.analogRead(mq_pin)
#     rs += MQResistanceCalculation(raw)
#     time.sleep(READ_SAMPLE_INTERVAL)
#    except IOError as e:
#     time.sleep(READ_SAMPLE_INTERVAL)
#     if debug: print "MQRead IOError: ", e
#    # end try
  # end while
  
#  rs = rs/READ_SAMPLE_TIMES

  if debug: print "MQRread rs=",rs

  return(rs)

# /***************************** MQGetGasPercentage **********************************
# Input: rs_ro_ratio - Rs divided by Ro
# gas_id - target gas type
# Output: ppm of the target gas
# Remarks: This function passes different curves to the MQGetPercentage function which
# calculates the ppm (parts per million) of the target gas.
# ************************************************************************************/
# /***************************** MQGetPercentage **********************************
# Input: rs_ro_ratio - Rs divided by Ro
# pcurve - pointer to the curve of the target gas
# Output: ppm of the target gas
# Remarks: By using the slope and a point of the line. The x(logarithmic value of ppm)
# of the line could be derived if y(rs_ro_ratio) is provided. As it is a
# logarithmic coordinate, power of 10 is used to convert the result to non-logarithmic
# value.
# ************************************************************************************/
def MQGetGasPercentage(rs_ro_ratio, pcurve):

  val=10.**(math.log(rs_ro_ratio-pcurve[1])/pcurve[2] + pcurve[0] )
# val=10.**(math.log(rs_ro_ratio-H2Curve[1])/H2Curve[2] + H2Curve[0])
  if debug: print "MQGetPercentage= ", val
  return(val)

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



# test
if debug:
  H2=MQxSensor("H2", 0, True)
  H2.Calibrate()
  H2.ReadGas()
  print "H2 ppm: ", H2.Gas_ppm

