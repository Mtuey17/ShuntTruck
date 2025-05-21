'''
Matthew Tuer, April 23, 2025
mtuer@uwaterloo.ca/matthewjtuer@gmail.com

Shunt Truck V0.1

version notes:

-running relay card at 256000 baud instead of 115200
allows the loop to run much faster.
previously took ~15ms to just  read digital inputs
now takes ~7ms. will keep testing to ensure reliability is not an issue


-steering motor and steering pump logic has been added
buttons 1 and 2 on remote control steer direction
pump will be enabled whenever motor is in motion
running steering motor in velocity mode rather than position mode

'''

from mcp2515.canio import Message, RemoteTransmissionRequest
from mcp2515.config import spi, CS_PIN
from mcp2515 import MCP2515 as CAN
import gc
import time
from machine import Pin,UART
from Modbus.waveshareRelayModules import RelayTypeD
from otherFunctions.remoteLogic import calculateControls
from CanFunctions.NiMotionFunctions import packPositionData,unPackPostionFeedback


def CANReceive():
    global feedBackSteeringPos
    with can_bus.listen(timeout=0.005) as listener:
        message_count = listener.in_waiting()
        for _i in range(message_count):
            msg = listener.receive()
            if not isinstance(msg,Message):
                continue
            
           # print("ID:%s"%msg.id)
            #print("data:%s"%msg.data.hex())
            
            #Can messages work weird for Nimotion motor, cant just go by ID 
            if msg.id==1409 and hex(msg.data[0])=="0x43" and hex(msg.data[1])=="0x64" and hex(msg.data[2])=="0x60":
               # print((msg.data).hex())
                #print("unpack")
                feedBackSteeringPos=unPackPostionFeedback(msg.data)
                    
def CANSend(messageinfo,data):
    
    toSend=bytearray(data)
    message = Message(id=messageinfo, data=toSend, extended=False)
    send_success = can_bus.send(message)


        
    
    
    
    
    
    
    

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

CANSend(NiMotion,init1)
CANSend(NiMotion,accelTimeMs)
CANSend(NiMotion,deAccelTimeMs)
CANSend(NiMotion,initialSpeed)
CANSend(NiMotion,ProfileVelocityMode)
CANSend(NiMotion,init2)
CANSend(NiMotion,init3)
CANSend(NiMotion,init4)









#init relay card 
RS485=UART(1, baudrate=256000, tx=17, rx=18)
RelayCard=RelayTypeD(RS485,0x01)#will not change address if you set it to the wrong one
steeringPump=Pin(41, Pin.OUT) #relay 1
steeringPump.off()
time.sleep(1.5)




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




loopSpeedMS=25 #45ms=22.2 Hz
startTime = time.ticks_ms()/1000
lastSteeringUpdate=startTime

while 1:
    currentTime=time.ticks_ms()/1000
    
    
        
    if currentTime>=startTime:

        while RS485.any():
            #if there is data here find where is coming from and fix there!
            print("BAD DATA: %s" %(RS485.read()))
        
        
        #------relay card and remote logic-------
        if 	RelayCard.inputs[7]==1:
            controlErrorFlag=True
            speedCount=0
            toSendSpeed=0
        else:
            controlErrorFlag=False
            previousTurnSpeed=turnSpeed
            turnSpeed,speedCount,toSendSpeed,forward=calculateControls(RelayCard.inputs,feedBackSteeringPos,speedCount)
            
            
            
        #-------steering logic---------
        #keeping pump on 500ms after requesting 0 speed 
        if (abs(previousTurnSpeed)>0 and turnSpeed==0):
            pumpDelay=True
            print("pumpdelayon")
            pumpDelayTimer=time.ticks_ms()/1000
        if time.ticks_ms()/1000>pumpDelayTimer+((pumpDelayMs)/1000):
            pumpDelay=False    
        if turnSpeed!=0 or pumpDelay:
            steeringPump.on()
        else:
            steeringPump.off()
        packedData=packPositionData(turnSpeed)
        
        if previousTurnSpeed!=turnSpeed:
            CANSend(NiMotion,packedData)
        
        
        
        

            
        
        
        
        
        
        
        
        print("-------")
        print("controller error: %s" %controlErrorFlag)
        print("requested steering speed: %s" %turnSpeed)
        print("steering position:    %s" %feedBackSteeringPos)
        print("Speed: %s rpm" %toSendSpeed)
        print("Forward: %s" %forward)
       
       
        
        CANSend(NiMotion,feedbackPosition)#requesting feedback position from steering motor
        
        CANReceive()
        RelayCard.updateInputs()
        RelayCard.flipRelays()
        endTime = time.ticks_ms()/1000
        computeTime=(endTime-currentTime)*1000
        extraTime=(loopSpeedMS/1000-computeTime/1000)
        startTime=endTime+extraTime
        print("ComputeTime:%sms" %computeTime)
        
        
    



