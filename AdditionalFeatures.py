from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import ttk
from Animation import *
from EquationProcess import *
from SplitCoordinates import *

def ResetAxes(ax):
        ''' Clears the axes and redraws grid and axis lines while preserving the current range.
    Parameters:
    ax-->matplotlib axes to reset
    Returns:
    tuple of (x_min, x_max, y_min, y_max)'''
        x_min,x_max=ax.get_xlim() 
        y_min,y_max=ax.get_ylim()
        ax.cla() 
        ax.autoscale(False)
        ax.axvline(0,color='black')
        ax.axhline(0,color='black')
        ax.grid(True)
        ax.set_xlim(x_min,x_max)
        ax.set_ylim(y_min,y_max)
        return x_min,x_max,y_min,y_max

class RotationWindow:
    '''Window that lets the user apply a rotation to all currently graphed equations.
    Satisfies objective 2.3 — rotations applied externally to the currently graphed equations.
    Builds a Rotation transformation from user input and passes it to each equation's engine,
    then plays the animation sequence for all graphs simultaneously.'''
    def __init__(self,ax,canvas,sidebar):
        self.ax=ax
        self.canvas=canvas
        self.sidebar=sidebar
        self.window=Toplevel()
        self.window.geometry('300x180')
        self.window.title('Rotation')
        self.BuildEntryBoxes()
        self.BuildAngleApplication()

    def BuildEntryBoxes(self):
        '''Angle/centre entry'''
        angle_label=Label(self.window,text='Type Angle:')
        angle_label.grid(column=0,row=0,sticky='w',padx=10,pady=5)
        self.angle_entry=Entry(self.window,width=10)
        self.angle_entry.grid(column=1,row=0,pady=5)
        centrex_label=Label(self.window,text='Centre X:')
        centrex_label.grid(column=0,row=1,sticky='w',pady=5,padx=10)
        self.centrex_entry=Entry(self.window,width=5)
        self.centrex_entry.grid(column=1,row=1,sticky='w',padx=10,pady=5)
        centrey_label=Label(self.window,text='Centre Y:')
        centrey_label.grid(column=2,row=1,sticky='w',padx=10,pady=5)
        self.centrey_entry=Entry(self.window,width=5)
        self.centrey_entry.grid(column=3,row=1,sticky='w',padx=10,pady=5)
    
    def BuildAngleApplication(self):
        '''Buttons to facilitate the rotation'''
        clockwise_button=ttk.Button(self.window,text='Clockwise',command=lambda:self.Apply(clockwise=True),width=12)
        clockwise_button.grid(column=0,row=2,padx=10,pady=5,columnspan=2,sticky='ew')
        anticlockwise_button=ttk.Button(self.window,text='Anticlockwise',command=lambda:self.Apply(clockwise=False),width=12)
        anticlockwise_button.grid(column=2,row=2,padx=10,pady=5,columnspan=2,sticky='ew')
        self.BuildError()

    def BuildError(self):
        self.error_label=Label(self.window,text='Radians not supported with this feature',fg='red')
        self.error_label.grid(column=0,row=3,columnspan=4,padx=10)

    def _ValidateAngle(self):
        '''Validates the angle entry 
        Parameters: none
        Returns: 
        angle as float, or None if invalid
        Raises:
        ValueError: must be a numeric value.'''
        try:
            return float(self.angle_entry.get())
        except ValueError:
            self.error_label.config(text='Enter a float (decimal) or integer for the angle.')
            return None
        
    def _ValidateCentre(self):
        '''Validates the centre x and y entries (both must be numeric, defaults to 0.0 if empty).
        Parameters: 
        none
        Returns: 
        (cx, cy) tuple, or None if invalid'''
        cx=self.centrex_entry.get().strip()
        cy=self.centrey_entry.get().strip()
        try:
            c_x=float(cx) if cx else 0.0
            c_y=float(cy) if cy else 0.0
            return c_x,c_y
        except ValueError:
            self.error_label.config(text='Centre coordinates must both be floats (decimals) or integers.')
            return None
    
    def _BuildAnimations(self,rotation,speed,show_coords):
        '''Builds an Animation object for each equation in the sidebar with the rotation appended.
        The rotation is added directly to each engine's transformation list (this is what makes
        it external to the standard transformation pipeline (objective 2.3)).
        Parameters:
        rotation (Rotation)-->the rotation transformation to apply
        speed (int)-->animation frame delay in milliseconds
        show_coords (bool)-->whether to annotate key coordinates after animation
        Returns:
        list of Animation objects, one per valid equation'''
        animations=[]
        for equation in self.sidebar.equation_list:
            try:
                engine=equation.Process()
                if engine is None:
                    continue
                engine.EquationOrder()
                engine.transformations.append(rotation) #rotation appended after standard transformations
                descriptions=engine.GetDescriptions()
                equation.description_box.config(state=NORMAL)
                equation.description_box.delete('1.0',END)
                equation.description_box.config(state=DISABLED)
                animate=Animation(engine,self.ax,self.canvas,descriptions,equation.description_box,speed,show_coords,self.sidebar)
                animations.append(animate)
            except Exception as e:
                equation.description_box.config(state=NORMAL)
                equation.description_box.delete(1.0,END)
                equation.description_box.insert(END,f'Error:{e}\n')
                equation.description_box.config(state=DISABLED)
        return animations

    def Apply(self,clockwise): 
        '''Validates inputs, builds the Rotation transformation and plays the animation for all graphs.
        Pushes to undo stack before applying so the rotation can be undone (objective 2.5).
        Parameters: 
        clockwise (bool):True for clockwise, False for anticlockwise
        Returns: 
        none'''
        angle=self._ValidateAngle()
        if angle is None:
            return 
        centre=self._ValidateCentre()
        if centre is None:
            return       
        self.error_label.config(text='')
        if self.sidebar.undo_redo is not None and self.sidebar.equation_list!=[]:
            self.sidebar.undo_redo.Push() #save state before rotation so it can be undone
        x_min,x_max,y_min,y_max=ResetAxes(self.ax)
        self.ax.set_ylim(y_min,y_max)
        rotation=Rotation(angle,centre=centre,clockwise=clockwise)
        speed=int(self.sidebar.speed_var.get())
        show_coords=getattr(self.sidebar,'show_coords',False)
        animations=self._BuildAnimations(rotation,speed,show_coords)
        for animate in animations:
            animate.all_animations=animations #share the list so all animations are synchronised
            animate.Play()
    
class SideBySide:
    '''Window showing the original and transformed graphs side by side.
    Satisfies objective 2.4: a side-by-side view with both the base and final transformed graph.
    Both plots share the same axis limits as the main graph for consistent comparison.
    '''
    def __init__(self,sidebar,ax_main,show_coords=False):
        self.sidebar=sidebar
        self.ax_main=ax_main
        self.show_coords=show_coords
        self.window=Toplevel()
        self.window.geometry('900x500')
        self.window.title('Side-by-side View')
        self.fig=Figure(figsize=(9,5))
        self.BuildPlots()
        self.canvas=FigureCanvasTkAgg(self.fig,self.window)
        self.canvas.get_tk_widget().grid(row=0,column=0,sticky='nsew')
        self.Plot()

    def BuildPlots(self):
        '''Sets up both subplot axes with matching limits from the main graph.'''
        self.ax_base=self.fig.add_subplot(121)
        self.ax_transformed=self.fig.add_subplot(122)
        self.ax_base.set_title('Original')
        self.ax_transformed.set_title('Transformed')
        x_min,x_max=map(float,self.ax_main.get_xlim())
        y_min,y_max=map(float,self.ax_main.get_ylim())
        for ax in [self.ax_base,self.ax_transformed]:
            ax.axvline(0,color='black')
            ax.axhline(0,color='black')
            ax.grid(True)
            ax.set_xlim(x_min,x_max)
            ax.set_ylim(y_min,y_max)
            ax.autoscale(False)
    
    def _CollectEngines(self):
        '''Processes all sidebar equations and collects their base graphs, transformed graphs and engines.
        Parameters: 
        none
        Returns: 
        tuple of (original_graphs, transformed_graphs, engines) lists'''
        original_graphs=[]
        transformed_graphs=[]
        engines=[]
        for equation in self.sidebar.equation_list:
            engine=equation.Process()
            if engine is None:
                continue
            engine.EquationOrder()
            original_graphs.append(engine.BaseEquation())
            transformed_graphs.append(engine.graph)
            engines.append(engine)
        return original_graphs,transformed_graphs,engines
    
    def _PlotOriginal(self,engines,original_graphs,x_min,x_max,shared_plotted):
        '''Plots the base (untransformed) graph for each equation on the left axes.
        shared_plotted is passed through to prevent duplicate coordinate annotations.
        Parameters:
        engines (list)-->list of TransformationEngine objects
        original_graphs (list)-->list of base Graph objects
        x_min, x_max (float)-->axis range
        shared_plotted (list)-->shared list of already annotated coordinates'''
        for position,engine in enumerate(engines):
            base=engine.BaseEquation()
            base.SetRange(x_min,x_max)
            coords=base.GetCoordinates()
            engine.graph.SetRange(x_min,x_max)
            engine.graph.eval_coords=engine.graph.GetCoordinates()
            DrawSegmentedLines(self.ax_base,coords)
            if self.sidebar.show_coords==True:
                base_display=DisplayGraph(base)
                base_display.plotted=shared_plotted
                base_display.PlotCoords(self.ax_base,original_graphs,position,shared_plotted)
    
    def _PlotTransformed(self,engines,transformed_graphs):
        '''Plots the fully transformed graph for each equation on the right axes.
        Selects between rotated/trig and standard coordinate methods based on transformation type.
        Parameters:
        engines (list)-->list of TransformationEngine objects
        transformed_graphs (list)-->list of transformed Graph objects'''
        for position,engine in enumerate(engines):
            transformed_coords=engine.ApplyAll() #apply all transformations to get final coordinates
            x,y=SplitCoordinates(transformed_coords)
            self.ax_transformed.plot(x,y)
            has_rotation=False
            for transformation in engine.transformations:
                if isinstance(transformation,Rotation):
                    has_rotation=True
                    break
            temp_display=DisplayGraph(engine.graph)
            graph_type=engine.graph.graph_type
            if has_rotation==True or (graph_type=='sin' or graph_type=='cos' or graph_type=='tan'):
                #coordinates shown depends on graph type
                temp_display.PlotTrigRotCoordinates(self.ax_transformed,transformed_coords)
                temp_display.PlotIntersections(self.ax_transformed,transformed_graphs,position)
            else:
                temp_display.PlotCoords(self.ax_transformed, transformed_graphs, position)   

    def Plot(self): 
        '''Both the original and transformed graph is plotted.'''
        x_min,x_max=self.ax_base.get_xlim()
        shared_plotted=[]
        original_graphs,transformed_graphs,engines=self._CollectEngines()
        self._PlotOriginal(engines,original_graphs,x_min,x_max,shared_plotted)
        self._PlotTransformed(engines,transformed_graphs) 
        self.canvas.draw()
    
class RangeWindow:
    '''Window for updating the x and y axis range.
    Range changes are pushed to the undo stack so they can be undone (objective 2.5).'''
    def __init__(self,ax,canvas,sidebar):
        self.ax=ax
        self.canvas=canvas
        self.sidebar=sidebar
        self.window=Toplevel()
        self.window.geometry('300x180')
        self.window.title('Update range')
        self.DetectGraphType()
        self.BuildRangeInput()
        self.BuildApplyButton()
        
    def DetectGraphType(self):
        '''Checks whether any active equation is a trig graph-->used to adjust range behaviour.'''
        self.is_trig=False
        for equation in self.sidebar.equation_list:
            try:
                engine=equation.Process()
                if engine is None:
                    continue
                if engine.graph.graph_type=='sin' or engine.graph.graph_type=='cos' or engine.graph.graph_type=='tan':
                    self.is_trig=True
            except:
                continue

    def BuildRangeInput(self):
        Label(self.window,text='x min:').grid(row=0,column=0,padx=10,pady=5,sticky='w')
        Label(self.window,text='x max:').grid(row=1,column=0,padx=10,pady=5,sticky='w')
        Label(self.window,text='y min:').grid(row=0,column=3,padx=10,pady=5,sticky='w')
        Label(self.window,text='y max:').grid(row=1,column=3,padx=10,pady=5,sticky='w')
        self.x_min_entry=Entry(self.window,width=10)
        self.x_min_entry.grid(row=0,column=1,pady=5)
        self.x_max_entry=Entry(self.window,width=10)
        self.x_max_entry.grid(row=1,column=1,pady=5)
        self.y_min_entry=Entry(self.window,width=10)
        self.y_min_entry.grid(row=0,column=4,pady=5)
        self.y_max_entry=Entry(self.window,width=10)
        self.y_max_entry.grid(row=1,column=4,pady=5)
        self.error_label=Label(self.window,text='',fg='red')
        self.error_label.grid(row=3,column=0,columnspan=2,padx=10)

    def BuildApplyButton(self):
        range_button=ttk.Button(self.window,text='Apply Range',command=self.Apply)
        range_button.grid(row=4,column=0,columnspan=2,padx=10)

    def _ValidateRange(self):
        '''Validates all four range entries--.all must be numeric and max must exceed min.
        Parameters: 
        none
        Returns: 
        (x_min, x_max, y_min, y_max) tuple, or None if invalid
        '''
        x_max=self.x_max_entry.get()
        x_min=self.x_min_entry.get()
        y_min=self.y_min_entry.get()
        y_max=self.y_max_entry.get()
        try:
            y_min=float(y_min)
            y_max=float(y_max)
        except ValueError:
            self.error_label.config(text='y values should be a float (decimal number) or integer.')
            return None
        if y_min>=y_max or y_max<=y_min:
            self.error_label.config(text='y max should be greater than y min.')
            return None
        try:
            x_min=float(x_min)
            x_max=float(x_max)
        except ValueError:
                self.error_label.config(text='x values should be a float (decimal number) or integer.')
                return None
        return x_min,x_max,y_min,y_max
    
    def _UpdateGraphRanges(self,x_min,x_max):
        '''Updates the x range on every active graph object to match the new axis limits.'''
        for equation in self.sidebar.equation_list:
            try:
                engine=equation.Process()
                if engine is None:
                        continue
                engine.graph.SetRange(x_min,x_max)     
            except:
                continue

    def Apply(self): 
        '''Validates the range, pushes to undo stack then applies the new limits to the axes.
        Pushing with action='range' means Undo() knows to just redraw rather than replay transformations.
        Parameters: 
        none
        Returns:
        none'''
        graph_range=self._ValidateRange()
        if graph_range is None:
            return
        x_min,x_max,y_min,y_max=graph_range
        self.error_label.config(text='')
        if self.sidebar.undo_redo is not None:
            self.sidebar.undo_redo.Push(action='range')
        self._UpdateGraphRanges(x_min,x_max)
        self.ax.set_xlim(x_min,x_max)
        self.ax.set_ylim(y_min,y_max)
        self.canvas.draw()

class ShowCoordinates:
    '''Window for toggling coordinate annotations on and off.
    Updates sidebar.show_coords so all other parts of the program read the current setting.'''
    def __init__(self,ax,canvas,sidebar):
        self.ax=ax
        self.canvas=canvas
        self.sidebar=sidebar
        self.window=Toplevel()
        self.window.geometry('200x120')
        self.window.title('Show Coordinates')
        self.show_coords=True
        self.sidebar.show_coords=True
        self.BuildToggleButton()
    
    def BuildToggleButton(self):
        self.status_label=Label(self.window,text='Show Coordinates: on')
        self.status_label.grid(row=0,column=0,padx=20,pady=10,sticky='ew')
        self.toggle_button=ttk.Button(self.window,text='Hide Coordinates',command=self.ToggleCoords)
        self.toggle_button.grid(row=1,column=0,padx=20,pady=5,sticky='ew')

    def ToggleCoords(self):
        '''Flips the show_coords flag, updates sidebar and button text, then redraws.'''
        self.show_coords=not self.show_coords
        self.sidebar.show_coords=self.show_coords
        if self.show_coords==True:
            self.status_label.config(text='Show Coordinates: on')
            self.toggle_button.config(text='Hide coordinates')
        else:
            self.status_label.config(text='Show Coordinates: off')
            self.toggle_button.config(text='Show coordinates')
        self.Redraw()

    def _RedrawGraphs(self,x_min,x_max):
        '''Replots all graphs with or without coordinate annotations based on current show_coords state.
        Trig graphs use PlotTrigRotCoordinates since their key points must be found from
        the transformed coordinate list rather than Evaluate().
        Parameters:
        x_min, x_max (float)-->current axis range'''
        for equation in self.sidebar.equation_list:
            engine=equation.Process()
            if engine is None:
                continue
            engine.EquationOrder()  
            engine.graph.SetRange(x_min,x_max)
            display=DisplayGraph(engine.graph,toggle_coords=self.show_coords)
            display.Plot(self.ax)
            if self.show_coords==True:
                graph_type=engine.graph.graph_type
                if graph_type=='sin' or graph_type=='cos' or graph_type=='tan':
                    coords=engine.ApplyAll()
                    display.PlotTrigRotCoordinates(self.ax,coords) #trig uses coordinate-based annotation
                else:
                    display.PlotCoords(self.ax)

    def Redraw(self):
        '''Resets axes and redraws all graphs with the updated coordinate setting.'''
        x_min,x_max,y_min,y_max=ResetAxes(self.ax)
        self._RedrawGraphs(x_min,x_max)
        self.canvas.draw()