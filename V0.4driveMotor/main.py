'''
Matthew Tuer, April 24, 2025
mtuer@uwaterloo.ca/matthewjtuer@gmail.com

Shunt Truck V0.4

version notes:

-issue with the pump
pulls too much current for powersupply
causes the 24-50V converter to brown out for a second
can bus will also die sometimes when running pump
incorrect reading from relay card DI aswell when running pump
hoping that once a proper power source is hooked up this behaviour stops

-now inverting speed increase/decrease buttons depending on direction
same logic is used on hydraulic truck 

-rear tank sensor not working right
front sensor seems to be off a bit, but good enough
might just use front tank value 


'''

from mcp2515.canio import Message, RemoteTransmissionRequest
from mcp2515.config import spi, CS_PIN
from mcp2515 import MCP2515 as CAN
import gc
import time
import machine
from machine import Pin,UART,ADC
from Modbus.waveshareRelayModules import RelayTypeD
from otherFunctions.remoteLogic import calculateControls
from CanFunctions.NiMotionFunctions import packPositionData,unPackPostionFeedback
from CanFunctions.ctsBMS import unPackPowerLimits,unPackBMSInfoOne
from CanFunctions.TM4Functions import packCommandSafety,packCommandOne,packCommandTwo,unpackMCUInfo1,TM4Bootup
from analogSensors.pressureSensor import PT05,PT010

def CANReceive():
    global powerDischargePeak,PowerDischargeContinue,PowerChargePeak,powerChargeContinue
    global BmsVolBat,BmsCurBat,BmsSoc
    global feedBackSteeringPos
    global highPowerVoltage
    with can_bus.listen(timeout=0.005) as listener:
        message_count = listener.in_waiting()
        for _i in range(message_count):
            msg = listener.receive()
            if not isinstance(msg,Message):
                continue
                 
            #CAN messages work weird for Nimotion motor, cant just go by ID 
            if msg.id==1409 and hex(msg.data[0])=="0x43" and hex(msg.data[1])=="0x64" and hex(msg.data[2])=="0x60":
                feedBackSteeringPos=unPackPostionFeedback(msg.data)
            if hex(msg.id)=="0x1e1":#BMS Info 1 message
                
                BmsVolBat,BmsCurBat,BmsSoc=unPackBMSInfoOne(msg.data,debug=False)
                   
            if hex(msg.id)=="0x1f3":# BMSpower limits 
                powerDischargePeak,PowerDischargeContinue,PowerChargePeak,powerChargeContinue=unPackPowerLimits(msg.data,debug=False)
            
            #---------TM4 Motor messages-----------------
            if hex(msg.id)=="0x440":
                highPowerVoltage=unpackMCUInfo1(msg.data)

            

def sendCanMessages(timer):
    global previousTurnSpeed,turnSpeed,NiMotion#steering variables
    global RPM,rollingCount,driveMotorCommandSafety,driveMotorCommand1,driveMotorCommand2
    global operationRequest,MaxChargeCurrent,maxDischargeCurrent,MaxBatteryVoltage,minBatteryVoltage,safetyRPM
    global operationalMode,commandMode,speedCommandStatus

        
    
    #--------TM4 Motor CAN messages--------   
    #safety
    commandSafetyData=packCommandSafety(safetyRPM,rollingCount)
    CANSend(driveMotorCommandSafety,commandSafetyData) 
    #command1
    commandOneData=packCommandOne(operationRequest,MaxChargeCurrent,maxDischargeCurrent,MaxBatteryVoltage,minBatteryVoltage,rollingCount)
    CANSend(driveMotorCommand1,commandOneData)
    #command2
    commandTwoData=packCommandTwo(operationalMode,commandMode,speedCommandStatus,RPM,rollingCount)
    CANSend(driveMotorCommand2,commandTwoData)
    
    
    
    

    if previousTurnSpeed!=turnSpeed:
        packedData=packPositionData(turnSpeed)
        CANSend(NiMotion,packedData,steering=True)    
    CANSend(NiMotion,feedbackPosition,steering=True)#requesting feedback position from steering motor
    
                
def CANSend(messageinfo,data,ext=False,steering=False,debug=False):
    
    if steering:
        toSend=bytearray(data)
        message = Message(id=messageinfo, data=toSend, extended=False)
        send_success = can_bus.send(message)
    else:
        DCL=messageinfo[1]
        if len(data)!=DCL:
            print("data does not match DCL! Exiting..")
            return -1
        toSend=bytearray(data)
        message = Message(id=messageinfo[0], data=toSend, extended=ext)
        send_success = can_bus.send(message)
        if debug:
            print("Send success:", send_success)
            print("ID:%s|DCL:%s|Payload:%s"  %(hex(messageinfo[0]),hex(DCL),toSend.hex()))
        
#------------------------------------------------------------------------
    
    
#init Canbus 
can_bus = CAN(spi, CS_PIN,baudrate=250_000, loopback=False, silent=False)


#------init for NiMotion motor (steering)-------
motorID=0x601
NiMotion=motorID
feedbackPosition=[0x40,0x64,0x60,0x00,0x00,0x00,0x00,0x00]
accelTimeMs=[0x23,0x83,0x60,0x00,0x75,0x30,0x00,0x00]
deAccelTimeMs=[0x23,0x84,0x60,0x00,0xEA,0x60,0x00,0x00]
initialSpeed=[0x23,0x08,0x20,0x00,0x0A,0x00,0x00,0x00]
ProfileVelocityMode=[0x2F,0x60,0x60,0x00,0x03,0x00,0x00,0x00]#turn to velocity mode
init1=[0x2B,0x40,0x60,0x00,0x00,0x00,0x00,0x00]
init2=[0x2B,0x40,0x60,0x00,0x06,0x00,0x00,0x00]#switch driver state machine 1
init3=[0x2B,0x40,0x60,0x00,0x07,0x00,0x00,0x00]#switch driver state machine 2
init4=[0x2B,0x40,0x60,0x00,0x0F,0x00,0x00,0x00]#switch driver state machine 4
CANSend(NiMotion,init1,steering=True)
CANSend(NiMotion,accelTimeMs,steering=True)
CANSend(NiMotion,deAccelTimeMs,steering=True)
CANSend(NiMotion,initialSpeed,steering=True)
CANSend(NiMotion,ProfileVelocityMode,steering=True)
CANSend(NiMotion,init2,steering=True)
CANSend(NiMotion,init3,steering=True)
CANSend(NiMotion,init4,steering=True)


#init relays
RS485=UART(1, baudrate=256000, tx=17, rx=18)
#Waveshare Relays
RelayCard=RelayTypeD(RS485,0x01)#will not change address if you set it to the wrong one
RelayCard.fanAndPump=0
RelayCard.remoteSignal=1
RelayCard.brakesOff=0
RelayCard.dumpAirDryer=0


#ESP relays
airDryer=Pin(1, Pin.OUT)#relay1
notUsed=Pin(2,Pin.OUT)#relay2
steeringPump=Pin(41, Pin.OUT)#relay3
highVBattEnab=Pin(42, Pin.OUT)#relay4
airCompressor=Pin(45,Pin.OUT)#relay5
notUsed2=Pin(46, Pin.OUT)#relay6
airDryer.off()
notUsed.off()
steeringPump.off()

#highVBattEnab.off()
highVBattEnab.on()

notUsed2.off()
time.sleep(2)


#BMS Setup
powerDischargePeak=0
PowerDischargeContinue=0
PowerChargePeak=0
powerChargeContinue=0
BmsVolBat=0
BmsCurBat=0
BmsSoc=0


#pressure sensor setup
rearTank=PT05(6)#0-5V sensor 
frontTank=PT010(7)#0-10V sensor 


#----variables for Remote and steering------
turnSpeed=0
feedBackSteeringPos=0
speedCount=0
toSendSpeed=0
previousTurnSpeed=0
forward=False
controlErrorFlag=False
pumpDelay=False
pumpDelayTimer=0
pumpDelayMs=500
previousDirection=False 
#-------------Drive motor bootup------------------
#drive motor commands 
driveMotorProtocolVersion=[0x444,2]#ID,DCL
ProtocolVersion=[0x04,0x00] #ensure length matches DCL
driveMotorCommandSafety=[0x42,5]
driveMotorCommand1=[0x40,8]
driveMotorCommand2=[0x41,6]
TM4Init=False
driveMotorInit=0
#command safety data
safetyRPM=100
rollingCount=14
#command one data
operationRequest=0#0 standby,1 operational, 2 shutdown
MaxChargeCurrent=2 #A
maxDischargeCurrent=5 #A
MaxBatteryVoltage=400 #V
minBatteryVoltage=200 #V
minBatterVoltageStatus=0#0=Valid, 1=Invalid 
maxDischargeCurrentStatus=0
maxChargeCurrentStatus=0
maxbatteryVoltageStatus=0
#command two data
operationalMode=0
commandMode=2
speedCommandStatus=0
RPM=0

highPowerVoltage=0
requiredPrechargeVoltage=250
prechargeVoltageMet=False 
#do this once on boot 
CANSend(driveMotorProtocolVersion,ProtocolVersion)


#---------------------------------------------





#-------Timing-----------
#hardware interupt for sending CAN messages at same time interval
timer1 = machine.Timer(0)
timer1.init(period=20, mode=machine.Timer.PERIODIC, callback=sendCanMessages) #was 20
loopSpeedMS=30 #45ms=22.2 Hz


#print timer 
updatePrints=0
updatRate=0.5 #second(s)
updateInterval=int(1/(loopSpeedMS/1000)*updatRate)


#sensor timer 
updateSensors=0
sensorUpdatRate=0.5 #second(s)
sensorUpdateInterval=int(1/(loopSpeedMS/1000)*sensorUpdatRate)


startTime = time.ticks_ms()/1000
lastSteeringUpdate=startTime

while 1:
    currentTime=time.ticks_ms()/1000
    
    
    if currentTime>=startTime:

        while RS485.any():
            #if there is data here find where is coming from and fix there!
            print("BAD DATA: %s" %(RS485.read()))
        
    
     
        
        
        
        
        
        #Drive Motor Logic    
        MaxChargeCurrent=int(PowerChargePeak)
        maxDischargeCurrent=int(powerDischargePeak)
        if TM4Init:
            RPM=toSendSpeed
            
        rollingCount+=1
        if rollingCount==16:
            rollingCount=1
        TM4Init,prechargeVoltageMet,driveMotorInit,operationRequest,operationalMode,RPM=TM4Bootup(operationRequest,operationalMode,RPM,TM4Init,highPowerVoltage,prechargeVoltageMet,driveMotorInit)
        
    
        #------relay card and remote logic-------

        
        if RelayCard.inputs[7]==1:
            controlErrorFlag=True
            speedCount=0
            toSendSpeed=0
        else:
            controlErrorFlag=False
            previousTurnSpeed=turnSpeed
            previousDirection=forward
            turnSpeed,speedCount,toSendSpeed,forward=calculateControls(RelayCard.inputs,feedBackSteeringPos,speedCount,previousDirection)
            
            
        #-------steering logic---------
        #keeping pump on 500ms after requesting 0 speed 
        if (abs(previousTurnSpeed)>0 and turnSpeed==0):
            pumpDelay=True
            pumpDelayTimer=time.ticks_ms()/1000
        if time.ticks_ms()/1000>pumpDelayTimer+((pumpDelayMs)/1000):
            pumpDelay=False
            
        #print(previousTurnSpeed) 
            
        if turnSpeed!=0 or pumpDelay:
            steeringPump.on()
        else:
            steeringPump.off()
        
        
        
         #---TEST turning on air compressor with button 7---
        if RelayCard.inputs[6]==1:
            airCompressor.on()
        else:
            airCompressor.off()
            
        #-------Sensor Logic--------
        updateSensors+=1
        if updateSensors==sensorUpdateInterval:
            rearTank.read()
            frontTank.read()
            updateSensors=0
            
        
        #-----------Prints---------------
        updatePrints+=1
        if updatePrints==updateInterval:
            steeringMessages=False
            driveMotorMessages=False
            bmsMessages=False
            analogSensorMessages=True
            
            if steeringMessages:
                print("-------Steering Messages-------")
                print("controller error: %s" %controlErrorFlag)
                print("requested steering speed: %s" %turnSpeed)
                print("steering position:    %s" %feedBackSteeringPos)
                print("Speed: %s rpm" %toSendSpeed)
                print("Forward: %s" %forward)
                print(" ")
            if driveMotorMessages:
                print("------Drive Motor Messages-----")
                print("TM4 Init: %s " %TM4Init)
                print("Precharge Voltage: %s V" %highPowerVoltage)
                print("Speed: %s rpm" %toSendSpeed)
                print("Forward: %s" %forward)
                print(" ")
                
            if bmsMessages:
                print("---------BMS Messages----------")
                print("BMS PDP: %s" %powerDischargePeak) #to tm4?
                print("BMS PDC: %s" %PowerDischargeContinue)
                print("BMS PCP: %s" %PowerChargePeak)#to tm4?
                print("BMS PCC: %s" %powerChargeContinue)
                print("Battery Voltage: %s" %BmsVolBat)
                print("Battery curBat: %s" %BmsCurBat)
                print("Battery SOC: %s" %BmsSoc)
                print(" ")
            if analogSensorMessages:
                print("---------Sensor Messages----------")
                #print("Rear Tank: %s PSI" %rearTank.pressurePSI)
                print("Front Tank: %s PSI" %frontTank.pressurePSI) 
                print(" ")
                
            print("ComputeTime:%sms" %computeTime)
            updatePrints=0
            
             
        
        
        CANReceive()
        RelayCard.updateInputs()
        RelayCard.flipRelays()
        
        
        
        endTime = time.ticks_ms()/1000
        computeTime=(endTime-currentTime)*1000
        extraTime=(loopSpeedMS/1000-computeTime/1000)
        startTime=endTime+extraTime
        
        
        
    



