from GraphClass import *
class EquationAnalysis:
    '''Extracts transformation parameters from expanded polynomial equations.
    Used by TransformationEngine when an equation needs converting to a traversable form
    before transformation order can be identified.'''

    def CompletingTheSquare(self,equation): 
        '''Converts an expanded quadratic into vertex form by completing the square.
        Vertex form a(x+h)^2+k is needed because the parse tree of an expanded quadratic
        like x^2+4x+4 doesn't have a single x to traverse, vertex form does.
        Parameters: 
        equation (str)-->expanded quadratic string e.g. '2x^2+8x+3'
        Returns: 
        vertex form string e.g. '2.0(x+2.0)^2+-1.0' with any '+-' cleaned to '-' '''
        quadratic=Quadratic(equation)
        enlargement=quadratic.b #vertical stretch factor
        translation_x=(quadratic.c)/(2*enlargement) #calculates how far x is shifted
        translation_y=enlargement*(-((translation_x)**2)+(quadratic.d)/enlargement)
        form=f'{enlargement}(x+{translation_x})^2+{translation_y}'
        form=form.replace('+-','-') #clean up any '+-' that results from a negative translation_y
        return form
    
    def CubicCoefficients(self,equation):
        '''Extracts the transformation parameters from an expanded cubic equation.
        The point of inflection of a cubic ax^3+bx^2+cx+d always occurs at x=-b/3a
        this x value gives the horizontal translation, and evaluating the cubic there gives the vertical translation.
        Parameters: 
        equation (str)-->expanded cubic string e.g. '2x^3+6x^2+1'
        Returns:
        tuple of (translation_x, enlargement, translation_y)'''
        cubic=Cubic(equation)
        enlargement=cubic.a 
        translation_x=-(cubic.b/(3*(cubic.a)))
        translation_y=cubic.Evaluate(translation_x)
        return translation_x,enlargement,translation_y