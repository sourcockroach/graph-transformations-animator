from AdditionalFeatures import *
class TopBar:
    '''How all the additional features is implimented into the UI'''
    def __init__(self,parent,ax,canvas,sidebar,undo_redo):
        self.undo_redo=undo_redo
        self.parent=parent
        self.ax=ax
        self.canvas=canvas
        self.sidebar=sidebar
        self.topbar_frame=Frame(parent,height=50,bd=2,relief='ridge',bg='black')
        self.topbar_frame.grid(row=0,column=0,columnspan=3,sticky='ew')
        self.topbar_frame.propagate(False)
        self.topbar_frame.grid_columnconfigure(3,weight=1)

        self.BuildButtons()
        self.BuildUndoRedo()
    
    def OpenRotations(self):
        RotationWindow(self.ax,self.canvas,self.sidebar)
    
    def OpenSideBySide(self):
        SideBySide(self.sidebar,self.ax,self.sidebar.show_coords)
    
    def OpenRange(self):
        RangeWindow(self.ax,self.canvas,self.sidebar)
    
    def OpenCoords(self):
        ShowCoordinates(self.ax,self.canvas,self.sidebar)

    def BuildButtons(self):    
        self.features_button=Menubutton(self.topbar_frame,text='Additional Features',bg='#00c4cc',fg='white',relief='flat')
        self.features_menu=Menu(self.features_button,tearoff=0)
        self.features_button.config(menu=self.features_menu)
        self.features_menu.add_command(label='Rotations',command=self.OpenRotations)
        self.features_menu.add_command(label='Side-by-side View',command=self.OpenSideBySide)
        self.features_menu.add_command(label='Update range',command=self.OpenRange)
        self.features_menu.add_command(label='Show Coordinates',command=self.OpenCoords)
        self.features_button.grid(row=0,column=4,padx=15,sticky='e')
    
    def BuildUndoRedo(self):
        undo_button=ttk.Button(self.topbar_frame,text='Undo',command=self.undo_redo.Undo)
        undo_button.grid(row=0,column=0,padx=(5,2),pady=5)
        redo_button=ttk.Button(self.topbar_frame,text='Redo',command=self.undo_redo.Redo)
        redo_button.grid(row=0,column=1,padx=(0,5),pady=5)