from GraphClass import *
rotation_threshold=0.03  #maximum distance between two points to be considered an intersection after rotation
class GraphIntersections:
    '''Static methods for finding intersections between two graphs.
    Three separate methods are needed because polynomial, trig and rotated graphs
    each require different approaches-->polynomials can use Evaluate(), trig and rotated
    graphs must work directly from coordinate lists since they can't be evaluated algebraically.
    All methods return coordinates as lists of (x,y) tuples.'''
    @staticmethod
    def FindIntersections(graph_1,graph_2): 
        '''Finds intersections between two polynomial graphs using sign change detection.
        The difference between the two graphs' y values is checked at consecutive x points--> a sign change means
        the graphs crossed so BinarySearch() narrows down the exact x.
        Parameters:
        graph_1, graph_2 (Graph)-->the two graphs to find intersections between
        Returns:
        tuple of (is_intersection (bool), intersections (list of (x,y) tuples))'''
        is_intersection=False
        x=[]
        x_intersections=[]
        intersections=[]
        coordinates_1=graph_1.GetCoordinates()
        for i in range (len(coordinates_1)-1):
            x.append(coordinates_1[i][0]) #extract x values from graph_1's coordinates
        for i in range (len(x)-1):
            x1=x[i]
            x2=x[i+1]
            if (graph_1.Evaluate(x1)-graph_2.Evaluate(x1))*(graph_1.Evaluate(x2)-graph_2.Evaluate(x2))<0:
                #negative product means the difference changed sign (graphs crossed between x1 and x2)
                intersection=graph_1.BinarySearch(x1,x2)
                is_intersection=True
                x_intersections.append(intersection)
        if x_intersections:
            x_intersections=list(map(lambda coords: round(coords,1),x_intersections))
            y=map(lambda x_value:graph_1.Evaluate(x_value),x_intersections)
            y=list(map(lambda coords: round(coords,1),y))
            intersections=list(zip(x_intersections,y)) #pair x intersections with their y values
        return is_intersection,intersections
   
    @staticmethod
    def FindTrigIntersections(graph_coords_1,graph_coords_2):
        ''' Finds intersections between two trig graphs by working directly from coordinate lists.
        Trig graphs can't use Evaluate() based sign detection reliably due to discontinuities,
        so the difference between the two graphs' y values at each point is checked instead.
        Linear interpolation finds the precise crossing point within each interval.
        Parameters:
        graph_coords_1, graph_coords_2 (list)-->coordinate lists of (x,y) tuples for each graph
        Returns: 
        tuple of (has_intersections (bool), intersections (list of (x,y) tuples))'''
        graph_intersections=[]
        has_intersections=False
        for i in range(len(graph_coords_1)-1):
            graph1_x1,graph1_y1=graph_coords_1[i]
            graph1_x2,graph1_y2=graph_coords_1[i+1]
            graph2_x1,graph2_y1=graph_coords_2[i]
            graph2_x2,graph2_y2=graph_coords_2[i+1]
            difference1=graph1_y1-graph2_y1 #y gap between graphs at first point
            difference2=graph1_y2-graph2_y2 #y gap between graphs at second point
            if (difference1)*(difference2)<0:
                t=-difference1/(difference2-difference1)
                x=graph1_x1+t*(graph1_x2-graph1_x1) #interpolated x of crossing
                y=graph1_y1+t*(graph1_y2-graph1_y1) #interpolated y of crossing
                rounded_x=float(round(x,2))
                rounded_y=float(round(y,2))
                graph_intersections.append((rounded_x,rounded_y))
        if graph_intersections!=[]:
            has_intersections=True
        return has_intersections,graph_intersections
    @staticmethod
    def FindRotatedIntersections(coords_1,coords_2,threshold=rotation_threshold):
        ''' Finds intersections between two rotated graphs by checking proximity between coordinate points.
        After rotation, graphs no longer share x values so Evaluate() based methods don't work-->instead,
        every point in coords_1 is compared against every point in coords_2 and points
        within rotation_threshold distance are treated as intersections.
        Parameters:
        coords_1, coords_2 (list)-->coordinate lists of (x,y) tuples for each rotated graph
        threshold (float)-->maximum distance to count as an intersection
        Returns: 
        tuple of (has_intersections (bool), intersections (list of (x,y) tuples))'''
        intersections=[]
        has_intersections=False
        for coord1 in coords_1:
                x1,y1=coord1[0],coord1[1]
                for coord2 in coords_2:
                    x2,y2=coord2[0],coord2[1]
                    distance=((x1-x2)**2+(y1-y2)**2)**0.5 #distance formula applied between the two points
                if distance < threshold:
                    if distance<threshold:
                        rounded_x=(round(x1,2))
                        rounded_y=(round(y1,2))
                        rounded=((rounded_x,rounded_y))
                        if rounded not in intersections:  #only add if not already recorded-->avoids duplicates
                            intersections.append(rounded)
                        break #found a match for this coord1 point — no need to check remaining coord2 points
        if intersections!=[]:
            has_intersections=True
        return has_intersections,intersections