class Node:
    '''Represents a single node in a binary parse tree.
    Each node holds an operator or value and up to two children,
    left and right. Leaf nodes have no children and hold atomic values like numbers or 'x'.
    Operator nodes hold a symbol like '+' or '*' and have left and right subtrees.'''
    def __init__(self,value,left=None,right=None):
        '''Parameters:
            value (str)-->the operator or atomic value this node holds
            left (Node)-->left child subtree, None for leaf nodes
            right (Node)-->right child subtree, None for leaf nodes'''
        self.value=value
        self.left=left
        self.right=right

    def IsLeaf(self): 
        '''Checks whether this node is a leaf (has no children)
        Used heavily during tree traversal to identify atomic values and stop recursion.
        Parameters: 
        none
        Returns: 
        True if both left and right children are None'''
        if self.left is None and self.right is None:
            return True
        else:
            return False