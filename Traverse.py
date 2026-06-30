import re
from Parser import *
from GraphClass import *
#General operators are set to avoid long lines of repeated code.
trig_operators=frozenset({'sin','cos','tan'}) 
additive_operators=frozenset({'+','-'})

def _ApplyNegative(node,negate):
    '''Adds a negative sign to a value when negate is true. It's used to correctly sign leaf nodes that are 
    found on the right side of a '-' parent node in CollectLikeTerms().
    Parameters:
    -node (str)--> the numeric string to sign
    -negate (bool)--> flag that indicates whether to format the numeric string as negative or not
    Returns:
    The value string with an optional negative sign in front of it if negate is true.'''
    if negate==True:
        node=f'-{node}'
    return node

class TreeAnalyser:
    '''A class of helper functions that are exclusively internally used in EquationSimplifier and 
    TransformationAnalyser which inherit from this class. These are read-only methods and no nodes are modified.'''
    def _ContainsX(self,node):
        '''Recursively checks a subtree tree to see if the 'x' variable is within its branches. Used to
        distinguish which branch contains an 'x' so the correct path is taken during traversal.
        Parameters:
        -node (Node)--> root of the subtree to search for the 'x'
        Returns:
        True if 'x' is found in either branch of the subtree.'''
        if node is None: 
            return False 
        if node.IsLeaf():
            #The check for x only happens when the node is a leaf as only leaf nodes can contain x. 
            return node.value=='x'
        #Recurses to the left and right of the tree to check if either branch contains an x.
        return self._ContainsX(node.left) or self._ContainsX(node.right)
    
    def _ContainsTrig(self,node):
        '''Recursively checks whether a trig operator appears anywhere in the subtree. It's used to 
        simply trigonometric and polynomial simplification parts.
        Parameters:
        -node (Node)--> root of the subtree to search for the trig operator.
        Returns:
        True if a trig operator is found.'''
        if node is None:
            #Base case for recursion--> it has looked through the entire tree without finding a trig operator.
            return False
        if node.value in trig_operators:
            #If the string value of the node is a trig operator, there is no need to recurse further.
            return True
        #Recurses to the left and right of the subtree to check if either branch contains a trig operator.
        return self._ContainsTrig(node.left) or self._ContainsTrig(node.right)
    
    def _CountCoeff(self,node):
        '''Used to extract a numeric value from a term subtree. An example: for 4*x the value 4.0 is returned.
        This is used when multiplying coefficients in the Multiply() method.
        Parameters:
        -node (Node)--> root of the term subtree.
        Returns:
        The numeric coefficients as a float value. The value 1.0 is returned by default if no coefficient is found.'''
        if node is None:
            #Base case for when no coefficient is found.
            return 1
        if node.IsLeaf() and node.value!='x':
            #If there is a leaf that doesn't have a value of x it must be a numerical value. Float representation of that value is returned.
            return float(node.value)
        if node.IsLeaf() and node.value=='x':
            #The value x on its own has a numeric coefficient of 1.
            return 1
        if node.value=='^' and node.left.value=='x':
            #x^n has a coefficient of 1. The power is not a coefficient.
            return 1
        if node.value=='*':
            #When there is a root multiplication node, coefficients from both sides of the subtree are multiplied together.
            return self._CountCoeff(node.left)*self._CountCoeff(node.right)
        return 1
    
    def _CountX(self,node,x_count=None):
        '''Counts the total degree of x in a subtree. An example: x^2 return an x count of 2 and x*x 
        returns an x count of 2. Used by Multiply() to add powers when combining x terms.
        Parameters:
        node (Node)--> root of the subtree to search.
        x_count (int)--> accumulator used during recursion. It is set to None in the initial call.
        Returns:
        The total degree of x represented in the subtree.'''
        if x_count is None:
            x_count=0
            #This prevents the x_count from resetting to None with each recursive call.
        if node is None:
            return 0
        if node.IsLeaf():
            if node.value=='x':
                #The plain value of x has a degree of 1.
                return 1 if node.value=='x' else 0
        if node.value=='^' and node.left.value=='x':
            #This is for when a x^n subtree is found. The right side's value will always be the power so that degree is returned.
            return int(node.right.value)
        if node.value=='*' or node.value in additive_operators:
            #If an operator is found, add the degrees of both sides of the subtree. 
            return self._CountX(node.left,x_count)+self._CountX(node.right,x_count)
        return x_count
    
    def _PathToX(self,node):
        '''This checks for if x is only reachable via '*' nodes. It is used in GetTransformationType()
        to distinguish between horizontal stretches and translations. A direct multiplication path to x indicates 
        a stretch.
        Parameters:
        -node (Node)--> root of the subtree that is to be searched.
        Returns:
        -True if an x value can only be reached through a '*' node.
        '''
        if node is None:
            return False
            #Base case
        if node.IsLeaf():
            return node.value=='x'
        if node.value=='*':
            #Only recurse when the root is a multiplication node. If it is a + or - then the method returns False.
            return self._PathToX(node.left) or self._PathToX(node.right)
        return False
    
    def _CopyTree(self,node):
        '''Creates a deep copy of a tree. Required by Expand() to duplicate branches during distribution
        without modifying the original tree. An example: when expanding (x+1)^2 copies of the tree are needed
         to build (x+1)*(x+1)
        Parameters:
         -node (Node)--> root of the subtree that is to be copied.
        Returns:
         -A new node that is a structural and value copy of the node used as the parameter. '''
        if node is None:
            return None
        #Recursively copy both children before creating the parent copy.
        return Node(node.value,self._CopyTree(node.left),self._CopyTree(node.right))

class EquationSimplifier(TreeAnalyser):
    '''Methods that contain the logic for expanding, multiplying and simplifying user inputs. Used by 
    EquationProcess to clean user inputs before graph type detection. Helps achieve core objective: 
    'It must be able to verify whether the input is a valid equation (a cubic, quadratic, linear, or simple trigonometric equation). 
    It must identify the corresponding graph type.'
    Methods are inherited from TreeAnalyser.'''
    def __init__(self,equation):
        '''Initialiser method
        Parameters"
        -equation (str)--> The equation string being simplified.'''
        self.equation=equation
    
    def Expand(self,node): 
        '''Distributes brackets in the tree using the distributive law. An example: 2*(x+3) becomes
        2*x+2*3. Brackets that are to the power of something such as (a+b)^n are handled by converting it
        into repeated multiplication before distributing.
        Parameters:
        -node (Node)-->root of the subtree to expand
        Returns:
        A restructured node with all the brackets fully distributed.'''
        if node is None or node.value=='x':
            #Base cases. Recursion stops.
            return node
        if node.value in trig_operators:
            node.right=self.Expand(node.right)
            #For trig functions, the argument on the inside of the brackets are expanded: for sin(2(x+1)), distributive law is applied to 2(x+1).
            return node
        if node.value=='^':
            if node.right is not None and node.left is not None and (node.left.value in additive_operators):
                #(a+b)^n is converted to repeated multiplication and then expanded.
                power=int(node.right.value)
                tree=self._CopyTree(node.left)
                #Creates an initial copy of the bracketed equation.
                for i in range(power-1):
                    tree=Node('*',self._CopyTree(node.left),tree)
                    #Repeatedly multiply copies of the equation together: (a+b)*(a+b) etc.
                node=self.Expand(tree)
                #Expands the resulting multiplication tree.
        if node.value=='-' and node.right and not node.right.IsLeaf():
            left=node.left if node.left else Node('0')
            node=Node('+', left, Node('*', Node('-1'), node.right))
            #Rewrite a-(equation) as a+(-1*equation) so distribution can proceed normally.
            return self.Expand(node)
        if node.value=='*':
            #Handle distributive multiplication.
            node.left=self.Expand(node.left)
            node.right=self.Expand(node.right)
            #Expands both sides before distributing.
            if node.right is not None and (node.right.value in additive_operators):
                #Distribute when the right branch contains addition/subtraction.
                branch1=Node('*',self._CopyTree(node.left),node.right.left)
                branch2=Node('*',self._CopyTree(node.left),node.right.right)
                #Multiply the left branch by both terms on the right.
                branch1=self.Expand(branch1)
                branch2=self.Expand(branch2)
                #Recursively expand the resulting branches.
                return Node(node.right.value,branch1,branch2)
                #Rebuild the distributed equation using the original operator
            if node.left is not None and (node.left.value in additive_operators):
                branch1=Node('*',node.left.left,self._CopyTree(node.right))
                branch2=Node('*',node.left.right,self._CopyTree(node.right))
                branch1=self.Expand(branch1)
                branch2=self.Expand(branch2)
                return Node(node.left.value,branch1,branch2)
                #Same proccess but for when the left branch contains a +/- operator.
            if node.left is not None and node.left.IsLeaf() and node.right is not None and  node.right.value=='*':
                return Node('*',Node('*',node.left,node.right.left),node.right.right)
                #Turn a*(b*c) into (a*b)*c for consistent left-associative structure.
        node.left=self.Expand(node.left)
        node.right=self.Expand(node.right)
        #Continues recursively expanding remaining branches.
        return node
    
    def _EvaluateConstantPower(self,node):
        '''Evaluates a power node where both values are numeric constants.
            An example 2^3 becomes 8.0.
            Parameters:
            -node (Node)-->a '^' node with numeric children.
            Returns:
            A new leaf node containing the computed result.'''
        return Node(str(float(node.left.value)**float(node.right.value)))
        #Compute base^exponent and store the result as a new leaf node

    def Multiply(self,node): 
        '''Simplifies multiplication nodes by combining coefficients and adding x powers.
        An example:3*x*2*x^2 becomes 6*x^3. Also delegates constant (numerical values) power evaluation to _EvaluateConstantPower().
        Parameters:
        -node (Node)-->root of the node of the subtree to simplify.
        Returns:
        -A simplified Node with multiplications completed where possible.'''
        if node.value in trig_operators:
            node.right=self.Multiply(node.right)
            #Simplify the argument of the trig function but leave the function node itself.
            return node
        if node.value=='*':
            node.left=self.Multiply(node.left)
            node.right=self.Multiply(node.right)
            #Recursively simplify both branches first.
            if self._ContainsTrig(node.left) or self._ContainsTrig(node.right):
                coeff_left=self._CountCoeff(node.left) if not self._ContainsTrig(node.left) else 1
                coeff_right=self._CountCoeff(node.right) if not self._ContainsTrig(node.right) else 1
                #For trig equations, it combines the numeric coefficient with the trig node.
                if self._ContainsTrig(node.left):
                    return Node('*',(Node(str(coeff_left*coeff_right))),node.left)
                    #If the coefficient is on the right, combine and place trig on the right.
                if self._ContainsTrig(node.right):
                    return Node('*',(Node(str(coeff_left*coeff_right))),node.right)
                    #Do the same but for the left.
            if (node.left.value not in additive_operators) and (node.right.value not in additive_operators):
                coeff_1=self._CountCoeff(node.left)
                count_1=self._CountX(node.left)
                coeff_2=self._CountCoeff(node.right)
                count_2=self._CountX(node.right)
                return Node('*',Node(str(coeff_1*coeff_2)),Node('^',Node('x'),Node(str(count_1+count_2))))
                #Both sides are simple terms, multiply the coefficients and add the powers.
        if node.value in additive_operators:
            node.left=self.Multiply(node.left)
            node.right=self.Multiply(node.right)
            #Recurse and multiply into both sides of the +/- node.
        if node.value=='^' and self._ContainsX(node.left):
            return node
            #For x^n leave it as it is (already in its most simple form).
        if node.value=='^' and (not self._ContainsX(node.left) and not self._ContainsX(node.right)):
            if (node.left and node.right) and (node.left.IsLeaf() and node.right.IsLeaf()):
                return self._EvaluateConstantPower(node) 
                #Both sides are constant (numerical values). Multiply and evaluate them numerically.      
        return node
    
    def CollectLikeTerms(self,node,cubic_coefficients=None,quadratic_coefficients=None,linear_coefficients=None,constants=None,negate=False): 
        '''Traverses through the tree and accumulates coefficients by degree. Sign changes are tracked through '-' 
        nodes the 'negate' flag. When a subtraction node is encountered, the right branch is traversed with negative as True.
        Parameters:
        -node (Node)--> root of subtree to collect from.
        -cubic_coefficients (list)--> stores a list of identified x^3 coefficients.
        -quadratic_coefficients (list)--> stores a list of identified x^2 coefficients.
        -linear coefficients (list)--> stores a list of identified x^1 coefficients.
        -constants (list)--> stores a list of regular constants.
        -negate (bool)--> whether or not to negate values on this branch.
        Returns:
        -A tuple of 4 lists: (cubic_coefficients,quadratic_coefficients,linear_coefficients,constants)'''
        if cubic_coefficients is None:
            cubic_coefficients=[]
        if quadratic_coefficients is None:
            quadratic_coefficients=[]
        if linear_coefficients is None:
            linear_coefficients=[]
        if constants is None:
            constants=[]     
        #This was done for all the lists so they don't reset to None when recursively called.  
        if node is None:
          return cubic_coefficients,quadratic_coefficients,linear_coefficients,constants
        #Base case to end recursion.
        if node.value == 'x':
            linear_coefficients.append(float(_ApplyNegative('1', negate)))
            return cubic_coefficients,quadratic_coefficients,linear_coefficients,constants  
        #Plain x has a coefficient of 1. Apply negate to it and append it to the linear_coefficients list.
        if node.value=='^':
            if self._ContainsX(node.left):
                #Handles powers of x.
                if node.right.value=='3':
                    cubic_coefficients.append(float(_ApplyNegative('1',negate)))
                    #Classify cubic terms.
                elif node.right.value=='2':
                    quadratic_coefficients.append(float(_ApplyNegative('1',negate)))
                    #Classify quadratic terms.
            return cubic_coefficients,quadratic_coefficients,linear_coefficients,constants
        if node.value=='*':
            if self._ContainsX(node.left):
                #Handles multiplied terms like 4*x or 3*x^2
                if node.left.value=='^':
                    if node.left.right.value=='3':
                        cubic_coefficients.append(float(_ApplyNegative(node.right.value,negate)))
                    elif node.left.right.value=='2':
                        quadratic_coefficients.append(float(_ApplyNegative(node.right.value,negate)))
                    #Handles multiplied powers such as 3*x^2.
                elif node.left.value=='x':
                    linear_coefficients.append(float(_ApplyNegative(node.right.value,negate))) 
                    #Handles multiplied linear terms such as 4*x.
            if self._ContainsX(node.right):
                if node.right.value=='^':
                    if node.right.right.value=='3':
                        cubic_coefficients.append(float(_ApplyNegative(node.left.value,negate)))
                    elif node.right.right.value=='2':
                        quadratic_coefficients.append(float(_ApplyNegative(node.left.value,negate)))
                elif node.right.value=='x':
                        linear_coefficients.append(float(_ApplyNegative(node.left.value,negate)))
            #Does the same but for the right (for terms like x*4 and x^2*3).
            return cubic_coefficients,quadratic_coefficients,linear_coefficients,constants
        if node.value=='-':
            #Handles subtraction operations.
            self.CollectLikeTerms(node.left,cubic_coefficients,quadratic_coefficients,linear_coefficients,constants,negate) 
            self.CollectLikeTerms(node.right,cubic_coefficients,quadratic_coefficients,linear_coefficients,constants,not negate)
            #Traverse the left branch normally but negate the terms collected from the right branch (for 4-2, 2 would be read as -2.
            if not self._ContainsX(node.right) and node.right.IsLeaf():
                constants.append(float(_ApplyNegative(node.right.value,True)))
                #Collect right side values as negative.
            if not self._ContainsX(node.left) and node.left.IsLeaf():
                constants.append(float(_ApplyNegative(node.left.value,False))) 
                #Collect the left side normally. 
        elif node.value=='+':
            self.CollectLikeTerms(node.left,cubic_coefficients,quadratic_coefficients,linear_coefficients,constants) 
            self.CollectLikeTerms(node.right,cubic_coefficients,quadratic_coefficients,linear_coefficients,constants) 
            if not self._ContainsX(node.right) and node.right.IsLeaf():
                constants.append(float(_ApplyNegative(node.right.value,False)))
            if not self._ContainsX(node.left) and node.left.IsLeaf():
                constants.append(float(_ApplyNegative(node.left.value,False)))
            #Collects both sides normally with no negate applied.
        return cubic_coefficients,quadratic_coefficients,linear_coefficients,constants
    
    def FormatLikeTerms(self,cubic_coefficients,quadratic_coefficients,linear_coefficients,constants):
        '''Formats the collected coefficient lists into a readable equation for validation.
            Terms with a coefficient of 0 are ignored for the output.
            Terms are joined with '+' (PostTraverseClean() already handles any '+-' operators.)'''
        cubic_sum=sum(cubic_coefficients) if cubic_coefficients else 0
        quadratic_sum=sum(quadratic_coefficients) if quadratic_coefficients else 0
        linear_sum=sum(linear_coefficients) if linear_coefficients else 0
        constants_sum=sum(constants) if constants else 0
        #The sum of the coefficients are added.
        result=[]
        if cubic_sum!=0:
            result.append(f'{cubic_sum}x^3')
        if quadratic_sum!=0:
            result.append(f'{quadratic_sum}x^2')
        if linear_sum!=0:
            result.append(f'{linear_sum}x')
        if constants_sum!=0:
            result.append(str(constants_sum))
        final='+'.join(result) if result else '0'
        #All coefficients are joined into a single string with a '+'.
        return final
    
    def CollectTrigConstants(self,node,constants=None,negative=False):
        '''Collects numeric constants from outside the trig function nodes. Recursion stops at trig nodes 
        so only outside constants are collected. An example:  2sin(x)+3+4. 3 and 4 are collected.
        Parameteres:
        -node (Node)-->root of the subtree to collect from
        -constants (list)-->stores list of all appended constant values.
        -negative (bool)--> whether to negate values on this branch or not.
        Returns:
        -constant '''
        if constants is None:
            constants=[]
            #Ensures constants doesn't reset
        if node.value in trig_operators:
            return constants
            #Base case. When trig operator is hit, stop recursing.
        if node.IsLeaf():
            if node.value!='x' and node.value!='':
                constants.append(-float(node.value) if negative else float(node.value))
                #Apply sign and append the numeric leaf value.
            return constants
        if node.value=='+':
            self.CollectTrigConstants(node.left, constants, negative)
            self.CollectTrigConstants(node.right, constants, negative)
            #Both sides of '+' keep the current sign.
        if node.value=='-':
            self.CollectTrigConstants(node.left, constants, negative)
            self.CollectTrigConstants(node.right, constants, not negative)
            #Left keeps sign, right flips.
        if node.value=='*':
            if not self._ContainsTrig(node):
                coefficient=self._CountCoeff(node)
                constants.append(-coefficient if negative else coefficient)
                #Numeric multiplication. For values like 2*3sin(x), it'll count it as a single constant (6)
        return constants
    
    def FormatTrigWithConstants(self,node,constants_sum=0):
        ''' Formats a trig expression tree into a readable equation string.
         Handles the trig function node, its argument, and any outer constants.
         Parameters: 
         -node (Node)-->root of the trig expression subtree.
         -constants_sum (float)-->total of outer constants passed down recursion.
        Returns:
        Fully formatted equation such as: 2.0sin(x-2.0)'''
        if node.IsLeaf():
            return node.value if node.value!='x' else ''
            #Leaf node reached. Return its value if it's a constant. If it is x, return an empty string.
        if node is None:
            return ''
            #Base case for empty nodes.
        if node.value in trig_operators:
            cubic_coefficients,quadratic_coefficients,linear_coefficients,constants=self.CollectLikeTerms(node.right)
            #Collect polynomial terms inside the trig brackets.
            brackets=self.FormatLikeTerms(cubic_coefficients,quadratic_coefficients,linear_coefficients,constants)
            return f'{node.value}({brackets})'
            #Format the argument inside the brackets using polynomial formatting.
        if node.value in additive_operators:
            #Handle addition and subtraction equations.
            constants=self.CollectTrigConstants(node)
            constants_sum=sum(constants)
            #Collect all non-trig constants in the subtree.
            trig_result=''
            if self._ContainsTrig(node.left):
                trig_result+=self.FormatTrigWithConstants(node.left,constants_sum)
                #Format trig equations from the left branch.
            if self._ContainsTrig(node.right):
                trig_result+=self.FormatTrigWithConstants(node.right,constants_sum)
                #Do the same but for the rigth branch.
            if constants_sum!=0:
                if trig_result!='':
                    trig_result=re.sub(r'[+-]\d*\.?\d*$','',trig_result)
                    #Remove trailing constants before appending the combined value. (Regular expression pattern matches values such as -10.5 and +5).
                    return f'{trig_result}+{constants_sum}'
                else:
                    return str(constants_sum)
                    #Return constants alone if no trig expression exists.
            return trig_result
        if node.value=='*':
            #Handle multiplication equations.
            if node.left is not None:
                left=self.FormatTrigWithConstants(node.left,constants_sum)
                #Format the left branch if it exists.
            else:
                left=''
            if node.right is not None:
                right=self.FormatTrigWithConstants(node.right,constants_sum)
                #Format the right branch if it exists.
            else:
                right=''
            if left=='':
                return right
            if right=='':
                return left
            #Return whichever branch isn't empty.
            return f'{left}*{right}'
        result=''
        if node.left is not None:
            result+=self.FormatTrigWithConstants(node.left,constants_sum)
        if node.right is not None:
            result+=self.FormatTrigWithConstants(node.right,constants_sum)
            #Continue recursively traversing remaining branches so all trig expressions within the subtree are processed.
        return result if result else ''
    
class TransformationAnalyser(TreeAnalyser):
    '''Analyses the parse tree of a transformed equation to extract the order and type of transformations.
      Helps achieve objective: The program must be able to support transformation types such as translations, reflections and 
      stretches for all appropriate graph types. And objective: Nested and multiple transformations must also be supported with ease and must be in the correct order.
      It analyses linear, vertex and trigonometric equations. It inherits methods from Tree Analyser.'''
    def __init__(self,equation):
       '''Initialiser
       Parameter:
       -equation (str)--> original unsimplified equation to analyse.'''
       self.equation=equation

    def IsVertex(self,node,is_vertex=False):
        '''Checks whether an equation is in vertex form.
        Vertex form equations like 2(x+3)^2+1 can be directly traversed for transformations.
        Parameters:
        -node (Node)-->root of the tree to be analysed
        -is_vertex (bool)-->recursion flag.
        Returns: 
        -True if the equation is in vertex form'''
        if node is None or node.value=='x':
            return False
            #Base case. Recursion stops here.
        if node.value=='^' and (node.left is not None and self._ContainsX(node.left) and node.left.value!='x'):
                 #Checks for a '^' node whose left child contains x but isn't a plain x. (This means that there is an x inside a bracket.)
                if self._CountX(node.left)==1:
                    return True
                    #If there is exactly one x inside the bracket, it is in vertex form.
                else:
                    return False
        if node.value in additive_operators:
            if self._ContainsX(node.left) and self._ContainsX(node.right):
                return False
                #At a +/- node, if x appears in both branches, it is expanded form not vertex form.
            return self.IsVertex(node.right,is_vertex) or self.IsVertex(node.left,is_vertex)
        if node.value=='*':
            if self._ContainsX(node.left) and self._ContainsX(node.right):
                #If there is an x on both sides of the '*' node it is not a vertex.
                return False
            return self.IsVertex(node.right,is_vertex) or self.IsVertex(node.left,is_vertex)
            #Recursively checks for a vertex on each branch.
        return is_vertex   
   
    def _GetOperator(self,node,operators=None):
        '''Traverses the tree and collects all operators along the path to x.
            Only follows branches that contain x or trig.
            Parameters:
            -node (Node)-->root of the subtree that is to be analysed.
            -operators (list)-->a list of all operator strings in traversal order.
            Returns:
            -The list of operators.'''
        if operators is None:
            operators=[]
            #Initialises the list on the first call (prevents list from resetting with every recursive call).
        if node is None or node.IsLeaf():
            return operators
            #Base case for recursion.
        operators.append(node.value)
        #Appends every operator that is on the path to a trig operator or x.
        if self._ContainsTrig(node.left) or self._ContainsX(node.left):
            self._GetOperator(node.left,operators)
        elif self._ContainsTrig(node.right) or self._ContainsX(node.right):
                self._GetOperator(node.right, operators)
        #If a trig oprator or x is found in any branch, the method recurses deeper into that branch.
        return operators

    def _GetValues(self,node,values=None):
        '''Traverses the tree and collects the constant values paired with each operator along the path to x.
            Always follows the branch containing x, collecting the constant from the other side.
            Parameters:
            -node (Node)--> root of the subtree to be analysed.
            -values (list)--> a list of constants that transform the equation in traversal order.'''
        if values is None:
            values=[]
            #Ensures that the list doesn't reset with the first call.
        if node is None or node.IsLeaf():
            return values 
            #Base case for recursion.
        if self._ContainsTrig(node.left) or self._ContainsX(node.left):
            x_side=node.left
            constant_side=node.right
        else:
            x_side=node.right
            constant_side=node.left
        #Identifies which side contains the x and which side contains the constant.
        if constant_side is not None and constant_side.IsLeaf() and constant_side.value!='x' and constant_side.value!='':
            values.append(constant_side.value)
            #Appends the constant leaf value to the list of constants if it exists.
        return self._GetValues(x_side,values)
        #Recurses to the x branch to identify remaining constants.
    
    def _GetTransformationType(self,node,transform_type=None,to_find=None,found=False):
        '''Traverses the tree and classifies each operator as acting on 'x' or 'y'.
            Operators outside of brackets act on y,
            operators inside act on x. Uses _PathToX() to distinguish stretches from translations.
            Parameters:
            -node (Node)--> root of subtree to be analysed.
            -transform_type(list)-->List that stores all x and y transformation in traversal order.
            -to_find(str)--> A specific trigger to search for to identify whether it is a y or x transformation.
            -found(bool)--> Whether a trigger has been found yet.
            Returns:
            -The transform_type list with y or x values appended based on traversal order. '''
        if transform_type is None:
            transform_type=[]
            #Ensures list doesn't reset with every call.
        if to_find is None: 
            if 'sin' in self.equation:
                to_find='sin'
            elif 'cos' in self.equation:
                to_find='cos'
            elif 'tan' in self.equation:
                to_find='tan'
            elif '^' in self.equation:
                to_find='^'
            else:
                to_find=None #Linear equations don't have a trigger like vertex and trig equations do so it is set to None.
            #Determines what the trigger node is based on the equation type.
            #Everything before the trigger acts on y, everything after acts on x.
        if node is None or node.IsLeaf():
            return transform_type
            #Base case for recursion.
        if (node.value in additive_operators) and to_find is None:
            #For linear equations, _PathToX() is used to distinguish between x and y translations instead of a trigger.
            #A +/- that leads directly to x via multiplication is a horizontal translation, if it doesn't it's vertical.
            if self._ContainsX(node.left) or self._ContainsTrig(node.left):
                x_side=node.left
                constant_side=node.right
            else:
                x_side=node.right
                constant_side=node.left
            if self._PathToX(x_side):
                #X is only reachable via '*' from this node so it's an x transformation.
                if constant_side is not None and constant_side.IsLeaf() and constant_side.value!='x' and constant_side.value!='':
                    transform_type.append('x' if found else 'y')
        if to_find is None:
            #No anchor: you need to classify each operator by whether found is set.
            #Found being True means the point where x transformations begin has already been passed.
            if self._ContainsX(node.left) or self._ContainsTrig(node.left):
                x_side=node.left
                constant_side=node.right
            else:
                x_side=node.right
                constant_side=node.left
            new_found=found
            if constant_side is not None and constant_side.IsLeaf() and constant_side.value!='x' and constant_side.value!='':
                if node.value=='*':
                    if x_side.IsLeaf() and x_side.value=='x':
                        transform_type.append('x')
                        #If a leaf node is directly being multiplied by an x value (like 2*x), it is a stretch in the x direction.
                    else:
                        transform_type.append('y')
                        #If there is no direct multiplication, it is a y stretch.
                    new_found=True #An indication that a multiplication has now been identified.
                else:
                    #This is for a +/- operator. Found tracks whether we are inside the brackets or not.
                    #If found is false, it is a y translation else it is an x translation.
                    transform_type.append('x' if found else 'y')
                    new_found=found
            return self._GetTransformationType(x_side,transform_type,to_find,new_found)
        if node.value==to_find:
            #If the trigger node is found, found is set to True and all subsequent transformations are x transformations. 
            #Everything from here deeper into the tree acts on x.
            if node.value=='^':
                return self._GetTransformationType(node.left,transform_type,to_find,True)
            else:
                return self._GetTransformationType(node.right,transform_type,to_find,True)
        #The trigger hasn't been found yet all transformations currently are y transformations
        if self._ContainsX(node.left) or self._ContainsTrig(node.left):
            x_side=node.left
            constant_side=node.right
        else:
            x_side=node.right
            constant_side=node.left
        if constant_side is not None and constant_side.IsLeaf() and constant_side.value!='x' and constant_side.value!='':
            transform_type.append('x' if found else 'y')
        #The algorithm keeps recursing deeper into the x_side until the trigger is found. 
        return self._GetTransformationType(x_side,transform_type,to_find,found)

    def GetOrder(self,node):
        '''Combines the results of _GetOperator(), _GetValues() and _GetTransformationType()
        into a single ordered list of transformation dictionaries.
        '^' and trig operator nodes are taken out since they are triggers and not transformations.
        Parameters: 
        -node (Node)-->root of the parse tree.
        Returns:
        -list of dictionaries each with keys 'operator', 'value' and 'type' '''
        order=[]
        operators=self._GetOperator(node)
        values=self._GetValues(node)
        transform_type=self._GetTransformationType(node)
        i=0
        while i<len(operators):
            if operators[i]=='^':
                del operators[i]
                # '^' is a trigger value not a operator so it gets deleted.
                if i<len(values):
                    del values[i]
                    #Removes corresponding value to keep list aligned
            elif operators[i] in trig_operators:
                del operators[i] 
                #Same thing is applied for trig operators.
            else:
                i+=1
        for op,val,typ in zip(operators,values,transform_type):
            #All three lists are zipped and stored into a dictionary.
            trans={'operator':op,'value':val,'type':typ}
            order.append(trans)
        return order
