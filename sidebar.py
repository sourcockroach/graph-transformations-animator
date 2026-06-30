from AdditionalFeatures import *
default_speed=42 #default animation speed
degrees_range=(-360,360) #default trig range for degrees
radians_range=(-2*math.pi,2*math.pi) #default trig range for radians

class Sidebar:
    '''Thee main sidebar UI component. Manages the equation input list, angle mode selection,
    animation speed and the View Transformation button.
    Satisfies objectives:
    2.1: equation input and processing via TypeEquation and ViewTransformation()
    2.1.5: radians/degrees switching via the angle mode dropdown
    2.2.3: animation speed slider
    2.5: undo/redo integration via self.undo_redo'''
    def __init__(self,parent,ax,canvas):
        self.equation_list=[]
        self.parent=parent
        self.ax=ax
        self.canvas=canvas
        self.undo_redo=None
        self.show_coords=True
        self.BuildScrollBar()
        self.BuildTopFrame()
        self.AddEquation()
        self.TransformationButton()
        self.BuildAnimationSpeed()
    
    def BuildScrollBar(self):
        self.scroll_canvas=Canvas(self.parent,width=320,height=500)
        self.sidebar_frame=Frame(self.scroll_canvas,width=320)
        self.scroll_canvas.grid(row=1,column=0,sticky='nsew')
        self.scrollbar=Scrollbar(self.parent,orient=VERTICAL,command=self.scroll_canvas.yview)
        self.scrollbar.grid(row=1,column=1,sticky='ns')
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scroll_canvas.create_window((0, 0), window=self.sidebar_frame, anchor="nw")
        self.sidebar_frame.bind("<Configure>",self.ConfigureFrame)

    def ConfigureFrame(self,event=None):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox('all'))

    def BuildTopFrame(self):
        self.top_frame=Frame(self.sidebar_frame,width=250)
        self.top_frame.grid(row=0,column=0,sticky='ew',padx=10,pady=5)
        self.BuildAngleMode()
        self.button=ttk.Button(self.top_frame,text='Enter New Equation',command=self.AddEquation)
        self.button.grid(row=1,column=0,sticky='ew',pady=5)

    def BuildAngleMode(self):
        '''Builds the angle mode dropdown.
        Satisfies objective 2.1.5: users can switch between radians and degrees for trig graphs.
        N/A is the default and is required for polynomial equations.'''
        angles=['N/A','Radians','Degrees']
        self.angle_var=StringVar(value='N/A')
        self.angle_dropdown=ttk.Combobox(self.top_frame,values=angles,textvariable=self.angle_var,state='readonly')
        self.angle_dropdown.grid(row=0,column=0,sticky='ew',pady=5)
    
    def GetAngleMode(self):
        return self.angle_var.get()

    def AddEquation(self):
        '''Adds a new TypeEquation row to the sidebar.
        Each row has its own entry box, description box and delete button.
        Satisfies objective 2.1: users can input equations, and 2.1.3: multiple equations can be added.'''
        type_equation=TypeEquation(self.sidebar_frame,len(self.equation_list)+1)
        delete_button=ttk.Button(type_equation.frame,text='x',command=lambda:self.DeleteButton(type_equation))
        delete_button.grid(row=0,column=1,padx=5)
        self.equation_list.append(type_equation)
        self.sidebar_frame.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox('all'))
        self.sidebar_frame.after(100, self.ConfigureFrame)

    def DeleteButton(self,row):
        self.equation_list.remove(row)
        row.frame.destroy()
    
    def PrepareAnimation(self,equation): 
        '''Processes a single equation and builds an Animation object ready to play.
        Sets the x range based on the angle mode
        Satisfies objective 2.2.3: animation with speed control.
        Parameters:
        equation (TypeEquation)-->the equation row to prepare
        Returns:
        Animation object configured for this equation'''
        equation.description_box.config(state=NORMAL)
        equation.description_box.delete('1.0',END)
        equation.description_box.config(state=DISABLED)
        engine=equation.Process()
        engine.EquationOrder()
        x_min,x_max=self.ax.get_xlim()
        angle_mode=self.GetAngleMode()
        if angle_mode=='Degrees':
            engine.graph.SetRange(*degrees_range)
        elif angle_mode=='Radians':
            engine.graph.SetRange(*radians_range)
        else:
            engine.graph.SetRange(x_min,x_max)
        base=engine.BaseEquation()
        base.SetRange(engine.graph.x_min,engine.graph.x_max)
        engine.start_coords=base.GetCoordinates()
        descriptions=engine.GetDescriptions()
        speed=int(self.speed_var.get())
        show_coords=getattr(self,'show_coords',False)
        return Animation(engine,self.ax,self.canvas,descriptions,equation.description_box,speed,show_coords,self)

    def _ShowEquationError(self,equation,message):
        equation.description_box.config(state=NORMAL)
        equation.description_box.delete('1.0',END)
        equation.description_box.insert(END,f'{message}\n')
        equation.description_box.config(state=DISABLED)

    def _ValidateAngleMode(self,engine,angle_mode,equation):
        '''Checks that the angle mode matches the graph type.
        Trig graphs require Degrees or Radians, polynomials require N/A.'''
        graph_type=engine.graph.graph_type
        if any(op in graph_type for op in trig_operators) and angle_mode=='N/A':
            self._ShowEquationError(equation,'ERROR: Select Degrees or Radians angle mode for trigonometric equations.')
            return False
        if graph_type!='sin' and graph_type!='cos' and graph_type!='tan' and angle_mode!='N/A':
            self._ShowEquationError(equation,'ERROR: Select N/A for polynomial equations.')
            return False
        return True

    def ViewTransformation(self,push=True,animate=True):
        import traceback 
        '''Facilitates the actions when 'View Transformation' is pressed.'''
        if push==True and self.undo_redo is not None:
            self.undo_redo.Push()
        angle_mode=self.GetAngleMode()
        x_min,x_max,y_min,y_max=ResetAxes(self.ax)
        animations=[]
        for equation in self.equation_list:
            try:
                engine=equation.Process()
                if engine is None:
                    continue
                if not self._ValidateAngleMode(engine,angle_mode,equation):
                    return 
                AngleMode.SetAngleMode(angle_mode)
                animations.append(self.PrepareAnimation(equation))
            except SyntaxError as e:
                self._ShowEquationError(equation, f'ERROR: {e}')
            except Exception as e:
                self._ShowEquationError(equation, f'Unexpected error: {e}')
                traceback.print_exc()
        for animation in animations:
            animation.all_animations=animations
            if animate==True:
                animation.Play()

    def TransformationButton(self):
        trans_button=ttk.Button(self.sidebar_frame,text='View Transformation',command=self.ViewTransformation)
        trans_button.grid(row=3,column=0,sticky='ew',padx=10,pady=5)
    
    def BuildAnimationSpeed(self):
        '''Builds variable slider for animation speed'''
        self.speed_label=Label(self.sidebar_frame,text='Adjust Animation speed')
        self.speed_label.grid(row=4,column=0,sticky='w',padx=10)
        self.speed_var=DoubleVar(value=default_speed)
        self.speed_slider=ttk.Scale(self.sidebar_frame,from_=200,to_=10,orient=HORIZONTAL,variable=self.speed_var)
        self.speed_slider.grid(row=5,column=0,sticky='ew',padx=10,pady=5)

class TypeEquation:
    def __init__(self,parent,row_len):
        self.frame=Frame(parent,width=320)
        self.frame.grid(row=row_len,column=0,sticky='ew',padx=10,pady=5)
        self.frame.grid_columnconfigure(0,weight=1)
        self.equation_entry=Entry(self.frame,width=32)
        self.equation_entry.grid(row=0,column=0,sticky='w',pady=3)
        self.BuildDescriptionBox()

    def Process(self):
        '''Reads the equation entry, runs it through EquationProcess and returns a TransformationEngine.'''
        self.equation=self.equation_entry.get()
        self.process=EquationProcess(self.equation)
        self.engine=self.process.EngineApplication()
        return self.engine

    def BuildDescriptionBox(self):
        '''Builds the area for the step-by-step descriptions.'''
        self.description_box=Text(self.frame,height=5,width=32,wrap='word',state=DISABLED)
        self.description_box.grid(row=1,column=0,columnspan=2,sticky='w',padx=2,pady=2)