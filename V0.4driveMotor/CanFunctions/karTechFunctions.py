'''
Matthew Tuer, April 2025
mtuer@uwaterloo.ca/matthewjtuer@gmail.com
'''
previousHeartbeat=0
missedHeartbeats=0
speedCount=0
turnCount=0
previousStop=0
enableLatch=True
forward=1
backward=0
conflictingStatusCount=0

    
def calculateControls(
    Heartbeat, previousHeartbeat, rfLink, 
    button1, button2, button3, button4, button5, 
    button6, button7, stop, previousStop, outputStatus):
    
    global speedCount, turnCount, enableLatch
    global forward, backward, missedHeartbeats, conflictingStatusCount
    
 
    maxSpeed = 50
    maxTurn = 30

    # Toggle latch if stop button changes state
    if stop and stop != previousStop:
        enableLatch = not enableLatch

    # Ensure outputStatus matches enableLatch
    conflictingStatusCount = conflictingStatusCount + 1 if outputStatus != enableLatch else 0
    if conflictingStatusCount > 5:
        enableLatch = int(outputStatus)

    # Monitor heartbeats
    missedHeartbeats = missedHeartbeats + 1 if Heartbeat == previousHeartbeat else 0
    
    #only allow movment if less than5 missed HB, remote connected and enable is selected 
    allowMovment = missedHeartbeats < 5 and rfLink and enableLatch 

    if not allowMovment:
        speedCount = 0

    # Forward/backward selection
    if button3:
        forward, backward, speedCount = 1, 0, 0
    elif button5:
        forward, backward, speedCount = 0, 1, 0

    # Adjust turn count
    if button1 and allowMovment:
        turnCount -= 0.25
    elif button2 and allowMovment:
        turnCount += 0.25

    # Adjust speed count
    if button4 and allowMovment:
        speedCount += 5
    elif button6 and allowMovment:
        speedCount -= 5

    # Limit speedCount and turnCount
    speedCount = max(-maxSpeed, min(maxSpeed, speedCount))
    turnCount = max(-maxTurn, min(maxTurn, turnCount))

    return allowMovment, forward, backward, turnCount, speedCount

        

def checkOutputStatus(payload):
    if payload[0]==128:
        return True
    else: return False 
    
        
def unPackButtonStatus(payload,outputStatus=None,full=True,returnControls=True,debug=True):
    '''
    returnControls=False and full=True
    will return the raw values of all buttons,heartbeat, Rflink and button power
    
    returnControls=False and full=False
    will return the raw values of all buttons
    
    returnControls=True
    will return values in form of controls as defined in calculateControls function
    enableMovment,Forward,backward,turn,speed
    only need to include output status in this case 
    '''
    global previousHeartbeat
    global previousStop
    Data=payload[0]|(payload[1]<<8)|(payload[2]<<16)|(payload[3]<<24)
    Heartbeat=(Data>>0)&0x01
    rfLink= (Data>>1)&0x01
    button1=(Data>>16)&0x01
    button2=(Data>>17)&0x01
    button3=(Data>>18)&0x01
    button4=(Data>>19)&0x01
    button5=(Data>>20)&0x01
    button6=(Data>>21)&0x01
    button7=(Data>>22)&0x01
    button8=(Data>>23)&0x01
    buttonPWR=(Data>>24)&0x01
    if debug:
        print("--------------REMOTE INFO--------------")
        print("RAW: %s" %payload.hex())
        print("Heartbeat:%s"%Heartbeat)
        print("rfLink:%s"%rfLink)
        print("buttonPWR:%s"%buttonPWR)
        print("B1:%s |B2:%s |B3:%s |B4:%s |B5:%s |B6:%s |B7:%s |B8:%s |"%(button1,button2,button3,button4,button5,button6,button7,button8))
        print("---------------------------------------")
    
    if returnControls:
        allowMovment,forward,backward,turnCount,speedCount=calculateControls(Heartbeat,previousHeartbeat,rfLink,button1,button2,button3,button4,\
                      button5,button6,button7,button8,previousStop,outputStatus)
        previousHeartbeat=Heartbeat
        previousStop=button8
        return allowMovment,forward,backward,turnCount,speedCount
    
    if not full: return button1,button2,button3,button4,button5,button6,button7,button8
    return Heartbeat,rfLink,button1,button2,button3,button4,button5,button6,button7,button8,buttonPWR
    
    

def unPackSystemStatus(payload,full=False,debug=False):
    Data=payload[0]|(payload[1]<<8)|(payload[2]<<16)
    batteryVoltage=((Data>>0)&0xFFFF)*.05
    lowBattery=(Data>>16)&0x01
    txNotNeutral=(Data>>17)&0x01
    if debug:
        print("-------------SYSTEM INFO---------------")
        print("RAW: %s" %payload.hex())
        print("batteryVoltage:%s"%batteryVoltage)
        print("lowBattery:%s"%lowBattery)
        print("txNotNeutral:%s"%txNotNeutral)
        print("---------------------------------------")
    if not full: return batteryVoltage,lowBattery
    return batteryVoltage,lowBattery,txNotNeutral
    

