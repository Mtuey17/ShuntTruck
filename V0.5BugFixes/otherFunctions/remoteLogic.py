import time


def calculateControls(data,feedBackSteeringPos,speedCount,previousDirection):
    
    
    #----Turning logic-----
    maxTurn=400000
    turnSpeed=0
    if data[0]: turnSpeed=35000
    elif data[1]: turnSpeed=-35000
    else:
        turnSpeed=0
        
    if (feedBackSteeringPos>=maxTurn and data[1]) or (feedBackSteeringPos<=-maxTurn and data[0]):
        turnSpeed=0
    
    

    #-----Forward/backward logic-----
    forward=True
    if data[4]: forward=False
    
    if (previousDirection!=forward)or data[6]:
        speedCount=0
        
    
    
 
        

        
    
    #-----speed logic-----
    speedLimit=100
    speedFactor=1
    
    
    if data[3] and forward:speedCount+=speedFactor
    elif data[5] and forward:speedCount-=speedFactor
    
    if data[3] and not forward:speedCount-=speedFactor
    elif data[5] and not forward:speedCount+=speedFactor
    
    
    
    
    speedCount = max(0,min(speedLimit,speedCount))
    toSendSpeed=speedCount
    if not forward:
        toSendSpeed=speedCount*-1
        
    return turnSpeed,speedCount,toSendSpeed,forward
  
    
 
    
    


