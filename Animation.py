from tkinter import *
from DisplayGraph import *
from GraphClass import *
from TransformationClass import *
from SplitCoordinates import *

frame_count=24 #number of interpolation frames per transformation step-->higher means smoother animation
max_y_value=1000 #y values beyond this are treated as discontinuities and plotted as None

class Animation:
    '''Handles the step-by-step animated display of graph transformations.
    Each transformation step is broken into frame_count interpolated frames-->coordinates are linearly interpolated 
    between the start and end state of each step.
    Multiple animations can run simultaneously (one per equation) and are synchronised
    through all_animations so every graph moves at the same time.
    The first animation in all_animations acts as the controller-->it drives PlayStack()
    and all others follow its frame index.'''
    def __init__(self,engine,ax,canvas,descriptions,descriptions_box,speed,show_coords,sidebar):
        ''' Parameters:
            engine (TransformationEngine)-->provides transformation steps and coordinates
            ax-->matplotlib axes to draw on
            canvas-->tkinter canvas wrapping the matplotlib figure
            descriptions (list)-->list of description strings, one per transformation step
            descriptions_box-->tkinter Text widget to display step descriptions
            speed (int)-->milliseconds between frames (lower is faster)
            show_coords (bool)-->whether to plot key coordinates after animation completes
            sidebar-->reference to sidebar for reading show_coords state at draw time'''
        self.engine=engine
        self.ax=ax
        self.canvas=canvas
        self.descriptions=descriptions
        self.descriptions_box=descriptions_box
        self.speed=speed
        self.sidebar=sidebar
        self.show_coords=show_coords
        self.current_frame=None #the coordinate list currently being displayed-->list of (x,y) tuples
        self.all_animations=[] #shared list of all active Animation instances-->set before Play() is called
        self._after_id=None #stores the tkinter after() id so frames can be cancelled if needed

    def _ResetAxes(self):
        '''Clears the axes and redraws the grid and axis lines while preserving the current range.
        Called before drawing each frame so previous frame content is removed.
        Parameters: 
        none
        Returns: 
        tuple of (x_min, x_max, y_min, y_max) — the preserved axis limits'''
        x_min,x_max=self.ax.get_xlim()
        y_min,y_max=self.ax.get_ylim()
        self.ax.cla()  #clear all plotted content
        self.ax.autoscale(False)
        self.ax.axvline(0,color='black')
        self.ax.axhline(0,color='black')
        self.ax.grid(True)
        self.ax.set_xlim(x_min,x_max) #restore limits after clearing
        self.ax.set_ylim(y_min,y_max)
        return x_min,x_max,y_min,y_max
        
    def GenerateFrames(self):
        '''Generates interpolated coordinate frames for every transformation step.
        For each step, frame_count frames are created by linearly interpolating between
        the start and end coordinate lists (giving the appearance of smooth movement).
        Coordinates are stored as lists of (x,y) tuples. None y values are preserved
        throughout to maintain discontinuities in trig graphs.
        The output structure is a list of steps, each containing a list of frames,
        each frame being a list of (x,y) tuples: [[[( x,y),...], ...], ...]
        Parameters: 
        none
        Returns: 
        list of transformation steps, each containing frame_count coordinate lists
        '''
        frame_list=[]
        trans_list=self.engine.TransformationList()  #list of coordinate snapshots: [[(x,y),...], ...]
        for i in range(len(trans_list)-1):
            start_x,start_y=SplitCoordinates(trans_list[i])  #coordinates before this transformation
            end_x,end_y=SplitCoordinates(trans_list[i+1])  #coordinates after this transformation
            transformation_frames=[]
            for j in range(frame_count):
                single_frame=[]
                for k in range(len(start_x)):
                    if start_y[k] is None or end_y[k] is None:
                        single_frame.append((start_x[k],None)) #preserve discontinuity through all frames
                    else:
                        #linear interpolation: at j=0 we're at start, at j=frame_count-1 we're at end
                        x=start_x[k]+(end_x[k]-start_x[k])*(j/(frame_count-1))  
                        y=start_y[k]+(end_y[k]-start_y[k])*(j/(frame_count-1))
                        if x is not None:
                            x=round(x,10)
                        if y is not None:
                            y=round(y,10)
                        if abs(y)>max_y_value:
                            single_frame.append((x,None)) #set extreme y values to None (tan asymptotes).
                        else:
                            single_frame.append((x,y))
                transformation_frames.append(single_frame)
            frame_list.append(transformation_frames)
        return frame_list
    
    def CreateTuple(self):
        ''' Pairs each transformation's frame list with its description string.
        Produces a stack of (frames, description) tuples that PlayStack() consumes in order.
        Parameters: 
        none
        Returns: 
        list of (frame_list, description) tuples, one per transformation step'''
        frame_list=self.GenerateFrames()
        final_list=list(zip(frame_list,self.descriptions)) #pair frames with their description
        return final_list
    
    def Play(self):
        '''Entry point for starting the animation sequence.
        Only the first animation in all_animations acts as the controller-->it builds the stack for
        every animation and starts PlayStack().
        This ensures all graphs are synchronised from a single driver.
        Parameters: 
        none
        Returns: 
        none'''
        if self==self.all_animations[0]: #only the controller initialises and drives playback
            for animate in self.all_animations:
                animate._stack=animate.CreateTuple() #build frame stacks for all animations
            self.PlayStack(transformation_index=0,frame_index=0)
    
    def UpdateDescription(self,transformation_index,description):
        '''Appends a step description to the description box for this animation's equation.
        The box is briefly unlocked to insert text then locked again to prevent user edits.
        Parameters:
        transformation_index (int)-->current step number, shown as 'Step N'
        description (str)-->description of the transformation'''
        self.descriptions_box.configure(state=NORMAL)
        self.descriptions_box.insert(END,f'Step {transformation_index+1}: {description}\n')
        line_count=self.descriptions_box.index(END).split('.')[0]
        self.descriptions_box.configure(height=line_count,state=DISABLED)

    def _PlotFinalState(self,any_rotation,x_min,x_max):
        '''Plots the final transformed state of all graphs with optional coordinate annotations.
        Chooses between rotated, trig and standard coordinate plotting based on the graph type
        and whether any rotation transformation was applied.
        Parameters:
        any_rotation (bool)-->whether any Rotation transformation is present
        x_min, x_max (float)-->current axis x range for setting graph range'''
        all_graphs=[]
        shared_plotted=[] #shared list prevents the same coordinate being annotated twice across graphs
        for animate in self.all_animations:
            if animate.current_frame is not None:
                if animate.engine:
                    all_graphs.append(animate.engine.graph)
        for position,animate in enumerate(self.all_animations):
                if animate.current_frame is not None:
                    #draw the final transformed graph
                    display=DisplayGraph(animate.engine.graph)
                    display.plotted=shared_plotted
                    DrawSegmentedLines(self.ax,animate.current_frame) 
                    animate.engine.graph.SetRange(x_min,x_max)
                    graph_type=animate.engine.graph.graph_type
                    current_show_coords=getattr(self.sidebar,'show_coords',False) #coordinates are shown if toggled.
                    if current_show_coords==True:
                        if any_rotation==True or graph_type in trig_operators:
                            # rotated and trig graphs can't use standard coordinate methods-->use their own respective methods.
                            display.PlotTrigRotCoordinates(self.ax,animate.current_frame)
                            if any_rotation and graph_type not in trig_operators:
                                display.PlotRotatedIntersections(self.ax,all_graphs,position)
                            else:
                                display.PlotTrigIntersections(self.ax,all_graphs,position)
                        else:
                            display.PlotCoords(self.ax,all_graphs,position)

    def _FindFinalCoordinates(self,any_rotation,x_min,x_max):
        '''Computes the final transformed coordinates for all animations after the stack is exhausted.
        Stores results in current_frame for plotting and in eval_coords for intersection detection.
        For rotated graphs, eval_coords uses the transformed coordinates directly since
        the graph can no longer be evaluated algebraically after rotation.
        Parameters:
        any_rotation (bool)-->whether any Rotation transformation is present
        x_min, x_max (float)-->current axis x range'''
        for animate in self.all_animations:
            if animate._stack:
                base=animate.engine.BaseEquation()
                base.SetRange(animate.engine.graph.x_min,animate.engine.graph.x_max)
                animate.engine.start_coords=base.GetCoordinates()
                animate.current_frame=animate.engine.ApplyAll() #apply all transformations to get final state
                animate.engine.graph.transformed_coords=animate.current_frame
                animate.engine.graph.SetRange(x_min,x_max)
                if any_rotation==True:
                    #rotated graphs can't be re-evaluated from x values-->store transformed coords for intersection use
                    animate.engine.graph.eval_coords=animate.current_frame
                else:
                    animate.engine.graph.eval_coords=animate.engine.graph.GetCoordinates()
    
    def _AnyRotation(self):
        ''' Checks whether any active animation includes a Rotation transformation.
        Used to switch between standard and rotated coordinate/intersection methods.
        Parameters: 
        none
        Returns: 
        True if at least one Rotation transformation exists across all animations'''
        any_rotation=False
        for animate in self.all_animations:
            for i in animate.engine.transformations:
                if isinstance(i,Rotation):
                    any_rotation=True
                    break # found one, no need to check further--> rotations applied to every graph
        return any_rotation
    
    def CompleteAnimation(self):
        '''Called when all transformation steps have been animated.
        Resets axes, computes final coordinates and plots the final state with annotations.
        Parameters: 
        none
        Returns: 
        none'''
        x_min,x_max,y_min,y_max=self._ResetAxes()
        any_rotation=self._AnyRotation()
        self._FindFinalCoordinates(any_rotation,x_min,x_max)
        self._PlotFinalState(any_rotation,x_min,x_max)
        self.canvas.draw()

    def UpdateAllDescription(self,transformation_index): 
        '''Updates the description box for every active animation at the start of a new step.
        Called once per transformation step before frames begin playing.
        Parameters: 
        transformation_index (int)-->index of the current transformation step
        '''
        for animate in self.all_animations:
            if transformation_index<len(animate._stack):
                unused_frame,description=animate._stack[transformation_index]
                animate.UpdateDescription(transformation_index,description)
        
    def PlayStack(self,transformation_index,frame_index):
        '''Recursive method that drives the animation frame by frame using tkinter's after().
        Only the controller (first in all_animations) calls this-->other animations follow.
        At each call it draws the current frame for all animations, then schedules the next call.
        When all frames in a step are done it moves to the next transformation step.
        When all steps are done it calls CompleteAnimation().
        Parameters:
        transformation_index (int)-->which transformation step is currently playing
        frame_index (int)-->which frame within that step is currently displaying'''
        if self!=self.all_animations[0]:
            return #only the controller drives playback
        if not transformation_index<len(self._stack):
            self.CompleteAnimation() #all steps exhausted-->show final state
            return 
        frame,unused_description=self._stack[transformation_index]
        if frame_index==0:
            self.UpdateAllDescription(transformation_index) #show description at the start of each step
        if frame_index<len(frame):
            #update current_frame for all animations to this frame index
            for animate in self.all_animations:
                if transformation_index<len(animate._stack):
                    animate_frame,_unused_description=animate._stack[transformation_index]
                    animate.current_frame=animate_frame[frame_index] #list of (x,y) tuples for this frame
            self.DrawFrame()
            #schedule next frame after self.speed milliseconds
            self._after_id=self.canvas.get_tk_widget().after(self.speed,self.PlayStack,transformation_index,frame_index+1)
        else:
            #all frames for this step done-->move to next transformation step
            self._after_id=self.canvas.get_tk_widget().after(self.speed,self.PlayStack,transformation_index+1,0)

    def DrawFrame(self):
        '''Clears the axes and redraws all animations at their current frame.
        Only the controller calls this-->ensures a single redraw per frame tick.
        Each animation's current_frame is a list of (x,y) tuples drawn as a segmented line.
        Parameters: 
        none
        Returns: 
        none'''
        if self!=self.all_animations[0]:
            return  #only the controller redraws
        self._ResetAxes()
        for animate in self.all_animations:
            if animate.current_frame is not None:
               DrawSegmentedLines(self.ax,animate.current_frame) # draw this animation's current (x,y) coordinates
        self.canvas.draw()
