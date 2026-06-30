from TransformationEngine import *
import re
class EquationProcess:
    ''' Validates and processes a raw user equation before passing it to the transformation pipeline.
    Expands, simplifies and cleans the equation, checks it is a supported graph type,
    then constructs a TransformationEngine if valid.'''
    def __init__(self,equation):
        '''Parameters: 
        equation (str)-->raw equation string from user input'''
        self.equation=equation
        self.traverse=EquationSimplifier(self.equation)
        self.tokens=DescentParser.Tokenise(self.equation)
        self.parser=DescentParser(self.tokens)
        self.tree=self.parser.ParseExpression() #parse tree of the raw equation
        self.is_valid=False #set by Validate()-->gates EngineApplication() and GraphApplication()
        self.clean=''#set by Validate()-->the fully simplified equation string
    
    def PostTraverseClean(self,equation):
        '''Cleans up artefacts left in the equation string after tree traversal and unparsing.
        Traversal leaves behind explicit '*' operators, redundant powers like x^1 and x^0,
        and sign combinations like '+-' that need normalising before graph type detection.
        Parameters: 
        equation (str)-->equation string produced by Unparse() or FormatLikeTerms()
        Returns: 
        cleaned equation string ready for graph type detection'''
        clean=re.sub(r'\*','',equation) #remove explicit '*' operators left by unparsing
        clean=re.sub(r'--','+',clean) #double negative becomes positive
        clean=re.sub(r'\+\+',r'\+',clean)
        clean=re.sub(r'\+-','-',clean) #clean up sign combinations from term joining
        clean=re.sub(r'-\+','-',clean)
        clean=re.sub(r'x\^1(?!\d)','x',clean)  #x^1 is just x-->remove redundant power
        clean=re.sub(r'(\d)x\^0',r'\1',clean) #x^0 is 1-->remove it and keep the coefficient
        clean=re.sub(r'x\^0', '',clean) #lone x^0 with no coefficient
        clean=re.sub(r'(\d+\.?\d*)\*x',r'\1x',clean) #remove any remaining explicit * before x
        return clean
    
    def Validate(self): 
        ''' Expands, simplifies and validates the equation through the full processing pipeline.
        Polynomial equations are collected into like terms after expansion.
        Trig equations are formatted separately since they have a different structure.
        After simplification, graph type detection confirms whether the result is supported.
        Parameters: 
        none
        Returns: 
        tuple of (is_valid (bool), clean (str))-->whether the equation is valid and its simplified form
        Raises: 
        SyntaxError: if the equation fails validation or cannot be processed'''
        try:
            self._ValidationStatements() #check for inputs that don't follow basic syntax rules for the program before any processing
            expanded=self.traverse.Expand(self.tree) #distribute all brackets
            multiplied=self.traverse.Multiply(expanded) #combine like multiplication terms
            unparsed=self.parser.Unparse(multiplied) #convert tree back to string
            clean=self.PostTraverseClean(unparsed) #clean traversed equation
            if not any(op in clean for op in trig_operators):
                # polynomial path: re-parse and collect like terms to fully simplify
                temp_tokens=DescentParser.Tokenise(clean)
                temp_parser=DescentParser(temp_tokens)
                temp_tree=temp_parser.ParseExpression()
                temp_traverse=EquationSimplifier(clean)
                cube,square,coeff,constant=temp_traverse.CollectLikeTerms(temp_tree)
                clean=temp_traverse.FormatLikeTerms(cube,square,coeff,constant)
                clean=self.PostTraverseClean(clean) #clean again after like term formatting
            else:
                # trig path: different formatting needed since trig structure can't be collected like polynomial terms
                trig_tokens=DescentParser.Tokenise(clean)
                trig_parser=DescentParser(trig_tokens)
                trig_tree=trig_parser.ParseExpression()
                trig_traverse=EquationSimplifier(clean)
                clean=trig_traverse.FormatTrigWithConstants(trig_tree)
                clean=self.PostTraverseClean(clean)
            graph=FindGraphType(clean)  #detect whether the simplified result is a supported graph type
            if graph is None:
                return False,clean  #unrecognised equation type
            if graph.IsValid():
                return True,clean
            else:
                return False,clean
        except Exception as e:
            raise SyntaxError(str(e))
          
    def _ValidationStatements(self):
        '''Checks the raw equation for unsupported inputs before any processing begins.
        Catches common mistakes like entering a base equation, using unsupported powers,
        writing function notation, using division, or mismatched brackets.
        Parameters: 
        none
        Returns: 
        none
        Raises: 
        SyntaxError: describes the specific validation failure'''
        raw=self.equation.strip()
        if raw=='x' or raw=='x^2' or raw=='x^3' or raw=='sin(x)' or raw=='cos(x)' or raw=='tan(x)':
            raise SyntaxError(f'{self.equation} is a base equation. Type in a transformed equation.')
        if re.search (r'x\^[4-9]|x\^[1-9]\d+',raw):
            #only linear, quadratic and cubic polynomials are supported-->x^4 and above are rejected
            raise SyntaxError (f'{self.equation} is not a supported equation. Linear, Quadratic and Cubic are the only polynomials that are accepted.')
        if 'y=' in raw or 'f(x)='in raw:
            raise SyntaxError(f"Don't write any function notation. Just write the equation.")
        if '/' in raw:
            raise SyntaxError(f'/ symbol is not supported. Write the number as *(1/number).')
        if raw.count('(') != raw.count(')'):
            #mismatched brackets would cause the parser to fail or produce an incorrect tree
            raise SyntaxError(f'Brackets are not equal for: {raw}')
        
    def EngineApplication(self):
        '''Validates the equation and constructs a TransformationEngine if valid.
        The engine receives both the original and cleaned equation, the original
        is needed for transformation analysis, the clean for graph type detection.
        Parameters: 
        none
        Returns: 
        TransformationEngine instance if valid, None if not'''
        self.is_valid,self.clean=self.Validate()
        if self.is_valid:
            return TransformationEngine(self.equation,self.clean)
            
    def GraphApplication(self):
        '''Returns the graph object for the validated equation.
        Only callable after EngineApplication() has set is_valid.
        Parameters:
        none
        Returns: 
        Graph instance matching the equation type, or None if not yet validated
        '''
        if self.is_valid:
            return FindGraphType(self.clean)

