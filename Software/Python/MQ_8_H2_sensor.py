# *******************Demo for MQ-8 Gas Sensor Module V1.0*****************************
# Modifications by Michael Vander Vorst
# History:
#  Original 2015-05-14 convert to Python for GrovePi
# Originally written for aruino
# Author: Tiequan Shao: tiequan.shao[at]sandboxelectronics.com
# Peng Wei: peng.wei[at]sandboxelectronics.com

# Lisence: Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)
# Note: This piece of source code is supposed to be used as a demostration ONLY. More
# sophisticated calibration is required for industrial field application.

# Sandbox Electronics 2011-04-25
# ************************************************************************************/
# Hydrogen properties by volume:
#   Source: Wikipedia
#  In air nominally 1 ppm = 1.e-4% = 1.e-6 volume fraction
#    Can reach 50 ppm in closed enviroments such as submarines
#  Explosive at 40,000 ppm = 4%

import time
import grovepi
import math
debug=False
# ************************Hardware Related Macros************************************/
MQ_PIN =0      # define which analog input channel you are going to use
RL_VALUE= 10 # define the load resistance on the board, in kilo ohms
RO_CLEAN_AIR_FACTOR= (10.) #  was 9.21,RO_CLEAR_AIR_FACTOR=(Sensor resistance in clean air)/RO,
# which is derived from the chart in datasheet
# ***********************Software Related Macros************************************/
CALIBARAION_SAMPLE_TIMES = 60 # define how many samples you are going to take in the calibration phase
CALIBRATION_SAMPLE_INTERVAL = 1.0 # //define the time interal(in milisecond) between each samples in the
# cablibration phase
READ_SAMPLE_INTERVAL = 0.5 # define how many samples you are going to take in normal operation
READ_SAMPLE_TIMES = 5 # define the time interal(in milisecond) between each samples in
# normal operation
#**********************Application Related Macros**********************************/
#define GAS_H2 (0)
#*****************************Globals***********************************************/
H2Curve = [2.3, 0.93,-1.44] # two points are taken from the curve in datasheet.
# with these two points, a line is formed which is "approximately equivalent"
# to the original curve.
# data format:{ x, y, slope}; point1: (lg200, 0.47), point2: (lg10000, -0.92)

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

# /***************************** MQCalibration ****************************************
# Input: mq_pin - analog channel
# Output: Ro of the sensor
# Remarks: This function assumes that the sensor is in clean air. It use
# MQResistanceCalculation to calculates the sensor resistance in clean air
# and then divides it with RO_CLEAN_AIR_FACTOR. RO_CLEAN_AIR_FACTOR is about
# 10, which differs slightly between different sensors.
#************************************************************************************/ 
def MQCalibration(mq_pin):
  val=0
  i=0
  while i < CALIBARAION_SAMPLE_TIMES:  # take multiple samples
    try:
      raw=grovepi.analogRead(mq_pin)
      val += MQResistanceCalculation(raw)
      i+= 1
      time.sleep(CALIBRATION_SAMPLE_INTERVAL)
    except IOError as e:
      time.sleep(CALIBRATION_SAMPLE_INTERVAL)
      if debug: print "MQCalibration IOError: ", e
    # end try
  # end while
  val = val/CALIBARAION_SAMPLE_TIMES # calculate the average value

  val = val/RO_CLEAN_AIR_FACTOR #  divided by RO_CLEAN_AIR_FACTOR yields the Ro
                                #  according to the chart in the datasheet

  return(val)

# /***************************** MQRead *********************************************
# Input: mq_pin - analog channel
# Output: Rs of the sensor
# Remarks: This function use MQResistanceCalculation to caculate the sensor resistenc (Rs).
# The Rs changes as the sensor is in the different consentration of the target
# gas. The sample times and the time interval between samples could be configured
# by changing the definition of the macros.
# ************************************************************************************/
def MQRead(mq_pin):

  i=0
  rs=0;
  if debug: print "MQRead mq_pin ", mq_pin
  while i<READ_SAMPLE_TIMES:
    try:
     i=i+1
     raw=grovepi.analogRead(mq_pin)
     rs += MQResistanceCalculation(raw)
     time.sleep(READ_SAMPLE_INTERVAL)
    except IOError as e:
     time.sleep(READ_SAMPLE_INTERVAL)
     if debug: print "MQRead IOError: ", e
    # end try
  # end while
  
  rs = rs/READ_SAMPLE_TIMES

  if debug: print "MQRread rs=",rs

  return(rs)

# /***************************** MQGetGasPercentage **********************************
# Input: rs_ro_ratio - Rs divided by Ro
# gas_id - target gas type
# Output: ppm of the target gas
# Remarks: This function passes different curves to the MQGetPercentage function which
# calculates the ppm (parts per million) of the target gas.
# ************************************************************************************/
def MQGetGasPercentage(rs_ro_ratio, gas_id):

    if debug:  print "MQGetGasPercentage, ratio ", rs_ro_ratio, " gas_id: ", gas_id
    val=MQGetPercentage(rs_ro_ratio,H2Curve)
    if debug: print"MQGetGasPercentage=", val 
    return (val)

# /***************************** MQGetPercentage **********************************
# Input: rs_ro_ratio - Rs divided by Ro
# pcurve - pointer to the curve of the target gas
# Output: ppm of the target gas
# Remarks: By using the slope and a point of the line. The x(logarithmic value of ppm)
# of the line could be derived if y(rs_ro_ratio) is provided. As it is a
# logarithmic coordinate, power of 10 is used to convert the result to non-logarithmic
# value.
# ************************************************************************************/
def MQGetPercentage(rs_ro_ratio, pcurve):

  val=10.**(math.log(rs_ro_ratio-pcurve[1])/pcurve[2] + pcurve[0] )
# val=10.**(math.log(rs_ro_ratio-H2Curve[1])/H2Curve[2] + H2Curve[0])
  if debug: print "MQGetPercentage= ", val
  return(val)


def setup():
# air sensor
  grovepi.pinMode(MQ_PIN,"INPUT")
  if debug: print("Calibrating.H2 sensor..")
  Ro = MQCalibration(MQ_PIN)  # Calibrating the sensor. Please make sure the sensor is in clean air
                              # when you perform the calibration
  print "Calibration H2 is done.  Ro= ", Ro , " kohm"
  time.sleep(1.)

def loop():
  print "loop"
  while True:
    H2ppm=MQGetGasPercentage(MQRead(MQ_PIN)/Ro,"GAS_H2")
    print "H2: ",H2ppm, " ppm"
    time.sleep(10.)

Ro = 10. # Ro is initialized to 10 kilo ohms
H2ppm=-1.
setup()
loop()
