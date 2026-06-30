from tkinter import *
from EquationProcess import *
from Animation import *
from sidebar import *
from topbar import *
from UndoStack import *
from AdditionalFeatures import *

class GraphApp: 
    '''Builds the app-->sets the UI up'''
    def __init__(self):
        self.window=Tk()
        self.window.geometry('1000x700')
        self.window.title('Graph Transformations')
        self.fig=Figure(figsize=(8,7))
        self.plot_canvas=FigureCanvasTkAgg(self.fig,self.window)
        self.plot_canvas.get_tk_widget().grid(row=1,column=2,sticky='nsew',rowspan=2,padx=10,pady=10)
        self.ax=self.fig.add_subplot(111)
        self.ax.autoscale(False)
        self.sidebar=Sidebar(self.window,self.ax,self.plot_canvas)
        self.undo_redo=UndoRedo(self.sidebar,self.ax,self.plot_canvas)
        self.sidebar.undo_redo=self.undo_redo
        self.topbar=TopBar(self.window,self.ax,self.plot_canvas,self.sidebar,self.undo_redo)
        self.window.mainloop()
app=GraphApp()#instantiates the class--> creates the app