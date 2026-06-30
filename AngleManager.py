import math
class AngleMode:
    '''Stores the current angle mode as a class variable so it is globally accessible.
    All Evaluate() calls read from this — changing it affects every graph simultaneously.'''
    angle_mode='Radians'
    @staticmethod
    def SetAngleMode(mode):
        AngleMode.angle_mode=mode

def ToRadians(angle,angle_mode):
    '''Converts an angle to radians if the mode is Degrees-->math functions always expect radians.'''
    if angle_mode=='Degrees':
        return angle*(math.pi/180)
    else:
        return angle