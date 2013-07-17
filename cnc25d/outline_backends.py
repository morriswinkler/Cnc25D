# outline_backends.py
# common interface to create lines, arcs and circles for the backends freecad, dxfwrite, svgwrite and Tkinter
# created by charlyoleg on 2013/06/21
# license: CC BY SA 3.0

"""
outline_backends.py provides a common API to create lines, arcs and circles with freecad, dxfwrite, svgwrite and Tkinter (via display_backend.py)
"""

################################################################
# python behavior
################################################################

from __future__ import division # to get float division


################################################################
# header for Python / FreeCAD compatibility
################################################################

import importing_freecad
importing_freecad.importing_freecad()

#print("FreeCAD.Version:", FreeCAD.Version())
#FreeCAD.Console.PrintMessage("Hello from PrintMessage!\n") # avoid using this method because it is not printed in the FreeCAD GUI


################################################################
# import
################################################################

import Part
from FreeCAD import Base
import math
import sys, argparse
import svgwrite
from dxfwrite import DXFEngine
import Tkinter
import display_backend


################################################################
# global variable
################################################################

unit_circle_resolution = 6
#default_dxf_layer_name = 'CNC25D'

################################################################
# ******** sub-functions for the API ***********
################################################################

def complete_circle(ai_center, ai_radius, ai_resolution):
  """ Generate a list of points that creates a circle with the resolution ai_resolution.
      ai_resolution sets the mamximum number of intermediate points to create
  """
  r_points = []
  # calculation of the angle resolution:
  if(ai_resolution<3):
    print("ERR821: The ai_resolution is smaller than 3. Current ai_resolution = {:d}".format(ai_resolution))
    sys.exit(2)
  #print("dbg424: ai_radius:", ai_radius)
  circle_resolution = int(ai_resolution * ai_radius) # circle resolution increase with the radius
  angle_resolution = 2*math.pi/circle_resolution
  # create the list of points
  for i in range(circle_resolution):
    r_points.append([ai_center[0]+ai_radius*math.cos(i*angle_resolution), ai_center[1]+ai_radius*math.sin(i*angle_resolution)])
  return(r_points)

def arc_of_circle(ai_start, ai_middle, ai_end, ai_resolution):
  """ From three points (list of 6 floats) creates a polyline (list of 2*n flaots) representing the arc of circle defined by the three points
      ai_resolution sets the mamximum number of intermediate points to create
  """
  # interpretation of the three points
  ptax = ai_start[0]
  ptay = ai_start[1]
  ptbx = ai_middle[0]
  ptby = ai_middle[1]
  ptcx = ai_end[0]
  ptcy = ai_end[1]
  #print("dbg501: pta: {:6.01f}  {:6.01f}".format(ptax, ptay))
  #print("dbg502: ptb: {:6.01f}  {:6.01f}".format(ptbx, ptby))
  #print("dbg503: ptc: {:6.01f}  {:6.01f}".format(ptcx, ptcy))
  # epsilon definiton to be tolerant to calculation imprecision
  epilon = math.pi/1000 # can be used to compare radian and sine
  #print("dbg747: epilon:", epilon)
  # check
  if((ptax==ptbx)and(ptay==ptby)):
    print("ERR807: Error, point_A and point_B are identical!")
    sys.exit(2)
  if((ptbx==ptcx)and(ptby==ptcy)):
    print("ERR808: Error, point_B and point_C are identical!")
    sys.exit(2)
  if((ptax==ptcx)and(ptay==ptcy)):
    print("ERR809: Error, point_A and point_C are identical!")
    sys.exit(2)
  ## check the documentation for the explanation of the following calculation
  # length of [AB] and [BC]
  lab = math.sqrt((ptbx-ptax)**2+(ptby-ptay)**2)
  lbc = math.sqrt((ptcx-ptbx)**2+(ptcy-ptby)**2)
  if(lab<epilon):
    print("ERR811: Error, A and B are almost identical")
    sys.exit(2)
  if(lbc<epilon):
    print("ERR812: Error, B and C are almost identical")
    sys.exit(2)
  # calculation of cos(e), cos(f), sin(e) and sin(f)
  cos_e = (ptbx-ptax)/lab
  cos_f = (ptcx-ptbx)/lbc
  sin_e = (ptby-ptay)/lab
  sin_f = (ptcy-ptby)/lbc
  #print("dbg304: cos_e: ", cos_e)
  #print("dbg305: sin_e: ", sin_e)
  #print("dbg306: cos_f: ", cos_f)
  #print("dbg307: sin_f: ", sin_f)
  if(abs((math.copysign(1, sin_e)*cos_e)-(math.copysign(1,sin_f)*cos_f))<epilon):
    print("ERR810: Error, A, B, C are colinear. Arc can not be created!")
    sys.exit(2)
  # Calculation of M and N
  ptmx = (ptax+ptbx)/2
  ptmy = (ptay+ptby)/2
  ptnx = (ptbx+ptcx)/2
  ptny = (ptby+ptcy)/2
  #print("dbg134: ptmx:", ptmx)
  #print("dbg135: ptmy:", ptmy)
  #print("dbg136: ptnx:", ptnx)
  #print("dbg137: ptny:", ptny)
  # calculation of I
  lix = cos_e*sin_f-cos_f*sin_e
  kix = sin_f*(cos_e*ptmx+sin_e*ptmy)-sin_e*(cos_f*ptnx+sin_f*ptny)
  liy = sin_e*cos_f-sin_f*cos_e
  kiy = cos_f*(cos_e*ptmx+sin_e*ptmy)-cos_e*(cos_f*ptnx+sin_f*ptny)
  if(abs(lix)<epilon):
    print("ERR813: Error, A, B and C are almost colinear. Arc can not be created!")
    sys.exit(2)
  if(abs(liy)<epilon):
    print("ERR814: Error, A, B and C are almost colinear. Arc can not be created!")
    sys.exit(2)
  #print("dbg124: lix:", lix)
  #print("dbg125: kix:", kix)
  #print("dbg126: liy:", liy)
  #print("dbg127: kiy:", kiy)
  ptix = kix / lix
  ptiy = kiy / liy
  #print("dbg505: pti: {:6.02f}  {:6.02f}".format(ptix, ptiy))
  # length of [IA], [IB] and [IC]
  lia = math.sqrt((ptax-ptix)**2+(ptay-ptiy)**2)
  lib = math.sqrt((ptbx-ptix)**2+(ptby-ptiy)**2)
  lic = math.sqrt((ptcx-ptix)**2+(ptcy-ptiy)**2)
  if(abs(lib-lia)>epilon):
    #print("dbg404: lia:", lia)
    #print("dbg405: lib:", lib)
    print("ERR815: I is not equidistant from A and B!")
    sys.exit(2)
  if(abs(lic-lib)>epilon):
    #print("dbg402: lib:", lib)
    #print("dbg403: lic:", lic)
    print("ERR816: I is not equidistant from B and C!")
    sys.exit(2)
  # calculation of the angle u=(Ix, IA) , v=(Ix, IB) and w=(Ix, IC)
  u = math.atan2(ptay-ptiy, ptax-ptix)
  v = math.atan2(ptby-ptiy, ptbx-ptix)
  w = math.atan2(ptcy-ptiy, ptcx-ptix)
  # calculation of the angle uv=(IA, IB), uw=(IA, IC) vw=(IB, IC)
  uv = math.fmod(v-u+4*math.pi, 2*math.pi)
  uw = math.fmod(w-u+4*math.pi, 2*math.pi)
  vw = math.fmod(w-v+4*math.pi, 2*math.pi)
  # check arc direction
  ccw_ncw = 1
  if(uw>uv):
    #print("dbg874: arc of circle direction: counter clock wise (CCW)")
    ccw_ncw = 1
  else:
    #print("dbg875: arc of circle direction: clock wise (CW)")
    ccw_ncw = 0
    uv = uv - 2*math.pi
    vw = vw - 2*math.pi
  # calculation of the angle resolution:
  if(ai_resolution<3):
    print("ERR821: The ai_resolution is smaller than 3. Current ai_resolution = {:d}".format(ai_resolution))
    sys.exit(2)
  #print("dbg414: arc radius: lia:", lia)
  circle_resolution = ai_resolution * lia # angle resolution increase with the radius
  ar = 2*math.pi/circle_resolution
  # number of intermediate point between A and B and step angle
  abip = int(abs(uv)/ar)
  absa = uv/(abip+1)
  #print("dbg741: uv angle resolution: absa:", absa)
  # number of intermediate point between B and C and step angle
  bcip = int(abs(vw)/ar)
  bcsa = vw/(bcip+1)
  #print("dbg742: vw angle resolution: bcsa:", bcsa)
  # polyline construction
  r_polyline = []
  r_polyline.append([ptax, ptay])
  for i in range(abip):
    r_polyline.append([ptix+lia*math.cos(u+(i+1)*absa), ptiy+lia*math.sin(u+(i+1)*absa)])
  r_polyline.append([ptbx, ptby])
  for i in range(bcip):
    r_polyline.append([ptix+lia*math.cos(v+(i+1)*bcsa), ptiy+lia*math.sin(v+(i+1)*bcsa)])
  r_polyline.append([ptcx, ptcy])
  return(r_polyline)

def outline_arc_line_with_freecad(ai_segments, ai_outline_closed):
  """ Generates the arcs and lines outline with the FreeCAD Part API
  """
  constant_z = 0 # FreeCAD.Part works in 3D. So we fix z=0 and just use the XY surface
  fc_vectors = [Base.Vector(ai_segments[0][0], ai_segments[0][1], constant_z)]
  segment_nb = len(ai_segments)-1
  fc_outline = []
  for i in range(segment_nb):
    segment_type = 'line'
    fc_vectors.append(Base.Vector(ai_segments[i+1][0], ai_segments[i+1][1], constant_z))
    point_start = fc_vectors[-2]
    point_end = fc_vectors[-1]
    if(len(ai_segments[i+1])==4):
      segment_type = 'arc'
      fc_vectors.append(Base.Vector(ai_segments[i+1][2], ai_segments[i+1][3], constant_z))
      point_start = fc_vectors[-3]
      point_mid = fc_vectors[-2]
      point_end = fc_vectors[-1]
    if(i==segment_nb-1):
      #print("dbg306: last segment")
      if(ai_outline_closed):
        #print("dbg307: close")
        point_end = fc_vectors[0]
    #print("dbg563: i: {:d}  segment: {:s}".format(i, segment_type))
    if(segment_type=='line'):
      fc_outline.append(Part.Line(point_start, point_end))
    elif(segment_type=='arc'):
      fc_outline.append(Part.Arc(point_start, point_mid, point_end))
  r_outline = Part.Shape(fc_outline)
  return(r_outline)

def outline_arc_line_with_svgwrite(ai_segments, ai_outline_closed):
  """ Generates the arcs and lines outline with the mozman svgwrite
  """
  svg_points = [tuple((ai_segments[0][0], ai_segments[0][1]))]
  segment_nb = len(ai_segments)-1
  svg_outline = []
  for i in range(segment_nb):
    segment_type = 'line'
    svg_points.append(tuple((ai_segments[i+1][0], ai_segments[i+1][1])))
    point_start = svg_points[-2]
    point_end = svg_points[-1]
    if(len(ai_segments[i+1])==4):
      segment_type = 'arc'
      svg_points.append(tuple((ai_segments[i+1][2], ai_segments[i+1][3])))
      point_start = svg_points[-3]
      point_mid = svg_points[-2]
      point_end = svg_points[-1]
    if(i==segment_nb-1):
      #print("dbg306: last segment")
      if(ai_outline_closed):
        #print("dbg307: close")
        point_end = svg_points[0]
    #print("dbg563: i: {:d}  segment: {:s}".format(i, segment_type))
    if(segment_type=='line'):
      svg_line = svgwrite.shapes.Line(start=point_start, end=point_end)
      svg_line.fill('green', opacity=0.25).stroke('black', width=1)
      #svg_line.fill('green', opacity=0.0).stroke('black', width=1)  # opacity=0.0 doesn't work!
      #svg_line.stroke('black', width=1)
      svg_outline.append(svg_line)
    elif(segment_type=='arc'):
      arc_polyline = arc_of_circle(point_start, point_mid, point_end, unit_circle_resolution)
      arc_polyline_svg = []
      for i in arc_polyline:
        arc_polyline_svg.append(tuple(i))
      svg_polyline = svgwrite.shapes.Polyline(arc_polyline_svg)
      svg_polyline.fill('green', opacity=0.25).stroke('black', width=1)
      #svg_polyline.fill('green', opacity=0.0).stroke('black', width=1)   # opacity=0.0 doesn't work!
      #svg_polyline.stroke('black', width=1)
      svg_outline.append(svg_polyline)
  r_outline = svg_outline
  return(r_outline)

def outline_arc_line_with_dxfwrite(ai_segments, ai_outline_closed):
  """ Generates the arcs and lines outline with the mozman dxfwrite
  """
  dxf_points = [tuple((ai_segments[0][0], ai_segments[0][1]))]
  segment_nb = len(ai_segments)-1
  dxf_outline = []
  for i in range(segment_nb):
    segment_type = 'line'
    dxf_points.append(tuple((ai_segments[i+1][0], ai_segments[i+1][1])))
    point_start = dxf_points[-2]
    point_end = dxf_points[-1]
    if(len(ai_segments[i+1])==4):
      segment_type = 'arc'
      dxf_points.append(tuple((ai_segments[i+1][2], ai_segments[i+1][3])))
      point_start = dxf_points[-3]
      point_mid = dxf_points[-2]
      point_end = dxf_points[-1]
    if(i==segment_nb-1):
      #print("dbg306: last segment")
      if(ai_outline_closed):
        #print("dbg307: close")
        point_end = dxf_points[0]
    #print("dbg563: i: {:d}  segment: {:s}".format(i, segment_type))
    if(segment_type=='line'):
      #dxf_line = DXFEngine.line(start=point_start, end=point_end, color=7, layer=default_dxf_layer_name)
      dxf_line = DXFEngine.line(start=point_start, end=point_end)
      dxf_outline.append(dxf_line)
    elif(segment_type=='arc'):
      arc_polyline = arc_of_circle(point_start, point_mid, point_end, unit_circle_resolution)
      arc_polyline_dxf = []
      for i in arc_polyline:
        arc_polyline_dxf.append(tuple(i))
      #dxf_polyline = DXFEngine.polyline(arc_polyline_dxf, color=7, layer=default_dxf_layer_name)
      #dxf_polyline = DXFEngine.polyline(arc_polyline_dxf, flags=DXFEngine.POLYLINE_3D_POLYLINE)
      dxf_polyline = DXFEngine.polyline(arc_polyline_dxf)
      dxf_outline.append(dxf_polyline)
  r_outline = dxf_outline
  return(r_outline)

def outline_arc_line_with_tkinter(ai_segments, ai_outline_closed):
  """ Transform the arcs and lines outlines into tkinter lines
  """
  tkline_points = [tuple((ai_segments[0][0], ai_segments[0][1]))]
  segment_nb = len(ai_segments)-1
  tkline_outline = []
  for i in range(segment_nb):
    segment_type = 'line'
    tkline_points.append(tuple((ai_segments[i+1][0], ai_segments[i+1][1])))
    point_start = tkline_points[-2]
    point_end = tkline_points[-1]
    if(len(ai_segments[i+1])==4):
      segment_type = 'arc'
      tkline_points.append(tuple((ai_segments[i+1][2], ai_segments[i+1][3])))
      point_start = tkline_points[-3]
      point_mid = tkline_points[-2]
      point_end = tkline_points[-1]
    if(i==segment_nb-1):
      #print("dbg306: last segment")
      if(ai_outline_closed):
        #print("dbg307: close")
        point_end = tkline_points[0]
    #print("dbg563: i: {:d}  segment: {:s}".format(i, segment_type))
    if(segment_type=='line'):
      tkinter_line = (point_start[0], point_start[1], point_end[0], point_end[1])
      tkline_outline.append(tkinter_line)
    elif(segment_type=='arc'):
      arc_polyline = arc_of_circle(point_start, point_mid, point_end, unit_circle_resolution)
      arc_polyline_tk = []
      for i in range(len(arc_polyline)-1):
        arc_polyline_tk.append((arc_polyline[i][0], arc_polyline[i][1], arc_polyline[i+1][0], arc_polyline[i+1][1]))
      tkline_outline.extend(arc_polyline_tk)
  r_outline = tuple(tkline_outline)
  return(r_outline)

def outline_circle_with_tkinter(ai_center, ai_radius):
  """ Transform the circle outline into tkinter lines
  """
  circle_points = complete_circle(ai_center, ai_radius, unit_circle_resolution)
  circle_polyline_tk = []
  for i in range(len(circle_points)-1):
    circle_polyline_tk.append((circle_points[i][0], circle_points[i][1], circle_points[i+1][0], circle_points[i+1][1]))
  circle_polyline_tk.append((circle_points[-1][0], circle_points[-1][1], circle_points[0][0], circle_points[0][1]))
  r_outline = tuple(circle_polyline_tk)
  return(r_outline)

################################################################
# ******** outline creation API ***************
################################################################

def outline_arc_line(ai_segments, ai_backend):
  """ Generates the arcs and lines outline according to the selected backend
      Possible backend: freecad, mozman dxfwrite, mozman svgwrite, Tkinter.
      ai_segments is a list of segments (ie line or arc)
      a segment starts from the last point of the previous segment.
      a line is defined by a list of two floats [x-end, y-end]
      an arc is defined by a list of four floats [x-mid, y-mid, x-end, y-end]
      The first element of ai_segments is the starting point, a list of two floats [x-start, y-start]
      If the last point [x-end, y-end] of the last segment is equal to [x-start, y-start] the outline is closed.
  """
  r_outline = ''
  #print("dbg204: len(ai_segments):", len(ai_segments))
  #print("dbg205: ai_backend:", ai_backend)
  # general checks on ai_segments
  if(len(ai_segments)<2):
    print("ERR402: Error, the segment list must contain at least 2 elements. Currently, len(ai_segments) = {:d}".format(len(ai_segments)))
    sys.exit(2)
  if(len(ai_segments[0])!=2):
    print("ERR403: Error, the first element of the segment list must have 2 elements. Currently, len(ai_segments[0]) = {:d}".format(len(ai_segments[0])))
    sys.exit(2)
  for i in range(len(ai_segments)):
    if((len(ai_segments[i])!=2)and(len(ai_segments[i])!=4)):
      print("ERR405: Error, the length of the segment {:d} must be 2 or 4. Currently len(ai_segments[i]) = {:d}".format(i, len(ai_segments[i])))
      sys.exit(2)
  # check if the outline is closed
  outline_closed = False
  if((ai_segments[0][0]==ai_segments[-1][-2])and(ai_segments[0][1]==ai_segments[-1][-1])):
    #print("dbg207: the outline is closed.")
    outline_closed = True
  # select backend
  if(ai_backend=='freecad'):
    r_outline = outline_arc_line_with_freecad(ai_segments, outline_closed)
  elif(ai_backend=='svgwrite'):
    r_outline = outline_arc_line_with_svgwrite(ai_segments, outline_closed)
  elif(ai_backend=='dxfwrite'):
    r_outline = outline_arc_line_with_dxfwrite(ai_segments, outline_closed)
  elif(ai_backend=='tkinter'):
    r_outline = outline_arc_line_with_tkinter(ai_segments, outline_closed)
  return(r_outline)

def outline_circle(ai_center, ai_radius, ai_backend):
  """ Generates a circle according to the selected backend.
      Possible backend: freecad, mozman dxfwrite, mozman svgwrite, Tkinter.
  """
  r_outline = ''
  # check the radius
  if(ai_radius<=0):
    print("ERR409: Error, the radius is negative or null!")
    sys.exit(2)
  # select backend
  if(ai_backend=='freecad'):
    r_outline = Part.Circle(Base.Vector(ai_center[0], ai_center[1], 0), Base.Vector(0,0,1), ai_radius).toShape()
  elif(ai_backend=='svgwrite'):
    r_outline = svgwrite.shapes.Circle(center=(ai_center[0], ai_center[1]), r=ai_radius)
    r_outline.fill('green', opacity=0.25).stroke('black', width=1)
  elif(ai_backend=='dxfwrite'):
    r_outline = DXFEngine.circle(radius=ai_radius, center=(ai_center[0], ai_center[1]))
  elif(ai_backend=='tkinter'):
    r_outline = outline_circle_with_tkinter(ai_center, ai_radius)
  return(r_outline)


################################################################
# ******** test API ***********
################################################################

def outline_arc_line_test1():
  """ test the functions outline_arc_line and outline_circle.
  """
  l_ol1 = [
    [0,0],
    [20,0],
    [20,20],
    [0,20],
    [0,0]]

  l_ol2 = [
    [110,0],
    [120,0],
    [130,0, 130,10],
    [130,20],
    [130,30, 120,30],
    [110,30],
    [100,30, 100,20],
    [100,10],
    [100,0, 110,0]]

  l_ol3 = [
    [210,0],
    [220,0],
    [230,0, 230,10],
    [230,20],
    [230,30, 220,30],
    [210,30],
    [200,30, 200,20],
    [200,10]]
    #[200,0, 210,0]]

  # check CC (clock wise)
  l_ol4 = [
    [300,10],
    [300, 20],
    [300,30, 310,30],
    [320,30],
    [330,30, 330,20],
    [330,10],
    [330,0, 320,0],
    [310,0]]

  l_ol5 = [
    [0,100],
    [100,150],
    [110,155, 120, 150],
    [150,110],
    [160,100, 170, 105],
    [200,200],
    [0,200],
    [0,100]]

  l_ols = [l_ol1, l_ol2, l_ol3, l_ol4, l_ol5]
  #l_ols = [l_ol2]
  # circle
  l_circle_center = [200,200]
  l_circle_radius = 150
  # backend freecad
  print("dbg701: test1 backend freecad")
  for i_ol in l_ols:
    r_ol = outline_arc_line(i_ol, 'freecad')
    #Part.show(r_ol)
    l_test_face = Part.Face(Part.Wire(r_ol.Edges))
    r_test_solid = l_test_face.extrude(Base.Vector(0,0,1)) # straight linear extrusion
    Part.show(r_test_solid)
  r_ol = outline_circle(l_circle_center, l_circle_radius, 'freecad')
  l_test_face = Part.Face(Part.Wire(r_ol.Edges))
  r_test_solid = l_test_face.extrude(Base.Vector(0,0,1)) # straight linear extrusion
  Part.show(r_test_solid)
  # backend svgwrite
  print("dbg702: test1 backend svgwrite")
  output_svg_file_name =  "outline_arc_line_test1_00.svg"
  object_svg = svgwrite.Drawing(filename = output_svg_file_name)
  #output_file_idx = 0
  for i_ol in l_ols:
    #output_file_idx += 1
    #output_svg_file_name =  "outline_arc_line_test1_{:02d}.svg".format(output_file_idx)
    #object_svg = svgwrite.Drawing(filename = output_svg_file_name)
    svg_outline = outline_arc_line(i_ol, 'svgwrite')
    for one_line_or_arc in svg_outline:
      object_svg.add(one_line_or_arc)
    #object_svg.save()
  one_circle = outline_circle(l_circle_center, l_circle_radius, 'svgwrite')
  object_svg.add(one_circle)
  object_svg.save()
  # backend dxfwrite
  print("dbg703: test1 backend dxfwrite")
  output_dxf_file_name =  "outline_arc_line_test1_00.dxf"
  object_dxf = DXFEngine.drawing(output_dxf_file_name)
  #object_dxf.add_layer(default_dxf_layer_name)
  for i_ol in l_ols:
    dxf_outline = outline_arc_line(i_ol, 'dxfwrite')
    for one_line_or_arc in dxf_outline:
      object_dxf.add(one_line_or_arc)
  one_circle = outline_circle(l_circle_center, l_circle_radius, 'dxfwrite')
  object_dxf.add(one_circle)
  object_dxf.save()
  # backend tkinter
  print("dbg704: test1 backend tkinter")
  tk_root = Tkinter.Tk()
  my_canvas = display_backend.Two_Canvas(tk_root)
  # callback function for display_backend
  def sub_canvas_graphics(ai_angle_position):
    r_canvas_graphics = []
    for i_ol in l_ols:
      r_canvas_graphics.append(('graphic_lines', outline_arc_line(i_ol, 'tkinter'), 'red', 2))
    r_canvas_graphics.append(('graphic_lines', outline_circle(l_circle_center, l_circle_radius, 'tkinter'), 'blue', 2))
    return(r_canvas_graphics)
  # end of callback function
  my_canvas.add_canvas_graphic_function(sub_canvas_graphics)
  tk_root.mainloop()
  #
  r_test = 1
  return(r_test)

################################################################
# ******** command line interface ***********
################################################################

def outline_backends_cli(ai_args=None):
  """ command line interface to run this script in standalone
  """
  ob_parser = argparse.ArgumentParser(description='Test the outline_backends API.')
  ob_parser.add_argument('--test1','--t1', action='store_true', default=False, dest='sw_test1',
    help='Run outline_arc_line_test1()')
  # this ensure the possible to use the script with python and freecad
  # You can not use argparse and FreeCAD together, so it's actually useless !
  # Running this script, FreeCAD will just use the argparse default values
  effective_args = ai_args
  if(effective_args==None):
    arg_index_offset=0
    if(sys.argv[0]=='freecad'): # check if the script is used by freecad
      arg_index_offset=1
      if(len(sys.argv)>=2):
        if(sys.argv[1]=='-c'): # check if the script is used by freecad -c
          arg_index_offset=2
    effective_args = sys.argv[arg_index_offset+1:]
  #print("dbg115: effective_args:", str(effective_args))
  #FreeCAD.Console.PrintMessage("dbg116: effective_args: %s\n"%(str(effective_args)))
  ob_args = ob_parser.parse_args(effective_args)
  r_obc = 0
  print("dbg111: start testing outline_backends.py")
  if(ob_args.sw_test1):
    r_obc = outline_arc_line_test1()
  print("dbg999: end of script")
  return(r_obc)

################################################################
# main
################################################################

if __name__ == "__main__":
  FreeCAD.Console.PrintMessage("outline_backends.py says hello!\n")
  # select your script behavior
  #outline_backends_cli()
  outline_backends_cli("--test1".split())

