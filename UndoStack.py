class StackNode:
    '''A single node in a linked list.
    Holds a data value and a reference to the next node.
    Used by LinkedStack to build the stack structure without a fixed-size array.'''
    def __init__(self,data):
        '''Parameters: 
        data-->the value stored in this node'''
        self.data=data
        self.next=None  #points to the node below this one in the stack, None if bottom

class LinkedStack:
    ''' A stack implemented as a singly linked list.
    New nodes are inserted at the head.
    Used by UndoRedo to maintain undo and redo history without a fixed size limit.'''
    def __init__(self):
        self.head=None #top of the stack: None when empty
        self.size=0

    def Push(self,data):
        '''Adds a new item to the top of the stack.
        The new node points to the current head, then becomes the new head.
        Parameters: 
        data-->value to push onto the stack
        Returns: 
        none'''
        new_node=StackNode(data)
        new_node.next=self.head #link new node to current top
        self.head=new_node #new node becomes the new top
        self.size+=1
    
    def Pop(self):
        '''Removes and returns the item at the top of the stack.
        Head is advanced to the next node, detaching the old top.
        Parameters: none
        Returns:
        data from the top node, or None if the stack is empty'''
        if self.head is None:
            return None
        data=self.head.data
        self.head=self.head.next #advance head to next node, old top is detached
        self.size-=1
        return data
    
    def Peek(self):
        '''Returns the top item without removing it.
        Used by Undo() to check the action type before popping.
        Parameters: 
        none
        Returns: 
        data from the top node, or None if the stack is empty'''
        if self.head is None:
            return None
        return self.head.data #returns top item
    
    def IsEmpty(self):
        '''Parameters: 
        none
        Returns: 
        True if the stack has no items'''
        return self.head is None
    
    def Clear(self):
        '''Empties the stack by removing the head reference.
        All nodes become unreachable and are garbage collected.
        Called on the redo stack whenever a new action is pushed,
        redoing after a new action would produce an inconsistent state.
        Parameters: 
        none
        Returns: 
        none'''
        self.head=None
        self.size=0
        
class UndoRedo:
    '''Manages undo and redo history using two LinkedStacks.
    Each state is a snapshot of the current equations and axis range stored as a dictionary
    Undo pops from the undo stack and pushes the current state to the redo stack.
    Redo does the reverse. The redo stack is cleared whenever a new action is pushed,
    branching redo history is not supported.
    _busy prevents Undo/Redo being called recursively if ViewTransformation triggers another push.'''
    def __init__(self,sidebar,ax,canvas):
        '''Parameters:
        sidebar-->reference to the sidebar for reading and restoring equation state
        ax-->matplotlib axes for reading and restoring axis limits
        canvas-->tkinter canvas for triggering redraws'''
        self.sidebar=sidebar
        self.ax=ax
        self.canvas=canvas
        self.undo_stack=LinkedStack()
        self.redo_stack=LinkedStack()
        self._busy=False
        
    def Push(self,action='transformation'):
        '''Saves the current screen state to the undo stack and clears the redo stack.
        Called before any action that should be undoable.
        Parameters: 
        action (str)-->'transformation' or 'range', used by Restore() to replay correctly
        Returns: 
        none'''
        self.undo_stack.Push(self.SaveScreen(action=action))
        self.redo_stack.Clear() #new action invalidates any existing redo history
 
    def SaveScreen(self,action='transformation'):
        ''' Captures the current application state as a dictionary snapshot.
        Stores all equation strings, axis limits and show_coords setting 
        (everything needed to fully restore the display to this moment).
        Parameters: 
        action (str)-->the type of action this snapshot represents
        Returns:
        dictionary with keys 'action', 'equations', 'x_min', 'x_max', 'y_min', 'y_max', 'show_coords' '''
        equation_list=[]
        for equation in self.sidebar.equation_list:
            eq=equation.equation_entry.get() 
            equation_list.append(eq) #store equation strings
        return {'action':action,'equations':equation_list,'x_min':self.ax.get_xlim()[0],'x_max':self.ax.get_xlim()[1],'y_min':self.ax.get_ylim()[0],'y_max':self.ax.get_ylim()[1],'show_coords':getattr(self.sidebar, 'show_coords', True)}

    def Undo(self):
        '''Restores the previous state from the undo stack.
        Current state is saved to the redo stack first so it can be recovered.
        Range-only changes just redraw, transformation changes call ViewTransformation()
        to rebuild the graph without animating.
        Parameters: 
        none
        Returns: 
        none'''
        if self.undo_stack.IsEmpty():
            return
        self._busy=True  #prevent re-entrant calls while restoring
        current_action=self.undo_stack.Peek()['action'] #check action type before popping
        current=self.SaveScreen(action=current_action)
        state=self.undo_stack.Pop()
        self.redo_stack.Push(current) #save current state so it can be redone
        self.Restore(state)
        if state['action']=='range':
            self.canvas.draw()  #range changes only need a redraw (no transformation replay needed)
        else:
            self.sidebar.ViewTransformation(push=False,animate=False)
        self.canvas.draw()
        self._busy=False

    def Redo(self):
        '''Restores the next state from the redo stack.
        Current state is saved to the undo stack first so it can be undone again.
        Transformation changes are replayed with animation, redo shows the transformation happening again.
        Parameters: 
        none
        Returns: 
        none'''
        if self._busy==True or self.redo_stack.IsEmpty():
            return 
        self._busy=True
        current=self.SaveScreen()
        state=self.redo_stack.Pop()
        self.undo_stack.Push(current)  #save current state so this redo can itself be undone
        self.Restore(state)
        if state['action']=='range':
            self.canvas.draw()
        else:
            self.sidebar.ViewTransformation(push=False,animate=True) #redo replays with animation
        self.canvas.draw() 
        self._busy=False
        
    def Restore(self,state):
        '''Rebuilds the UI from a saved state snapshot.
        All existing equation rows are destroyed and recreated from the saved equation strings.
        Axes are cleared and limits restored to match the saved range.
        Parameters: 
        state (dict)-->snapshot produced by SaveScreen()
        Returns: 
        none'''
        #destroy all current equation rows before rebuilding (avoids stale UI state)
        for equation in self.sidebar.equation_list[:]: 
            self.sidebar.equation_list.remove(equation)
            equation.frame.destroy()
        for eq in state['equations']:
            self.sidebar.AddEquation()
            self.sidebar.equation_list[-1].equation_entry.insert(0,eq) #populate entry with saved string
        self.ax.cla() #clear all plotted data
        self.ax.autoscale(False)
        self.ax.axvline(0,color='black')
        self.ax.axhline(0,color='black')
        self.ax.grid(True)
        self.ax.set_xlim(state['x_min'],state['x_max']) #restore saved axis limits
        self.ax.set_ylim(state['y_min'],state['y_max'])
        self.sidebar.show_coords=state.get('show_coords', True) #restore coordinate display setting