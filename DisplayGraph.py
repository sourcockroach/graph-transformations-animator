from Intersections import *
from SplitCoordinates import *
plot_tolerance=0.3  #minimum distance between two plotted points before a new annotation is suppressed
class DisplayGraph:
    '''Handles plotting and coordinate annotation for a single graph on the axes.
    Tracks which coordinates have already been annotated via the plotted list,
    shared across multiple DisplayGraph instances to prevent duplicate annotations
    when multiple graphs are displayed simultaneously.
    Provides separate methods for standard polynomials, trig graphs and rotated graphs
    since each requires different approaches to find key coordinates.
'''
    def __init__(self,graph,toggle_coords=False):
        '''Parameters:
        graph (Graph)-->the graph object whose coordinates will be plotted
        toggle_coords (bool)-->whether coordinate annotations are currently enabled'''
        self.graph=graph
        self.toggle_coords=toggle_coords
        self.visible=True
        self.colour=None #if None, matplotlib assigns a colour automatically
        self.plotted=[] #list of (x,y) tuples already annotated-->prevents duplicates

    def _AlreadyPlotted(self,rounded,tolerance=plot_tolerance):
        '''Checks whether a coordinate is too close to one already annotated.
        Prevents overlapping annotations when key points are very close together.
        Parameters:
        rounded (tuple)-->(x,y) coordinate to check
        tolerance (float)-->maximum distance to an existing point before suppressing
        Returns:
        True if a sufficiently close point has already been plotted'''
        for plotted in self.plotted:
            if abs(plotted[0]-rounded[0])<tolerance and abs(plotted[1]-rounded[1])<tolerance:
                return True
        return False
    
    def Plot(self,ax):
        '''Draws the graph as a segmented line on the axes.
        None y values in the coordinate list cause line breaks — preserving discontinuities.
        Parameters: 
        ax-->matplotlib axes to draw on
        Returns: 
        none'''
        if not self.visible:
            return
        coordinates=self.graph.GetCoordinates()
        DrawSegmentedLines(ax,coordinates,colour=self.colour)
  
    def PlotCoords(self,ax,graph_list=None,current_graph=None,plotted=None):
        '''Annotates key coordinates for a standard polynomial graph-->roots, turning points,
        y intercept and intersections with other graphs.
        plotted is passed in from outside so it can be shared across multiple graphs,
        this prevents the same point being annotated twice when two graphs share a coordinate.
        Parameters:
        ax-->matplotlib axes to annotate on
        graph_list (list)-->list of all graph objects, used for intersection detection
        current_graph (int)-->index of this graph in graph_list
        plotted (list)-->shared list of already annotated (x,y) tuples
        Returns: 
        updated plotted list'''
        if plotted is None:
            plotted=[]
        self.plotted=plotted
        is_root,roots=self.graph.FindXIntercepts()
        turning_points=self.graph.FindTurningPoints()
        y_intercept=self.graph.FindYIntercept()
        if is_root:
            for coord in roots: #plots x intercepts
                if not self._AlreadyPlotted(coord):
                    self.plotted.append(coord)
                    ax.scatter(coord[0],coord[1])
                    ax.annotate(f'({round(coord[0],2)}, {round(coord[1],2)})', 
                    xy=coord, textcoords='offset points', xytext=(5, 5))
        if turning_points: #plots turning points
            for coord in turning_points:
                if not self._AlreadyPlotted(coord):
                    self.plotted.append(coord)
                    ax.scatter(coord[0],coord[1])
                    ax.annotate(f'({round(coord[0],2)}, {round(coord[1],2)})', 
                    xy=coord, textcoords='offset points', xytext=(5, 5))
        if y_intercept is not None: #plots y intercepts
            y_value=(0,y_intercept)
            if not self._AlreadyPlotted(y_value):
                ax.scatter(0,y_intercept)
                ax.annotate(f'(0,{round(y_intercept,2)})', 
                xy=(0,y_intercept), textcoords='offset points', xytext=(5, 5))
        
        self.PlotIntersections(ax,graph_list,current_graph) #plots intrsections
        return self.plotted

    def PlotTrigIntersections(self,ax,graph_list,current_graph):
        '''Annotates intersections between trig graphs using coordinate list comparison.
        Only checks graphs after current_graph in the list-->avoids finding the same
        intersection twice from both sides.
        Parameters:
        ax-->matplotlib axes to annotate on
        graph_list (list)-->list of all graph objects
        current_graph (int)-->index of this graph in graph_list'''
        if graph_list is not None and current_graph is not None and len(graph_list)>=2:
            for graph in range(current_graph+1,len(graph_list)):
                if graph_list[current_graph].eval_coords is None or graph_list[graph].eval_coords is None:
                    continue #skip if either graph has no evaluated coordinates
                coords_current=graph_list[current_graph].eval_coords
                coords_other=graph_list[graph].eval_coords
                has_intersections,intersections=GraphIntersections.FindTrigIntersections(coords_current,coords_other)
                if has_intersections and intersections:
                    for points in intersections:
                        rounded=(float(round(points[0],2)),float(round(points[1],2)))
                        if not self._AlreadyPlotted(rounded):  #suppress if too close to existing annotation
                            self.plotted.append(rounded)
                            ax.scatter(points[0],points[1])
                            ax.annotate(f'({rounded[0]},{rounded[1]})',xy=points, textcoords='offset points', xytext=(5, 5)) 
                        
                               
    def PlotIntersections(self,ax,graph_list,current_graph):
        '''Annotates intersections between standard polynomial graphs.
        Only checks graphs after current_graph to avoid finding intersections twice.
        Parameters:
        ax-->matplotlib axes to annotate on
        graph_list (list)-->list of all graph objects
        current_graph (int)-->index of this graph in graph_list'''
        if graph_list is not None and current_graph is not None and len(graph_list)>=2:
            for graph in range(current_graph+1,len(graph_list)):
                other_graph=graph_list[graph]
                has_intersections,intersections=GraphIntersections.FindIntersections(self.graph,other_graph)
                if has_intersections and intersections:
                    for points in intersections:
                        rounded=(float(round(points[0],2)),float(round(points[1],2)))
                        if not self._AlreadyPlotted(rounded):
                            self.plotted.append(rounded)
                            ax.scatter(points[0],points[1]) #plots the intersection points at once
                            ax.annotate(f'({round(points[0],2)},{round(points[1],2)})',xy=points,textcoords='offset points',xytext=(5,5))
                   
                    
                  
        
    def _TrigRotXIntercepts(self,ax,coordinates):
        '''Finds and annotates x intercepts on a rotated graph using sign change detection.
        Standard FindXIntercepts() can't be used after rotation since the graph object's
        Evaluate() no longer reflects the rotated position-->must work from the coordinate list directly.
        Linear interpolation finds the precise crossing point between consecutive y values.
        Parameters:
        ax-->matplotlib axes to annotate on
        coordinates (list)-->list of (x,y) tuples of the rotated graph'''
        for i in range(len(coordinates)-1):
            x1,y1=coordinates[i]
            x2,y2=coordinates[i+1]
            if y1 is None or y2 is None or x1 is None or x2 is None:
                continue  #skip discontinuities
            if y1*y2<0:
                #sign change means the graph crossed y=0 between these two points
                t=-y1/(y2-y1) #linear interpolation parameter
                x=x1+t*(x2-x1) #interpolated x at y=0
                rounded_x=float(round(x,2))
                if not self._AlreadyPlotted((rounded_x,0.0)):
                    self.plotted.append((rounded_x,0.0))
                    ax.scatter(x,0,color='dodgerblue')
                    ax.annotate(f'{round(x,2)},0',xy=(x,0))

    def _TrigRotYIntercepts(self,ax,coordinates):
        ''' Finds and annotates y intercepts on a rotated graph using sign change detection on x values.
        Same reasoning as RotatedXIntercepts, Evaluate() can't be used after rotation.
        Detects where x changes sign (graph crosses x=0) and interpolates the y value there.
        Handles the edge case where a point is already essentially on the y axis (abs(x1) < 0.05).
        Parameters:
        ax-->matplotlib axes to annotate on
        coordinates (list)-->list of (x,y) tuples of the rotated graph'''
        for i in range(len(coordinates)-1):
            x1,y1=coordinates[i]
            x2,y2=coordinates[i+1]
            if x1 is None or x2 is None:
                continue #skip discontinuities
            if x1*x2<=0:
                #sign change in x means the graph crossed x=0 (y intercept is here).
                if y1 is None or y2 is None:
                    continue
                if (x2-x1)!=0:
                    t=-x1/(x2-x1) #interpolation parameter for where x=0
                    y=y1+t*(y2-y1) #interpolated y at x=0
                    rounded_y=float(round(y,2))
                    if not self._AlreadyPlotted((0.0,rounded_y)):
                        self.plotted.append((0.0,rounded_y))
                        ax.scatter(0,y,color='orange')
                        ax.annotate(f'(0,{round(y,2)})',xy=(0,y))
                elif abs(x1)<0.05:
                    #x1 is very close to 0: treat this point directly as the y intercept
                    rounded_y=float(round(y1,2))
                    if not self._AlreadyPlotted((0.0,rounded_y)):
                        ax.scatter(0,y,color='orange')
                        ax.annotate(f'(0,{round(y1,2)})',xy=(0,y1))

    def _TrigRotTP(self,ax,coordinates): 
        '''Finds and annotates turning points on a rotated graph by checking y value patterns.
        Standard FindTurningPoints() can't be used after rotation.
        A turning point occurs when the current y is greater or less than both its neighbours,
        checks both strict and non-strict inequalities to catch turning points.
        Parameters:
        ax-->matplotlib axes to annotate on
        coordinates (list)-->list of (x,y) tuples of the rotated graph'''
        for i in range(1,len(coordinates)-1):
            y_previous=coordinates[i-1][1]
            y_current=coordinates[i][1]
            y_next=coordinates[i+1][1]
            rounded_x=float(round(coordinates[i][0],2))
            if coordinates[i][1] is not None:
                rounded_y=float(round(coordinates[i][1],2))
            rounded_coords=(rounded_x,rounded_y)
            if y_previous is None or y_current is None or y_next is None:
                continue
            #check all combinations of strict/non-strict inequality to find turning points
            if (y_current>=y_previous and y_current>y_next) or (y_current>y_previous and y_current>=y_next) or (y_current<=y_previous and y_current<y_next) or (y_current<y_previous and y_current<=y_next):
                if not self._AlreadyPlotted(rounded_coords):
                    self.plotted.append(rounded_coords)
                    ax.scatter(coordinates[i][0],coordinates[i][1],color='red')
                    ax.annotate(f'({round(coordinates[i][0],2)},{round(coordinates[i][1],2)})',xy=coordinates[i]) #rounding to avoid floating point error/
    
    def PlotRotatedIntersections(self,ax,graph_list,current_graph):
        '''Annotates intersections between rotated graphs using proximity-based detection.
        Standard intersection methods can't be used after rotation since graphs no longer
        share x values, FindRotatedIntersections() checks distance between coordinate points instead.
        Only checks graphs after current_graph to avoid finding the same intersection twice.
        Parameters:
        ax-->matplotlib axes to annotate on
        graph_list (list)-->list of all graph objects
        current_graph (int)-->index of this graph in graph_list'''
        if graph_list is not None and current_graph is not None and len(graph_list)>=2:
            for graph in range(current_graph+1,len(graph_list)):
                if graph_list[current_graph].eval_coords is None or graph_list[graph].eval_coords is None:
                    continue #skip if either graph has no evaluated coordinates
                coords_current=graph_list[current_graph].eval_coords
                coords_other=graph_list[graph].eval_coords
                has_intersections,intersections=GraphIntersections.FindRotatedIntersections(coords_current,coords_other)
                if has_intersections and intersections:
                    for points in intersections:
                        rounded=(float(round(points[0],2)),float(round(points[1],2)))
                        if not self._AlreadyPlotted(rounded):
                            self.plotted.append(rounded) #if not already plotted, added to the already plotted list (ensures that there's no duplicates).
                            ax.scatter(points[0],points[1])
                            ax.annotate(f'({rounded[0]},{rounded[1]})',xy=points, textcoords='offset points', xytext=(5, 5)) 
                

    def PlotTrigRotCoordinates(self,ax,coordinates):
        ''' Annotates all key coordinates for a rotated graph: x intercepts, y intercepts and turning points.
        uses the three Rotated methods since standard coordinate methods don't work after rotation (no longer a regular graph object).
        Parameters:
        ax-->matplotlib axes to annotate on
        coordinates (list)-->list of (x,y) tuples of the rotated grap'''
        if not coordinates:
            return
        self._TrigRotXIntercepts(ax,coordinates)
        self._TrigRotYIntercepts(ax,coordinates)
        self._TrigRotTP(ax,coordinates)
