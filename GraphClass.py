from AngleManager import *
from Animation import max_y_value
import re
import math
#module-level constants used across all graph classes for coordinate generation and root finding
coordinate_points=5000 #number of x values generated for plotting, higher means smoother curves
max_binary_depth=100 #recursion limit for binary search methods
binary_tolerance=0.001 #interval width at which binary search stops and returns the midpoint

class Graph: 
    '''Base class for all graph types. Handles coordinate generation, root finding,
    turning point detection and coefficient extraction for polynomial equations.
    Coordinates are stored as a list of (x,y) tuples throughout, None is used as
    the y value to represent discontinuities where the graph breaks (such as tan asymptotes).
    Subclasses override graph_type and may override Evaluate(), IsValid() and ExtractTerms()
    where polynomial logic doesn't apply.'''
    pattern=r'(\d+|\d*\.\d+)?([-+]?(\d*|\d*\.\d+)?x(\^[123])?)+(([-+](\d+|\d*\.\d+))+)?'
    #pattern allows polynomials up until x^3
    def __init__(self,equation,x_min=-10,x_max=10):
        '''Parameters:
            equation (str)-->simplified equation string
            x_min, x_max (float)-->horizontal range for coordinate generation
           '''
        self.x_min=x_min
        self.x_max=x_max
        self.equation=equation
        self.graph_type=None
        self.is_valid=False
        self.eval_coords=None #stores evaluated coordinates for intersection detection
        a,b,c,d=self.Terms()      
        #default to 0 if a coefficient is None (not all equations have all four terms).   
        self.a=a or 0
        self.b=b or 0
        self.c=c or 0
        self.d=d or 0

    def Terms(self):
        '''Validates the equation and extracts its coefficients.
        Returns zeros for all coefficients if the equation is not valid.
        Parameters:
        none
        Returns: 
        tuple of (a, b, c, d) coefficients'''
        a=b=c=d=0
        if self.IsValid():
            terms=self.ExtractTerms()
            a=terms[0]
            b= terms[1]
            c=terms[2]
            d=terms[3]
        return a,b,c,d
            
    def IsValid(self):
        '''Checks whether the equation matches the accepted polynomial pattern using regex.
        Called during __init__ via Terms()-->raises immediately so invalid equations are never graphed.
        Parameters:
        none
        Returns: 
        True if the equation is a valid supported polynomial
        Raises: 
        SyntaxError-->if the equation doesn't match the pattern'''
        clean=self.equation.strip().lower().replace(' ','')
        if re.fullmatch(self.pattern,clean):
            self.is_valid=True
        if self.is_valid==False:
            raise SyntaxError (f'{self.equation} is not a supported equation. Linear, Quadratic and Cubic are the only polynomials that are accepted')
        return self.is_valid
        
    def ExtractTerms(self):
        '''Extracts the a, b, c, d coefficients from the equation string.
        Splits by '+' after converting '-' to '+-' so all terms can be separated uniformly.
        Terms containing x are classified by their power, remaining terms are constants.
        Parameters: 
        none
        Returns: 
        list of [a,b,c,d] where missing terms are None'''
        a=b=c=d=None
        term='x'
        terms=[]
        clean=self.equation.strip().lower().replace(' ','').replace('-','+-')
        t=list(filter(None,clean.split('+'))) #all terms are split by +, the none gets rid of empty terms
        for i in t:
            if term in i:
                if '^3' in i:
                    a=i.replace('x^3','') #identifies the cubic term for polynomials
                    a=float(a or '1') if a!='-' else -1 #bare '-' means coefficient is -1
                elif '^2' in i: #identifies the quadratic term for polynomials 
                    b=i.replace('x^2','')
                    b=float(b or '1') if b !='-' else -1
                else:
                    c= i.replace('x','') #identifies the linear term for polynomials 
                    c=float(c or 1) if c!='-' else-1 
            elif i!='' and not term in i:
                d=float(i) #no x in term means it's a constant
        terms+=[a,b,c,d]
        return terms
    
    def Evaluate(self,x_value): 
        '''Calculates the y value for a given x using the polynomial formula ax^3+bx^2+cx+d.
        Works for all polynomial types-->unused terms have coefficient 0 so they contribute nothing.
        Parameters: 
        x_value (float)-->x coordinate to evaluate at
        Returns: 
        corresponding y value'''
        return ((self.a*(x_value**3))+(self.b*(x_value**2))+(self.c*(x_value))+self.d)
    
    def ExtendRange(self,start,stop,num=coordinate_points): 
        '''Generates a list of evenly spaced x values across the given range.
        More points means a smoother plotted curve-->coordinate_points is set at module level.
        Parameters:
        start (float)-->start of range
        stop (float)-->end of range
        num (int)-->number of points to generate
        Returns: 
        list of evenly spaced float x values'''
        values=[]
        step=(stop-start)/(num-1) #step size between each x value
        for i in range (num):
            x=start+i*step
            values.append(x)
        return values
    
    def SetRange(self,x_min,x_max): 
        '''Updates the x range used for coordinate generation.
        Only applied if x_min is less than x_max-->prevents invalid ranges being set.
        Parameters: 
        x_min (float)-->new minimum x
        x_max (float)-->new maximum x
        Returns: none'''
        if x_min<x_max:
            self.x_min=x_min
            self.x_max=x_max

    def GetCoordinates(self): 
        '''Generates all (x,y) coordinate tuples across the current x range.
        Coordinates are stored as a list of (x,y) tuples-->the core data structure
        used throughout the program for plotting and transformation.
        Parameters: 
        none
        Returns: 
        list of (x,y) tuples'''
        x=[]
        y=[]
        coordinates=[]
        x=self.ExtendRange(self.x_min,self.x_max) 
        y=map(lambda x_value:self.Evaluate(x_value),x ) #applies evaluate to all x values. appends to y.
        coordinates=list(zip(x,y)) #creates a tuple for coordinates 
        return coordinates
    
    def FindXIntercepts(self):
        '''Finds all x intercepts by detecting sign changes between consecutive y values.
        A sign change between y1 and y2 means a root lies between x1 and x2,
        BinarySearch() then narrows it down to within binary_tolerance.
        Parameters:
        none
        Returns: 
        tuple of (is_root (bool), roots (list of (x,0) tuples))'''
        roots=[]
        is_root=False
        x=self.ExtendRange(self.x_min,self.x_max)
        for i in range(0,len(x)-1):
            x1=x[i]
            x2=x[i+1]
            if self.Evaluate(x1)*self.Evaluate(x2)<0:
                #negative product means opposite signs-->root lies between x1 and x2
                root=self.BinarySearch(x1,x2)
                is_root=True
                roots.append(root)
        roots=list(map(lambda coords: round(coords,3),roots))
        roots=list(map(lambda x:(x,0),roots)) #format as (x,0) tuples for plotting
        return is_root,roots

    def BinarySearch(self,a,b,depth=0): 
        '''Narrows down a root between two x values using repeated midpoint halving.
        Stops when the interval is smaller than binary_tolerance or recursion limit is hit.
        Parameters:
        a (float)-->left bound
        b (float)-->right bound
        depth (int)-->recursion counter
        Returns:
        x value of the estimated root'''
        mid=(a+b)/2 #midpoint splits the interval in half each recursion
        if b-a<binary_tolerance or depth>max_binary_depth:
            return mid #interval small enough to treat midpoint as the root
        else:
            if self.Evaluate(a)*self.Evaluate(mid)<0:
                #sign change on left half-->root is there, discard right
                return self.BinarySearch(a,mid,depth+1)
            else:
                #root must be in right half
                return self.BinarySearch(mid,b,depth+1)
                       
    def FindYIntercept(self):
        '''
        Returns the y intercept by evaluating at x=0.
        Parameters: 
        none
        Returns: 
        y value at x=0
        '''
        y_intercept=self.Evaluate(0)
        return y_intercept
        
    def FindTurningPoints(self): #returns an estimate of the turning points of a function.
        '''Estimates turning points by detecting sign changes in the numerical gradient.
        Gradient is approximated between consecutive x values-->a sign change means
        the gradient passed through zero so a turning point lies in that interval.
        BinarySearchTP() then narrows it down within binary_tolerance.
        Parameters: 
        none
        Returns: 
        list of (x,y) tuples at estimated turning points'''
        gradients=[]
        turning_points=[]
        x_values=[]
        x=self.ExtendRange(self.x_min,self.x_max)
        for i in range(0,len(x)-1):
            #numerical differentiation-->approximate gradient between consecutive points
            gradient=(self.Evaluate(x[i+1])-self.Evaluate(x[i]))/(x[(i+1)]-x[i]) #this is a way of implimenting numerical differentiation to find an estimate of the gradient of a polynomial.
            gradients.append(gradient)   
        for j in range(0,len(gradients)-1):
            if gradients[j]*gradients[j+1]<0: #turning points occur when there is a sign change --> similar logic to FindXIntercepts.
                turning_point=self.BinarySearchTP(x[j],x[j+1],gradients[j],gradients[j+1])
                x_values.append(turning_point)
        y=map(lambda x_value:self.Evaluate(x_value),x_values)
        turning_points=list(zip(x_values,y)) #pair x values with their y values
        return turning_points

    def BinarySearchTP(self,a,b,gradient_a,gradient_b,depth=0): 
        '''Narrows down a turning point between two x values using gradient sign changes.
        Same principle as BinarySearch() but checks gradient sign rather than y value sign.
        Gradient at midpoint is approximated numerically with a small step of 0.0001.
        Parameters:
            a,b (float)-->left and right bounds
            gradient_a,gradient_b (float)-->gradients at a and b
            depth (int)-->recursion counter
        Returns: 
        x value of the estimated turning point'''
        mid=(a+b)/2
        if b-a<binary_tolerance or depth>max_binary_depth:
            return mid  #interval small enough to treat midpoint as the turning point
        else:
            #approximate gradient at midpoint using a tiny step
            gradient_mid=(self.Evaluate(mid+0.0001)-self.Evaluate(mid))/0.0001
            if gradient_a*gradient_mid<0:
                #sign change between a and mid-->turning point is in left half
                return self.BinarySearchTP(a,mid,gradient_a,gradient_mid,depth+1)
            else:
                return self.BinarySearchTP(mid,b,gradient_mid,gradient_b,depth+1)
                
class Linear(Graph):
    ''' Represents a linear equation of the form cx+d.
        Overrides FindTurningPoints() since linear equations have no turning points.'''
    def __init__(self,equation,x_min=-10,x_max=10):
        '''Parameter:
        graph_type(str)-->the graph type'''
        super().__init__(equation,x_min,x_max)
        self.graph_type='Linear'

    def FindTurningPoints(self):
        return None #linear equations have no turning points

class Quadratic(Graph):
    '''Represents a quadratic equation of the form bx^2+cx+d.'''
    def __init__(self,equation,x_min=-10,x_max=10):
        '''Parameter:
        graph_type(str)-->the graph type'''
        super().__init__(equation,x_min,x_max)
        self.graph_type='Quadratic'

class Cubic(Graph):
    '''Represents a cubic equation of the form ax^3+bx^2+cx+d.'''
    def __init__(self,equation,x_min=-10,x_max=10):
        '''Parameter:
        graph_type(str)-->the graph type'''
        super().__init__(equation,x_min,x_max)
        self.graph_type='Cubic'

#if sin/cos/tan in identity --> it is a trig identity
class Trigonometric(Graph):
    '''Represents a trigonometric equation of the form a*sin/cos/tan(bx+c)+d.
    Overrides IsValid(), ExtractTerms(), Evaluate() and GetCoordinates() since
    trig equations have a fundamentally different structure to polynomials.
    Stores amplitude, frequency, phase and vertical_shift separately for evaluation.'''
    pattern = r'^-?(\d+\.?\d*)?(sin|cos|tan)\(-?(\d+\.?\d*)?x([+-]\d+\.?\d*)?\)([+-]\d+\.?\d*)*$'
    #only allows trig equations in the form atrig(bx+c)+d
    def __init__(self,equation,x_min=(-2*math.pi),x_max=(2*math.pi)):
        '''Parameters:
            equation (str)-->trig equation string
            x_min, x_max (float)-->default range is around -6.28 to 6.28'''
        #initialise trig parameters before super().__init__ since IsValid() is called there
        self.amplitude=1
        self.frequency=1
        self.phase=0
        self.vertical_shift=0
        super().__init__(equation,x_min,x_max)
        print(hasattr(self,'eval_coords'))
        self.graph_type=self.FindGraphType()
        if self.is_valid:
            # verride defaults with extracted values-->fall back to 0 if a term is missing
            terms=self.ExtractTerms()
            amplitude=terms[0]
            frequency= terms[1]
            phase=terms[2]
            vertical_shift=terms[3]
            self.amplitude=amplitude or 0
            self.frequency=frequency or 0
            self.phase=phase or 0
            self.vertical_shift=vertical_shift or 0
                                                            
    def IsValid(self):
        '''Checks whether the equation matches the trig pattern using regex.
        Uses a different pattern to Graph.IsValid() since trig equations have
        a different structure (brackets, function names) that the polynomial pattern can't match.
        Parameters: 
        none
        Returns: 
        True if the equation is a valid supported trig equation
        Raises: 
        SyntaxError: if the equation doesn't match the trig pattern'''
        clean=self.equation.strip().lower().replace(' ','')
        if re.fullmatch(self.pattern,clean):
            self.is_valid=True
        if self.is_valid==False:
            raise SyntaxError (f'{self.equation} is not a valid equation. Only trigonometric equations that simplify to the form asin/cos/tan(bx+c)+d are supported by the program.')
        return self.is_valid
    
    def Clean(self):
        '''Splits a trig equation into its three structural parts for coefficient extraction.
        'before' holds the function name and amplitude, 'inside' holds bx+c, 'after' holds +d.
        Parameters: 
        none
        Returns: 
        tuple of (t, term) where t is [before, after] and term is the split inside contents'''
        t=[]
        clean=self.equation.strip().lower().replace(' ','') #results in equations that are all lower case, with no spaces.
        before=clean[:clean.index('(')] #used to identify the graph type (sin, cos or tan) --> tokenises the part of the equation that is before the starting bracket.
        inside=clean[clean.index('(')+1:clean.index(')')] #tokenises the part of the equation that is inside the brackets.
        after=clean[clean.index(')')+1:]#tokenises the expression after the ending bracket.
        inside=inside.replace('-','+-')
        term=list(filter(None,inside.split('+'))) #tokenises the entire equation, splits it in a similar way used in the polynomial extraction.
        t.append(before)
        t.append(after)
        return t,term
        
    def ExtractTerms(self): 
        '''Extracts amplitude, frequency, phase and vertical shift from the trig equation.
        Uses a different approach to Graph.ExtractTerms()-->the before/after/inside
        structure of trig equations means polynomial splitting logic doesn't apply.
        Parameters: 
        none
        Returns: 
        list of [amplitude, frequency, phase, vertical_shift]'''
        terms=[]
        amplitude=frequency=phase=vertical_shift=None
        t,term=self.Clean()
        for i in t:
            #amplitude is the coefficient before the trig function name
            if 'sin' in i:
                amplitude=i.replace('sin','')
                amplitude=float(amplitude or '1') if amplitude!='-' else -1
            elif 'cos' in i:
                amplitude=i.replace('cos','')
                amplitude=float(amplitude or '1') if amplitude!='-' else -1
            elif 'tan' in i:
                amplitude=i.replace('tan','')
                amplitude=float(amplitude or '1') if amplitude!='-' else -1
            if i!='' and not 'sin' in i and not 'cos' in i and not 'tan' in i:
                vertical_shift=float(i) #after part with no trig name is the vertical shift
        for i in term:
            if 'x' in i:
                frequency= i.replace('x','') #coefficient of x inside the brackets is the frequency
                frequency=float(frequency or 1) if frequency!='-' else -1 
            elif i!='' and not 'x' in i:
                phase=float(i)  #constant inside brackets with no x is the phase shift
        terms+=[amplitude,frequency,phase,vertical_shift]
        return terms


    def GetCoordinates(self):
        '''Generates coordinates for trig equations. Polynomial GetCoordinates() is used for
        sin and cos since they are continuous. Tan needs special handling-->asymptotes cause
        near-infinite y values and large jumps between consecutive points that must be marked
        as None to prevent the graph drawing a vertical line through the asymptote.
        Parameters: 
        none
        Returns: 
        list of (x,y) tuples with None y values at discontinuities'''
        if self.graph_type!='tan':
            return super().GetCoordinates() #sin and cos are continuous-->use standard method
        x=self.ExtendRange(self.x_min,self.x_max)
        coordinates=[]
        prev_y=None
        for x_val in x:
            try:
                y=self.Evaluate(x_val)
                if abs(y)>max_y_value:
                    #y too large-->asymptote region, insert break
                    coordinates.append((x_val,None))
                    prev_y=None
                elif prev_y is not None and abs(y-prev_y)>50:
                    coordinates.append((x_val,None)) #sudden large jump-->asymptote crossed, insert break
                    prev_y=None
                else:
                    coordinates.append((x_val,y))
                    prev_y=y
            except:
                coordinates.append((x_val,None)) #evaluation error-->insert break
                prev_y=None
        return coordinates
    
    def FindGraphType(self):
        '''Identifies whether the equation is sin, cos or tan by checking the equation string.
        Parameters: 
        none
        Returns: 'sin', 'cos' or 'tan'
        '''
        if 'sin' in self.equation:
            self.graph_type='sin'
        elif 'cos' in self.equation:
            self.graph_type='cos'
        elif 'tan' in self.equation:
            self.graph_type='tan'
        return self.graph_type
   
    def Evaluate(self,x_value):
        '''Calculates y for a given x using the trig formula a*f(bx+c)+d.
        Converts x to radians first if angle mode is set to Degrees-->math.sin/cos/tan always expect radians.
        Parameters: 
        x_value (float)-->x coordinate to evaluate at
        Returns: 
        corresponding y value'''
        if AngleMode.angle_mode=='Degrees':
            x_value=ToRadians(x_value,'Degrees') #convert input to radians for math functions
            self.phase=ToRadians(self.phase,'Degrees') #phase must also be in radians
        if self.graph_type=='sin':
            return self.amplitude*(math.sin(self.frequency*(x_value)+self.phase))+self.vertical_shift
        if self.graph_type=='cos':
            return self.amplitude*(math.cos(self.frequency*(x_value)+self.phase))+self.vertical_shift
        if self.graph_type=='tan':
            return self.amplitude*(math.tan(self.frequency*(x_value)+self.phase))+self.vertical_shift

def FindGraphType(equation): 
    ''' Factory function that returns the correct Graph subclass for a given equation string.
    Only called on fully expanded and simplified equations-->relies on x^3, x^2 and trig
    keywords being present to classify correctly.
    Parameters: 
    equation (str)-->simplified equation string
    Returns:
    appropriate Graph subclass instance, or None if unrecognised'''
    if 'sin' in equation or 'cos' in equation or 'tan' in equation:
        return Trigonometric(equation)
    if 'x^3' in equation:
        return Cubic(equation)
    if 'x^2' in equation and 'x^3' not in equation:
        #check x^3 not present to avoid misclassifying cubics
        return Quadratic(equation)
    if 'x' in equation and 'x^2'not in equation and 'x^3' not in equation:
        return Linear(equation) 
