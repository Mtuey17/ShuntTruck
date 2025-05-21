import time


def calculateControls(data,feedBackSteeringPos,speedCount):
    
    
    #----Turning logic-----
    maxTurn=400000
    turnSpeed=0
    if data[0]: turnSpeed=35000
    elif data[1]: turnSpeed=-35000
    if (feedBackSteeringPos>=maxTurn and data[1]) or (feedBackSteeringPos<=-maxTurn and data[0]):
        turnSpeed=0
    
    

    #-----Forward/backward logic-----
    forward=True
    if data[4]: forward=False

        
    
    #-----speed logic-----
    speedLimit=200
    speedFactor=10
    if data[3]:speedCount+=speedFactor
    elif data[5]:speedCount-=speedFactor
    speedCount = max(0,min(speedLimit,speedCount))
    toSendSpeed=speedCount
    if not forward:
        toSendSpeed=speedCount*-1
        
    return turnSpeed,speedCount,toSendSpeed,forward
  
    
 
    
    


