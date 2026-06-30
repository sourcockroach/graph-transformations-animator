def SplitCoordinates(coordinates):
    '''Splits a list of (x,y) tuples into two separate lists.
    Parameters: 
    coordinates (list)-->list of (x,y) tuples
    Returns: 
    tuple of (x_list, y_list)'''
    x=[]
    y=[]
    for i in range(len(coordinates)):
        x.append(coordinates[i][0])
    for i in range(len(coordinates)):
        y.append(coordinates[i][1])
    return x,y

def DrawSegmentedLines(ax,coords,colour=None):
    '''Plots a coordinate list as a segmented line, breaking at None y values.
    None y values represent discontinuities (without breaks the graph would draw
    a vertical line through asymptotes and gaps which is mathematically incorrect).
    The first segment's colour is captured and reused for all subsequent segments
    so the whole graph appears as one consistent colour.
    Parameters:
    ax-->matplotlib axes to draw on
    coords (list)-->list of (x,y) tuples with None y values at discontinuities
    colour-->optional colour override, auto-assigned from first segment if None
'''
    graph_part_x=[]
    graph_part_y=[]
    colour=None
    for coord in coords:
        if coord[1] is None:
            if graph_part_x:
                line=ax.plot(graph_part_x,graph_part_y)[0]
                if colour is None:
                    colour=line.get_color()
                else:
                    line.set_color(colour)
                graph_part_x=[]
                graph_part_y=[]
        else:
            graph_part_x.append(coord[0])
            graph_part_y.append(coord[1])
    if graph_part_x:
        ax.plot(graph_part_x,graph_part_y,color=colour)