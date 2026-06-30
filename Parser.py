from Node import *
import re

class Simplifier:
    ''' Reformats a raw equation string so it can be safely tokenised and parsed.
    Inserts explicit '*' operators where multiplication is implied by mathematical convention —
    e.g. 4x becomes 4*x and 2(x+1) becomes 2*(x+1).'''
    def Reformat(self,equation): 
        '''Applies a series of regex substitutions to make all implicit operations explicit.
        Without this, the tokeniser would fail to correctly split terms like 4x or 2(x+1)
        since there is no operator character between them.
        Parameters: 
        equation (str)-->raw equation string from user input
        Returns: 
        cleaned equation string with all implicit multiplications made explicit'''
        clean=equation.strip().lower().replace(' ','')
        #Ensures that there are no unsual spacing/case issues that are being processed from the user input. Avoids weird edge cases.
        clean=re.sub(r'(-?\d+|-?\d*\.\d+)x',r'\1*x',clean)
        clean=re.sub(r'(-)x',r'\1 1*x',clean)
        #Uses regex to format coefficients of x as being multiplied by x. E.g. 4x will be reformatted to 4*x.
        #Implimented as this is a mathematical rule: if not, could lead to logic issues when build/traversing the tree.
        clean=re.sub(r'(\d+)\(',r'\1*(',clean)
        #Reformats the equation so that if a number is before an opening bracket, the contents inside the bracket appears to be multiplied by that number. E.g. 4(x+2)-->4*(x+2).
        #Implimented to follow mathematical rules.
        clean=re.sub(r'(-)\(',r'\1 1*\(',clean)
        clean=re.sub(r'(\d*)x\(',r'\1x*\(',clean)
        #Achieves the same thing as previous expression but for variables. 
        clean=re.sub(r'(\))\(',r'\1*(',clean)
        #Relies on the same principle as the previous 2 statements. Places a * between a closing bracket and opening bracket. E.g. )(-->)*(
        clean=re.sub(r'(\d+)sin',r'\1*sin',clean)
        clean=re.sub(r'(\d+)cos',r'\1*cos',clean)
        clean=re.sub(r'(\d+)tan',r'\1*tan',clean)
        clean=re.sub(r'\+-','-',clean)
        clean=re.sub(r'-\+','-',clean)
        clean=re.sub(r'--','+',clean)
        clean=re.sub(r'\+\+','\+',clean)
        #Makes a number next to a trigonometric function appear to multiply that trig function.
        return clean 
            
class DescentParser:
    ''' Builds a recursive descent parse tree from a tokenised equation string.
    Methods are ordered by operator precedence from lowest to highest:
    ParseExpression (+/-)--> _ParseTerm (*)-->_ParsePower (^)-->_ParseFunction (trig)-->_ParseAtomic (numbers/x).
    Each method calls the one below it before checking for its own operator,
    this ensures higher precedence operations are deeper in the tree and evaluated first.
    The resulting tree is used both to simplify/expand equations and to identify transformation order.'''
    def __init__(self,tokens):
        '''Parameters: tokens (list)
        list of token strings produced by Tokenise()'''
        self.tokens=tokens
        self.position=0
        #The current position of the current node. 
        self.current=tokens[self.position] if tokens else None
        #The current node.
        
    @staticmethod 
    def Tokenise(equation): 
        '''
        Tokenises an equation: breaks down an equation string into seperate tokens. E.g. 'x^2+4x+4'--> ['x','^','2','+','4','*','x','+','4'].
        Each individual token can be processed as a node when building a parse tree.
        Reformat() is called first to make all implicit operators explicit before splitting.
        Static because it doesn't depend on any parser instance state, it's a pure string operation.
        Parameters: 
        equation (str)-->raw equation string
        Returns:
        list of token strings
        Raises: 
        SyntaxError-->if the equation is empty or produces no valid tokens'''
        if not equation or not equation.strip():
            raise SyntaxError('Equation cannot be empty.')
        simplifier=Simplifier()
        clean=simplifier.Reformat(equation)
        pattern=r'\d+\.\d+|\d+|x|[/+*-]|\^|sin|cos|tan|\(|\)'
        #Defines all valid individual tokens: numbers (decimal and integers), x's, operations (+,-,*,/) powers, trig functions and brackets. 
        tokens=re.findall(pattern,clean) 
        #Creates a list of tokens (tokenising the equation) by following the rules defined in pattern.
        #findall makes a list of tokens based on the acceptable pattern shown above.
        if not tokens:
            raise SyntaxError(f'{equation} could not be processed.')
        return tokens 
    
    def _Consume(self):
        '''Advances the parser to the next token.
        Called after the current token has been processed — without this the parser
        would repeatedly process the same token and never terminate.
        Parameters: 
        none
        Returns: 
        none'''
    #When a token that correlates to a method is found, this is called. 
        self.position+=1
        #Advances current position so that it correctly parses the input from left to right and that the parser doesn't process the same token infinitley.
        if self.position<len(self.tokens):
        #Checks if the current position is less than the length of the tokenised equation: to avoid an index error.
            self.current=self.tokens[self.position]
            #Updates the token.
        else:
            self.current=None
            #if the position has advanced beyond the length, the current token will be assigned to None: None tokens cannot be processed (avoids any logic errors).

    def ParseExpression(self):
        '''Entry point for building the full parse tree. Handles + and - operators.
        Called first because +/- have the lowest precedence meaning they sit highest in the tree.
        Negative numbers at the start of an equation are merged into a single token here
        to distinguish them from the subtraction operator before parsing begins.
        Parameters: 
        none
        Returns: 
        root Node of the fully built parse tree'''
        if self.current=='-':
            # a leading '-' must be a negative number not a subtraction -->merge it with the next token
            # e.g. for -2x+4, '-' and '2' become '-2' so the tree doesn't see both '-' and '2' separately
            current=self.current
            self.tokens[self.position]=self.tokens[self.position]+self.tokens[self.position+1]
            #This sets the current token as a concantenated string with the next token. Due to prior error handling, this token must always be an integer.
            self.current=self.tokens[self.position]
            #sets the current token as this concantenated string so that it can be parsed by the tree.
            del self.tokens[self.position+1]
            #Deletes the token used as the integer that created the new token. If not, in the example of -2x+4 the tree would parse both -2 and 2 which would lead to logic errors and incorrect parsing.
        pattern=r'\+|-'
        #A more strict checking pattern than other methods in this class. It only checks if the token is a single -/+ due to the addition of negative numbers.
        left=self._ParseTerm()
        #Method call accesses term's while loop.
        #Method is called before checking for + and - due to order of precedence: token has to be processed through each operation's while loop.
        while self.current is not None and (bool(re.match(pattern,self.current)))==True:

        #Loop as there could be multiple + or - in the token list. 
            current=self.current
            self._Consume()
            #Calls _Consume: moves to the next term to the right.
            #_Consume is called before _ParseTerm() is called again: if not, the same token would be parsed again.
            right=self._ParseTerm()
            left=Node(current,left,right)
            #The left inside the brackets: passes the previous node that had +/- as its parent node. E.g. for equation x^2+4x+4 left=Node(+,Node(+,Node(^,x,2),Node(*,4,x)),4)
        return left
        #if there is no + or - in the list, the result of first _ParseTerm() is returned. Left would be the fully built parse tree in this method.
    
    def _ParseTerm(self):
        '''Handles * and / operators. Called by ParseExpression() before it checks for +/-.
        Follows the same structure as ParseExpression() but for higher precedence operators.
        Parameters:
        none
        Returns: 
        Node representing the term subtree'''
    
        left=self._ParsePower()
        while self.current is not None and ('*' in self.current):
            current=self.current
            self._Consume()
            right=self._ParsePower() #handle higher precedence operators first
            left=Node(current,left,right)
        return left
        #Left: result of _ParseTerm() unlike the entire tree (like in ParseExpression())
        #Left will be passed as the initial left node for ParseExpression()
        
    def _ParsePower(self):
        '''Handles ^ operators. Called by _ParseTerm() before it checks for *.
        Follows the same structure as _ParseTerm() but for higher precedence operators.
        Parameters: 
        none
        Returns: 
        Node representing the power subtree'''
        left=self._ParseFunction()
        while self.current is not None and ('^' in self.current):
            current=self.current
            self._Consume()
            right=self._ParseFunction() #parse higher precedence operations first
            left=Node(current,left,right)
        return left
        #Result will be initial left node for _ParseTerm().
        
    def _ParseFunction(self):
        '''Handles sin, cos and tan operators. Called by _ParsePower() before it checks for ^.
        Follows the same structure as _ParsePower() but for higher precedence operators.
        Parameters: 
        none
        Returns: 
        Node representing the trig function subtree'''
        left=self._ParseAtomic() #parse atomic values first before checking for trig
        while self.current is not None and ('sin' in self.current or 'cos' in self.current or 'tan' in self.current):
            current=self.current
            self._Consume()
            right=self._ParseAtomic()
            left=Node(current,left,right)
        return left
        #Result is initial left node for _ParsePower()

    def _ParseAtomic(self): 
        '''Handles atomic values numbers and x, values which can't be broken down further.
        Also handles bracketed expressions by recursively calling ParseExpression() on the contents,
        which builds a complete subtree for the bracket before returning it.
        Brackets have the highest precedence so they are resolved before any operator is applied.
        Parameters: 
        none
        Returns: 
        leaf Node for numbers/x, or subtree Node for bracketed expressions'''
    #Looks for atomic values.
        pattern=r'-\d+|-\d*\.\d+|\d+|\d*.\d+'
        #Regex pattern that is used to define what an accepted number is. (Both integer and decimals are accepted).
        current=''
        while self.current is not None and (bool(re.match(pattern,self.current))==True or 'x' in self.current):
            current=self.current
            self._Consume()
        if self.current is not None and '(' in self.current:
        #Checks for an opening bracket.
            self._Consume()
            #_Consume() called here: if not '(' would be processed when it shouldn't be. It would be infinetley processed (recursion error).
            result=self.ParseExpression()
            #Example of recursive algorithm (Table 1 skill). Each time a bracket is found, a new tree is created.
            #Creates a parse tree for the expression inside the brackets.
            #This follows a standard mathematical rule that states that brackets should be handled seperately before being processed in context of the whole equation.
            self._Consume()
            #_Consume() called here: if not it would lead to logic errors. Terms after the close brackets would not be parsed at all.
            return result
            #Parse tree created in the brackets would be returned before any numbers or x's.
            #This is due to the order of operations: brackets have the highest precedence.
        return Node(current)
        #Atomic data is returned.
        #There is no left and right nodes as atomic data would be leaf nodes.
    
    def Unparse(self,node): 
        '''Converts a parse tree back into a readable equation string.
        Traverses the tree recursively and reconstructs the equation from operator and leaf nodes.
        Trig nodes are formatted with their argument in brackets e.g. sin(x+1).
        Parameters:
        node (Node)-->root of the tree to unparse
        Returns: 
        equation string reconstructed from the tree'''
        if node is None:
            return ''
        if node.IsLeaf():
            return str(node.value) #leaf nodes are just their value (number or x)
        if node.value=='sin' or node.value=='cos' or node.value=='tan':
            return f'{node.value}({self.Unparse(node.right)})' #trig argument is always on the right
        #recursive calls to unparse both branches.
        left=self.Unparse(node.left)
        right=self.Unparse(node.right)
        #all statements below are for formatting the equation into its proper string representation.
        if node.value=='-' or node.value=='+':
            return f'{left}{node.value}{right}'
        if node.value=='*':
            return f'{left}*{right}'
        if node.value=='^':
            return f'{left}^{right}'
        return f'{left}{node.value}{right}'
        
