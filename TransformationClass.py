from abc import abstractmethod
from GraphClass import * 
from Traverse import *
from EquationAnalysis import *
from SplitCoordinates import SplitCoordinates
class Transformation:
    '''Abstract base class for all transformation types.
        Each subclass must implement Apply() to transform coordinates
        and GetDescription() to return a description of the transformation. Helps complete objective:
        Written descriptions of the transformation type must be provided for. and objective: The program must be able to support transformation types such as translations, 
        reflections and stretches for all appropriate graph types. '''
    @abstractmethod
    def Apply(self,coordinates):
        pass
    @abstractmethod 
    def GetDescription(self):
        pass

class Translation(Transformation):
    '''Shifts all coordinates by a fixed amount in the x or y direction.
    display_dx/display_dy store the absolute value for description purposes,
    direction is communicated through the description text rather than the number itself.'''
    def __init__(self,dx,dy,display_dx=None,display_dy=None):
        '''Parameters:
            dx (float)-->horizontal shift, negative moves left
            dy (float)-->vertical shift, negative moves down
            display_dx (float)-->optional override for the value shown in descriptions
            display_dy (float)-->optional override for the value shown in descriptions'''
        self.dx=dx
        self.dy=dy
        if display_dx is not None:
            self.display_dx=display_dx
        else:
            self.display_dx=abs(dx)
        if display_dy is not None:
            self.display_dy=display_dy
        else:
            self.display_dy=abs(dy)

    def Apply(self,coordinates):
        '''Shifts every coordinate in the list by dx and dy.
        Input and output are both lists of (x,y) tuples. Coordinates are split into
        two flat map objects, shifted, then zipped back into a list of tuples.
        None values are preserved, they represent asymptotes in tan graphs.
        Parameters: 
        coordinates (list)-->list of (x,y) tuples
        Returns: 
        list of shifted (x,y) tuples'''
        x_translated,y_translated=SplitCoordinates(coordinates)
        x_translated=map(lambda x:(x+self.dx) if x is not None else None,x_translated )
        y_translated=map(lambda y: (y+self.dy)if y is not None else None,y_translated)
        translated=list(zip(x_translated,y_translated))
        return translated
    
    def GetDescription(self):
        '''Returns a description of the translation direction and magnitude.
        Direction is determined by the sign of dx or dy.
        Parameters: none
        Returns: 
        description string e.g. "Translation 3 units to the right."'''
        if self.dx!=0:
            if self.dx<0:
                return f'Translation {self.display_dx} units to the left.'
            else:
                return f'Translation {self.display_dx} units to the right.'
        if self.dy!=0:
            if self.dy<0:
                return f'Translation {self.display_dy} units down.'
            else:
                return f'Translation {self.display_dy} units up.'
            
class Enlargement(Transformation):
    ''' Stretches coordinates in either the x or y direction by a scale factor.
    Only one of factor_x or factor_y is non-zero per instance,
    x and y stretches are always stored and applied separately.'''
    def __init__(self,factor_x,factor_y):
        '''Parameters:
            factor_x (float)-->x stretch factor, 0 means no x stretch
            factor_y (float)-->y stretch factor, 0 means no y stretch'''
        self.factor_x=factor_x
        self.factor_y=factor_y

    def Apply (self,coordinates):
        '''Stretches coordinates in x or y depending on which factor is non-zero.
        Input and output are both lists of (x,y) tuples. Coordinates are split into
        two flat sequences, one is scaled, then both are zipped back into tuples.
        X stretch divides x by factor_x-->opposite is expected.
        Y stretch multiplies y directly by factor_y.
        None values are preserved for tan asymptotes.
        Parameters: 
        coordinates (list)-->list of (x,y) tuples
        Returns: 
        list of stretched (x,y) tuples'''
        x_enlarged,y_enlarged=SplitCoordinates(coordinates) #split into two flat sequences
        if self.factor_x!=0:
            x_enlarged=map(lambda x:(x/self.factor_x) if x is not None else None,x_enlarged)
            #x stretch-->divide
        elif self.factor_y!=0:
            y_enlarged=map(lambda y: (y*self.factor_y) if y is not None else None,y_enlarged)
            #y stretch-->multiply
        enlarged=list(zip(x_enlarged,y_enlarged))
        return enlarged
            
    def GetDescription(self):
        '''Returns a description of the stretch direction and scale factor.
        For x stretches the displayed factor is inverted-->factor_x is stored as the divisor
        so 1/factor_x gives the actual scale factor seen by the user.
        Parameters: 
        none
        Returns: 
        description string e.g. "Stretch by a scale factor of 2 in the x direction."'''
        if self.factor_x!=0:
            return f'Stretch by a scale factor of {1/self.factor_x} in the x direction.'
        if self.factor_y!=0:
            return f'Stretch by a scale factor of {self.factor_y} in the y direction.'

class Reflection(Transformation):
    '''Reflects all coordinates in either the x or y axis.'''
    def __init__(self,axis):
        '''Parameters: 
        axis (str)-->'x' to reflect in the x axis, 'y' to reflect in the y axis'''
        self.axis=axis

    def Apply(self,coordinates):
        ''' Negates either y values (reflection in x axis) or x values (reflection in y axis).
        Input and output are both lists of (x,y) tuples. Each tuple is rebuilt with the
        appropriate value negated. None values are preserved asymptotes.
        Parameters: 
        coordinates (list)-->list of (x,y) tuples
        Returns: 
        list of reflected (x,y) tuples'''
        reflected=[]
        if self.axis=='x':
            for x,y in coordinates:
                reflected.append((x,-y if y is not None else None)) #flip y, preserve None for asymptotes.
        elif self.axis=='y':
            for x,y in coordinates: 
                reflected.append((-x,y if y is not None else None)) #flip x, preserve None for asymptotes.
        return reflected    
         
    def GetDescription(self):
        '''Returns a readable description of the reflection axis.
        Parameters: 
        none
        Returns: 
        description string e.g. "Reflection in the x axis."'''
        if self.axis=='x':
            return f'Reflection in the x axis.'
        if self.axis=='y':
            return f'Reflection in the y axis.'
        
class Rotation(Transformation):
    ''' Rotates all coordinates by a given angle around a centre point using a 2D rotation matrix.
    If the centre is not the origin, matrix subtraction is carried out.'''
    def __init__(self,angle,centre=(0,0),clockwise=False):
        ''' Parameters:
            angle (float)-->rotation angle in degrees
            centre (tuple)-->point to rotate around, defaults to origin
            clockwise (bool)-->True for clockwise rotation, False for anticlockwise'''
        self.angle=angle
        self.centre=centre
        self.clockwise=clockwise

    def CreateMatrix(self,coordinates):
        '''Converts a list of (x,y) tuples into column vector form for matrix multiplication.
        Each point becomes [[x],[y]]-->a 2x1 column vector.
        Parameters: 
        coordinates (list)-->list of (x,y) tuples
        Returns: 
        list of 2x1 column vectors'''
        matrix=[]
        for x,y in coordinates:
            matrix.append([[x],[y]]) #wrap each point as a column vector for matrix multiplication.
        return matrix

    def MatrixSubtraction(self,coordinates):
        '''
    Translates all coordinates so the rotation centre becomes the origin.
    The standard 2D rotation matrix always rotates around (0,0), so to rotate around
    an arbitrary centre like (3,4), we subtract that centre first to make it the origin,
    apply the rotation, then add it back in Apply() to restore the correct position.
    Parameters: 
    coordinates (list) — list of (x,y) tuples
    Returns: 
    list of 2x1 column vectors with centre shifted to origin'''
        result=[]
        matrix=self.CreateMatrix(coordinates)
        cx,cy=self.centre
        for i in range(len(matrix)):
            #subtract centre from each point to shift the rotation centre to the origin
            result.append([[matrix[i][0][0]-cx],[matrix[i][1][0]-cy]])
        return result

    def Apply(self,coordinates):
        ''' Applies a 2D rotation matrix to all coordinates.
        There are three lists involved:
        - matrix: list of 2x1 column vectors (one per point)
        - multiplied: flat list of alternating rotated x and y values
        - four_dimension: list of single-element lists rebuilt from multiplied
        - final: list of (x,y) tuples, the output format
        For non-origin centres, coordinates are shifted to origin via MatrixSubtraction,
        rotated, then shifted back by adding the centre coordinates.
        Clockwise rotation is achieved by negating the angle before building the matrix.
        Parameters: 
        coordinates (list)-->list of (x,y) tuples
        Returns:
        list of rotated (x,y) tuples'''
        multiplied=[]
        four_dimension=[]
        final=[]
        angle=math.radians(self.angle) #rotation matrix requires radians
        if self.clockwise:
            angle=-angle #negate angle for clockwise rotation
        cx,cy=self.centre
        rotation_mat=[[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]] #the rotation matrix equation.
        if self.centre!=(0,0):
            #shift centre to origin before rotating so the rotation matrix works correctly
            matrix=self.MatrixSubtraction(coordinates)
        else:
            matrix=self.CreateMatrix(coordinates) 
        for i in range(len(matrix)):
            x=matrix[i][0][0]
            y=matrix[i][1][0]
            if x is None or y is None:
                #preserve None pairs for asymptotes
                multiplied.append(None)
                multiplied.append(None)
            else:
                #apply rotation matrix: [cos*x-sin*y,sin*x+cos*y]
                x_new=rotation_mat[0][0]*x+rotation_mat[0][1]*y
                y_new=rotation_mat[1][0]*x+rotation_mat[1][1]*y
                multiplied.append(x_new)
                multiplied.append(y_new)
        #restructure flat multiplied list back into column vectors
        #stepping by 2 pairs each rotated x with its corresponding y
        for i in range(0,len(multiplied),2):
            four_dimension.append([multiplied[i]])
            four_dimension.append([multiplied[i+1]])
        for i in range(0,len(four_dimension),2):
            x_final=four_dimension[i][0]
            y_final=four_dimension[i+1][0]
            if x_final is None or y_final is None:
                #preserve discontinuities in final output
                final.append((None,None))
            else:
                if self.centre!=(0,0):
                    #shift back by adding the centre, undoes the earlier MatrixSubtraction()
                    x_final+=cx
                    y_final+=cy
                final.append((x_final,y_final)) #store as (x,y) tuple
        return final
    
    def GetDescription(self):
        '''Returns a description of the rotation angle, direction and centre.
        Parameters: 
        none
        Returns: 
        description string e.g. 'Rotation of 90 degrees clockwise at centre (0, 0).'
        '''
        if self.clockwise==True:
            return f'Rotation of {self.angle} degrees clockwise at centre {self.centre}.'
        else:
            return f'Rotation of {self.angle} degrees anticlockwise at centre {self.centre} '        