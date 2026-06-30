from Node import *
from EquationAnalysis import *
from Parser import *
from TransformationClass import *
from GraphClass import *
from Traverse import *
class TransformationEngine:
    '''Coordinates the full pipeline from a cleaned equation string to an ordered list of transformations.
    Builds the parse tree, identifies the graph type, determines the correct transformation order,
    and applies transformations sequentially to a set of base coordinates. Helps achieve all 2.2 sub objectives.
    '''

    def __init__(self,equation,clean):
        '''Parameters:
            equation(str)-->the original user input before cleaning
            clean(str)-->the fully expanded and simplified equation string'''
        self.equation=clean
        self.original=equation #original kept separately: some methods need the pre-cleaned form.
        self.clean=clean
        self.graph=FindGraphType(self.clean)#detect graph type from the simplified equation
        base=self.BaseEquation()
        base.SetRange(self.graph.x_min,self.graph.x_max) #match base range to the transformed graph
        self.start_coords=base.GetCoordinates() #list of (x,y) tuples (the coordinates of the base graph without transformation applied.)
        self.tokens=DescentParser.Tokenise(equation)
        self.parser=DescentParser(self.tokens) 
        self.tree=self.parser.ParseExpression() #parse tree of original equation for transformation analysis.
        self.traversal=TransformationAnalyser(equation)
        self.transformations=[] #EquationOrder() uses this to append an ordered list of Transformation objects.
        self.descriptions=[]

    def BaseEquation(self):
        '''
        Returns the untransformed base graph for the detected equation type.
        This is the starting point that all transformations are applied on top of.
        E.g. a quadratic always starts from x^2 before any transformations are applied.
        Parameters: none
        Returns: base Graph instance matching the equation type
        '''
        if self.graph.graph_type=='Linear':
            return Linear('x')
        if self.graph.graph_type=='Quadratic':
            return Quadratic('x^2')
        if self.graph.graph_type=='Cubic':
            return Cubic('x^3')
        if self.graph.graph_type=='sin':
            return Trigonometric('sin(x)')
        if self.graph.graph_type=='cos':
            return Trigonometric('cos(x)')
        if self.graph.graph_type=='tan':
            return Trigonometric('tan(x)')
        
    def EquationOrder(self):
        '''
        Determines which ordering method to use based on graph type and equation form.
        Cubics not in vertex form use coefficient analysis. Quadratics are converted to
        vertex form via completing the square before traversal. Everything else is traversed directly.
        Parameters: none
        Returns: ordered list of Transformation objects
        '''
        original_tokens=DescentParser.Tokenise(self.original) #re-parse the original equation.
        original_parser=DescentParser(original_tokens)
        original_tree=original_parser.ParseExpression()
        original_traversal=TransformationAnalyser(self.original)
        if self.graph.graph_type=='Cubic' and not (self.traversal.IsVertex(original_tree)):
            order=self._CubicOrder()  #expanded cubics can't be traversed directly-->use coefficient analysis instead
        elif self.graph.graph_type=='Linear' or self.traversal.IsVertex(original_tree):
            #linear and vertex form equations can be traversed directly from the original tree.
            self.traversal=original_traversal
            self.tree=original_tree
            order=self._VertTrigLinOrder()
        elif self.graph.graph_type=='Quadratic':
            self.equation=EquationAnalysis().CompletingTheSquare(self.equation)
            #expanded quadratics need converting to vertex form first so the tree structure is traversable.
            self.tokens=DescentParser.Tokenise(self.equation)
            self.parser=DescentParser(self.tokens) 
            self.tree=self.parser.ParseExpression()
            self.traversal=TransformationAnalyser(self.equation)
            order=self._VertTrigLinOrder()
        elif self.graph.graph_type=='sin' or self.graph.graph_type=='cos' or self.graph.graph_type=='tan':
            self.traversal=original_traversal
            self.tree=original_tree
            order=self._VertTrigLinOrder()
        return order
    
    def _ApplyAddition(self,transformation,x_stretch_factor,has_x_reflection):
        '''Builds and appends the correct Translation for a '+' operator node.
        X translations are divided by x_stretch_factor to account for any horizontal stretch already applied.
        X translation direction is flipped when a reflection in y is present.
        Parameters:
            transformation(dict)-->contains 'type' and 'value' for this operator
            x_stretch_factor(float)-->current horizontal stretch factor
            has_x_reflection(bool)-->whether a y axis reflection has been applied'''
        if float(transformation['value'])!=0.0:
            if transformation['type']=='y':
                self.transformations.append(Translation(0,float(transformation['value'])))
            else:
                if float(transformation['value'])!=0.0:
                    raw=float(transformation['value'])
                    #reflection flips translation direction-->positive raw becomes positive shift.
                    if has_x_reflection==True:
                        self.transformations.append(Translation((raw/x_stretch_factor),0,display_dx=raw))
                    else:
                        #x translations from '+' move left, opposite to what's written in the equation.
                        self.transformations.append(Translation(-(raw/x_stretch_factor),0,display_dx=raw))
    
    def _ApplySubtraction(self,transformation,x_stretch_factor,has_x_reflection):
              '''Builds and appends the correct Translation for a '-' operator node.
            Mirror of _ApplyAddition but with direction flipped.'-' moves x in the opposite direction to '+'.
            Parameters:
            transformation(dict)-->contains 'type' and 'value' for this operator
            x_stretch_factor(float)-->current horizontal stretch factor
            has_x_reflection(bool)-->whether a y axis reflection has been applied'''
              if float(transformation['value'])!=0.0:
                    if transformation['type']=='y':
                        self.transformations.append(Translation(0,-float(transformation['value'])))
                    else:
                        if float(transformation['value']):
                            raw=float(transformation['value'])
                            if has_x_reflection==True:
                                #reflection present, direction flipped again so '-' moves right.
                                self.transformations.append(Translation(-(raw/x_stretch_factor),0,display_dx=raw))
                            else:
                                #x translations from '-' move right — opposite to what's written in the equation.
                                self.transformations.append(Translation((raw/x_stretch_factor),0,display_dx=raw))
    
    def _ApplyMultiplication(self,transformation,x_stretch_factor,has_x_reflection):
        ''' Builds and appends the correct Reflection and/or Enlargement for a '*' operator node.
        A negative value means a reflection is present and must be separated out before the stretch.
        Updates and returns x_stretch_factor and has_x_reflection so subsequent translations are scaled correctly.
        Parameters:
            transformation(dict)-->contains 'type' and 'value' for this operator
            x_stretch_factor(float)-->current horizontal stretch factor
            has_x_reflection(bool)-->whether a y axis reflection has been applied
        Returns: 
        updated (x_stretch_factor, has_x_reflection) tuple'''
        if transformation['type']=='y':
            if '-' in transformation['value']:
                #negative y multiplier. Reflection in x axis comes before any stretch
                self.transformations.append(Reflection('x'))
                factor=abs(float(transformation['value']))
                if factor!=1.0:
                    #only add enlargement if factor isn't 1-->pure reflection with no stretch
                    self.transformations.append(Enlargement(0,factor))
            else:
                factor=float(transformation['value'])
                if factor!=1.0:
                    self.transformations.append(Enlargement(0,float(transformation['value'])))
        if transformation['type']=='x':
            if '-' in transformation['value']:
                #negative x multiplier-->reflection in y axis, flag it so translations are flipped
                has_x_reflection=True
                self.transformations.append(Reflection('y'))
                factor=abs(float(transformation['value']))
                x_stretch_factor=factor #store so subsequent x translations can be scaled correctly

                if factor!=1.0:
                    self.transformations.append(Enlargement(factor,0))
            else:
                factor=float(transformation['value'])
                x_stretch_factor=factor #store stretch factor even with no reflection.
                if factor!=1.0:
                    self.transformations.append(Enlargement(float(transformation['value']),0))
        return x_stretch_factor,has_x_reflection

    def _VertTrigLinOrder(self):
        ''' Builds the transformation list for vertex form, trig and linear equations by traversing the parse tree.
        GetOrder() returns transformations in inside-out order so the list is reversed before processing,
        this gives the correct mathematical order with outer transformations applied first.
        Parameters:
        none
        Returns:
        ordered list of Transformation objects'''
        transformation_order=self.traversal.GetOrder(self.tree)[::-1] #reverse so transformations are processed outermost first, matching mathematical application order
        has_x_reflection=False
        x_stretch_factor=1.0  #tracks any x stretch so translations can be scaled correctly
        for transformation in transformation_order:
            if transformation['operator']=='+':
                self._ApplyAddition(transformation,x_stretch_factor,has_x_reflection)
            if transformation['operator']=='-':
                self._ApplySubtraction(transformation,x_stretch_factor,has_x_reflection)
            if transformation['operator']=='*':
                #multiplication may update stretch factor and reflection state-->capture returned values
                x_stretch_factor,has_x_reflection=self._ApplyMultiplication(transformation,x_stretch_factor,has_x_reflection)
        return self.transformations
    
    def _CubicOrder(self):
        '''Builds the transformation list for expanded cubic equations using coefficient analysis.
        Only works for cubics expressible as simple transformations of x^3.
        cubics where (3ac-b^2)!= 0 cannot be analysed this way and are beyond A-Level scope.
        Parameters: 
        none
        Returns: 
        ordered list of Transformation objects
        Raises: 
        ValueError — if the cubic cannot be expressed as simple transformations
        '''
        translation_x,enlargement,translation_y=EquationAnalysis().CubicCoefficients(self.clean)
        cubic=Cubic(self.clean)
        if ((3*cubic.a*cubic.c)-(cubic.b)**2)!=0:
            #checks whether the cubic equation can be simplified into vertex form. If not, there are more advanced transformations applied.
            raise ValueError(f'This cubic equation cannot be expressed in terms of simple transformations. It is beyond the A-Level specification.')
        if translation_x!=0:
            self.transformations.append(Translation(translation_x,0))
        if enlargement<0:
            #negative enlargement means a reflection is present, separate it before applying the scale
            self.transformations.append(Reflection('x'))
            enlargement=abs(enlargement)
        if enlargement!=1:
            self.transformations.append(Enlargement(0,enlargement))
        if translation_y!=0:
            self.transformations.append(Translation(0,translation_y))
        return self.transformations
    
    def ApplyAll(self,coordinates=None):
        '''Applies every transformation in order to a set of coordinates.
        Coordinates are passed through each transformation sequentially,
        the output of one becomes the input of the next.
        Coordinate data is stored as a list of (x,y) tuples throughout.
        Parameters: 
        coordinates(list)-->list of (x,y) tuples, defaults to start_coords
        Returns: 
        fully transformed list of (x,y) tuples'''
        if coordinates is None:
            coordinates=self.start_coords #start from base coordinates on first call.
        for transformation in self.transformations:
            coordinates=transformation.Apply(coordinates)  #each transformation receives and returns a list of (x,y) tuples
        return coordinates
    
    def TransformationList(self):
        '''Builds a list of coordinate snapshots after each transformation step.
        Used by the animation system to draw each step of the transformation sequence.
        Returns a list of lists of tuples: [[(x,y),...], [(x,y),...], ...]
        where index 0 is the base state and each subsequent index is the state after one more transformation.
        Parameters: 
        none
        Returns:
        list of (x,y) tuple lists, one per step including the base state'''
        transformation_steps=[self.start_coords] #index 0 is always the untransformed base
        coordinates=self.start_coords
        for transformation in self.transformations:
            coordinates=transformation.Apply(coordinates) #apply next transformation to current state
            transformation_steps.append(coordinates) #snapshot the result as a list of (x,y) tuples
        return transformation_steps
        
        
    def GetDescriptions(self):
        '''Collects a readable description from each transformation in order.
        Used to populate the description box in the UI during animation.
        Parameters: none
        Returns: list of description strings in transformation order'''
        descriptions=[]
        for transformation in self.transformations:
            descriptions.append(transformation.GetDescription())
        return descriptions