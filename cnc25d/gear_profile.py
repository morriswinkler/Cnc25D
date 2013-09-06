# gear_profile.py
# generates a gear_profile and simulates it.
# created by charlyoleg on 2013/08/20
#
# (C) Copyright 2013 charlyoleg
#
# This file is part of the Cnc25D Python package.
# 
# Cnc25D is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Cnc25D is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Cnc25D.  If not, see <http://www.gnu.org/licenses/>.


"""
gear_profile.py is a parametric generator of gear-profiles.
You can use the gear-profile to create gearwheel, gearring or gearbar.
The function gear_profile() returns an format B outline that can be easily included in other scripts.
"""

################################################################
# header for Python / FreeCAD compatibility
################################################################

import cnc25d_api
#cnc25d_api.importing_freecad()

#print("FreeCAD.Version:", FreeCAD.Version())
#FreeCAD.Console.PrintMessage("Hello from PrintMessage!\n") # avoid using this method because it is not printed in the FreeCAD GUI

################################################################
# import
################################################################

# Python standard library
import math
import sys, argparse
#from datetime import datetime
#import os, errno
#import re
import Tkinter # to display the outline in a small GUI
# FreeCAD
#import Part
#from FreeCAD import Base
# 3rd parties
#import svgwrite
#from dxfwrite import DXFEngine
# cnc25d
import small_geometry # use some well-tested functions from the internal of the cnc25d_api

################################################################
# module variable
################################################################
gp_radian_epsilon = math.pi/1000
g1_rotation_speed = 1 # rad/s
speed_scale = 0.2 #1

################################################################
# gear_profile argparse
################################################################

def gear_profile_add_argument(ai_parser, ai_variant=0):
  """ Add the argparse switches relative to the gear_profile
      This function intends to be used by the gear_profile_cli, gear_profile_self_test and also gearwheel, gearring, gearbar ...
      ai_variant let's you remove some arguments:
      0:all for gear_profile_cli() and gear_profile_self_test()
      1:restriction for gearwheel
      2:restriction for gearring
  """
  r_parser = ai_parser
  ### first gear
  # general
  if((ai_variant!=1)and(ai_variant!=2)):
    r_parser.add_argument('--gear_type','--gt', action='store', default='e', dest='sw_gear_type',
      help="Select the type of gear. Possible values: 'e', 'i', 'l'. Default: 'e'")
  r_parser.add_argument('--gear_tooth_nb','--gtn', action='store', type=int, default=0, dest='sw_gear_tooth_nb',
    help="Set the number of teeth of the first gear_profile.")
  r_parser.add_argument('--gear_module','--gm', action='store', type=float, default=0.0, dest='sw_gear_module',
    help="Set the module of the gear. It influences the gear_profile diameters.")
  r_parser.add_argument('--gear_primitive_diameter','--gpd', action='store', type=float, default=0.0, dest='sw_gear_primitive_diameter',
    help="If not zero, redefine the gear module to get this primitive diameter of the first gear_profile. Default: 0. If gearbar, it redefines the length.")
  r_parser.add_argument('--gear_addendum_dedendum_parity','--gadp', action='store', type=float, default=50.0, dest='sw_gear_addendum_dedendum_parity',
    help="Set the addendum / dedendum parity of the first gear_profile. Default: 50.0%%")
  # tooth height
  r_parser.add_argument('--gear_tooth_half_height','--gthh', action='store', type=float, default=0.0, dest='sw_gear_tooth_half_height',
    help="If not zero, redefine the tooth half height of the first gear_profile. Default: 0.0")
  r_parser.add_argument('--gear_addendum_height_pourcentage','--gahp', action='store', type=float, default=100.0, dest='sw_gear_addendum_height_pourcentage',
    help="Set the addendum height of the first gear_profile in pourcentage of the tooth half height. Default: 100.0%%")
  r_parser.add_argument('--gear_dedendum_height_pourcentage','--gdhp', action='store', type=float, default=100.0, dest='sw_gear_dedendum_height_pourcentage',
    help="Set the dedendum height of the first gear_profile in pourcentage of the tooth half height. Default: 100.0%%")
  r_parser.add_argument('--gear_hollow_height_pourcentage','--ghhp', action='store', type=float, default=25.0, dest='sw_gear_hollow_height_pourcentage',
    help="Set the hollow height of the first gear_profile in pourcentage of the tooth half height. The hollow is a clear space for the top of the teeth of the other gearwheel. Default: 25.0%%")
  r_parser.add_argument('--gear_router_bit_radius','--grr', action='store', type=float, default=0.1, dest='sw_gear_router_bit_radius',
    help="Set the router_bit radius used to create the gear hollow of the first gear_profile. Default: 0.1")
  # positive involute
  r_parser.add_argument('--gear_base_diameter','--gbd', action='store', type=float, default=0.0, dest='sw_gear_base_diameter',
    help="If not zero, redefine the base diameter of the first gear involute. Default: 0")
  r_parser.add_argument('--gear_force_angle','--gfa', action='store', type=float, default=0.0, dest='sw_gear_force_angle',
    help="If not zero, redefine the gear_base_diameter to get this force angle at the gear contact. Default: 0.0")
  r_parser.add_argument('--gear_tooth_resolution','--gtr', action='store', type=int, default=2, dest='sw_gear_tooth_resolution',
    help="It sets the number of segments of the gear involute. Default: 2")
  r_parser.add_argument('--gear_skin_thickness','--gst', action='store', type=float, default=0.0, dest='sw_gear_skin_thickness',
    help="Add or remove radial thickness on the gear involute. Default: 0.0")
  # negative involute (if zero, negative involute = positive involute)
  r_parser.add_argument('--gear_base_diameter_n','--gbdn', action='store', type=float, default=0.0, dest='sw_gear_base_diameter_n',
    help="If not zero, redefine the base diameter of the first gear negative involute. Default: 0")
  r_parser.add_argument('--gear_force_angle_n','--gfan', action='store', type=float, default=0.0, dest='sw_gear_force_angle_n',
    help="If not zero, redefine the negative_gear_base_diameter to get this force angle at the gear contact. Default: 0.0")
  r_parser.add_argument('--gear_tooth_resolution_n','--gtrn', action='store', type=int, default=0, dest='sw_gear_tooth_resolution_n',
    help="If not zero, it sets the number of segments of the gear negative involute. Default: 0")
  r_parser.add_argument('--gear_skin_thickness_n','--gstn', action='store', type=float, default=0.0, dest='sw_gear_skin_thickness_n',
    help="If not zero, add or remove radial thickness on the gear negative involute. Default: 0.0")
  ### second gear
  # general
  if(ai_variant!=2):
    r_parser.add_argument('--second_gear_type','--sgt', action='store', default='e', dest='sw_second_gear_type',
      help="Select the type of gear. Possible values: 'e', 'i', 'l'. Default: 'e'")
  r_parser.add_argument('--second_gear_tooth_nb','--sgtn', action='store', type=int, default=0, dest='sw_second_gear_tooth_nb',
    help="Set the number of teeth of the second gear_profile.")
  r_parser.add_argument('--second_gear_primitive_diameter','--sgpd', action='store', type=float, default=0.0, dest='sw_second_gear_primitive_diameter',
    help="If not zero, redefine the gear module to get this primitive diameter of the second gear_profile. Default: 0.0. If gearbar, it redefines the length.")
  r_parser.add_argument('--second_gear_addendum_dedendum_parity','--sgadp', action='store', type=float, default=0.0, dest='sw_second_gear_addendum_dedendum_parity',
    help="Overwrite the addendum / dedendum parity of the second gear_profile if different from 0.0. Default: 0.0%%")
  # tooth height
  r_parser.add_argument('--second_gear_tooth_half_height','--sgthh', action='store', type=float, default=0.0, dest='sw_second_gear_tooth_half_height',
    help="If not zero, redefine the tooth half height of the second gear_profile. Default: 0.0")
  r_parser.add_argument('--second_gear_addendum_height_pourcentage','--sgahp', action='store', type=float, default=100.0, dest='sw_second_gear_addendum_height_pourcentage',
    help="Set the addendum height of the second gear_profile in pourcentage of the tooth half height. Default: 100.0%%")
  r_parser.add_argument('--second_gear_dedendum_height_pourcentage','--sgdhp', action='store', type=float, default=100.0, dest='sw_second_gear_dedendum_height_pourcentage',
    help="Set the dedendum height of the second gear_profile in pourcentage of the tooth half height. Default: 100.0%%")
  r_parser.add_argument('--second_gear_hollow_height_pourcentage','--sghhp', action='store', type=float, default=25.0, dest='sw_second_gear_hollow_height_pourcentage',
    help="Set the hollow height of the second gear_profile in pourcentage of the tooth half height. The hollow is a clear space for the top of the teeth of the other gearwheel. Default: 25.0%%")
  r_parser.add_argument('--second_gear_router_bit_radius','--sgrr', action='store', type=float, default=0.0, dest='sw_second_gear_router_bit_radius',
    help="If not zero, overwrite the router_bit radius used to create the gear hollow of the second gear_profile. Default: 0.0")
  # positive involute
  r_parser.add_argument('--second_gear_base_diameter','--sgbd', action='store', type=float, default=0.0, dest='sw_second_gear_base_diameter',
    help="If not zero, redefine the base diameter of the second gear involute. Default: 0.0")
  r_parser.add_argument('--second_gear_tooth_resolution','--sgtr', action='store', type=int, default=0, dest='sw_second_gear_tooth_resolution',
    help="If not zero, it sets the number of segments of the second gear involute. Default: 0")
  r_parser.add_argument('--second_gear_skin_thickness','--sgst', action='store', type=float, default=0.0, dest='sw_second_gear_skin_thickness',
    help="Add or remove radial thickness on the gear involute. Default: 0.0")
  # negative involute (if zero, negative involute = positive involute)
  r_parser.add_argument('--second_gear_base_diameter_n','--sgbdn', action='store', type=float, default=0.0, dest='sw_second_gear_base_diameter_n',
    help="If not zero, redefine the base diameter of the second gear negative involute. Default: 0.0")
  r_parser.add_argument('--second_gear_tooth_resolution_n','--sgtrn', action='store', type=int, default=0, dest='sw_second_gear_tooth_resolution_n',
    help="If not zero, it sets the number of segments of the second gear negative involute. Default: 0")
  r_parser.add_argument('--second_gear_skin_thickness_n','--sgstn', action='store', type=float, default=0.0, dest='sw_second_gear_skin_thickness_n',
    help="If not zero, add or remove radial thickness on the gear negative involute. Default: 0.0")
  ### gearbar specific (used by gearbar1 and gearbar2)
  r_parser.add_argument('--gearbar_slope','--gbs', action='store', type=float, default=0.0, dest='sw_gearbar_slope',
    help="if not zero, set the tooth slope angle for the gearbar. Default 0.0")
  r_parser.add_argument('--gearbar_slope_n','--gbsn', action='store', type=float, default=0.0, dest='sw_gearbar_slope_n',
    help="if not zero, set the tooth negative slope angle for the gearbar. Default 0.0")
  ### position
  # first gear position
  r_parser.add_argument('--center_position_x','--cpx', action='store', type=float, default=0.0, dest='sw_center_position_x',
    help="Set the x-position of the first gear_profile center. Default: 0.0")
  r_parser.add_argument('--center_position_y','--cpy', action='store', type=float, default=0.0, dest='sw_center_position_y',
    help="Set the y-position of the first gear_profile center. Default: 0.0")
  r_parser.add_argument('--gear_initial_angle','--gia', action='store', type=float, default=0.0, dest='sw_gear_initial_angle',
    help="Set the gear reference angle (in Radian). Default: 0.0")
  # second gear position
  r_parser.add_argument('--second_gear_position_angle','--sgpa', action='store', type=float, default=0.0, dest='sw_second_gear_position_angle',
    help="Angle in Radian that sets the postion on the second gear_profile. Default: 0.0")
  r_parser.add_argument('--second_gear_additional_axis_length','--sgaal', action='store', type=float, default=0.0, dest='sw_second_gear_additional_axis_length',
    help="Set an additional value for the inter-axis length between the first and the second gear_profiles. Default: 0.0")
  ### portion
  if(ai_variant!=1):
    r_parser.add_argument('--cut_portion','--cp', action='store', nargs=3, type=int, default=(0, 0, 0), dest='sw_cut_portion',
      help="(N, first_end, last_end) If N>1, cut a portion of N tooth ofthe gear_profile. first_end and last_end defines in details where the profile stop (0: slope-top, 1: top-middle, 2: slope-bottom, 3: hollow-middle). Default: (0,0,0)")
  ### output
  # gear_profile extrusion (currently only linear extrusion is possible)
  r_parser.add_argument('--gear_profile_height','--gwh', action='store', type=float, default=1.0, dest='sw_gear_profile_height',
    help="Set the height of the linear extrusion of the first gear_profile. Default: 1.0")
  # simulation
  r_parser.add_argument('--simulation_enable','--se', action='store_true', default=False, dest='sw_simulation_enable',
    help='It display a Tk window where you can observe the gear running. Check with your eyes if the geometry is working.')
  # output file : added later
  #r_parser.add_argument('--output_file_basename','--ofb', action='store', default='', dest='sw_output_file_basename',
  #  help="If not  the empty_string (the default value), it outputs the (first) gear in file(s) depending on your argument file_extension: .dxf uses mozman dxfwrite, .svg uses mozman svgwrite, no-extension uses FreeCAD and you get .brep and .dxf")
  # return
  return(r_parser)
    
################################################################
# help functions (including involute_to_circle)
################################################################

def involute_to_circle(ai_center, ai_base_radius, ai_initial_angle, ai_orientation, ai_parameter):
  """ Compute the Cartesian coordinates of P a point of an involute_to_circle curve with the parameter u
      ai_center: center of the base circle (O)
      ai_base_radius: radius of the base circle (B)
      ai_initial_angle : angle (xOS) with (S) start of of the involute_to_circle
      ai_orientation: orienation of the involute_to_circle: 1=CCW -1=CW
      it returns: the Cartesian coordinates of (P) and the tangent inclination (xPt)
  """
  # use notation of the documentation
  OX = ai_center[0]
  OY = ai_center[1]
  B = ai_base_radius
  s = ai_initial_angle
  rd = ai_orientation
  u = ai_parameter
  # check the parameter
  if(u<0):
    print("ERR099: Error, the parameter of the involute_to_circle must be positive {:0.8f}".format(u))
    print("dbg887: ai_center {:0.2f} {:0.2f}  ai_base_radius {:0.2f}  ai_initial_angle {:0.2f}  ai_orientation {:d}  ai_parameter {:0.2f}".format(ai_center[0], ai_center[1], ai_base_radius, ai_initial_angle, ai_orientation, ai_parameter))
    sys.exit(2)
  # involute_to_circle of center (0,0), radius 1 and initial_angle = 0 with the parameter u
  px0 = math.cos(u)+u*math.sin(u)
  py0 = rd*(math.sin(u)-u*math.cos(u))
  ti0 = math.fmod(rd*u+math.pi, 2*math.pi) - math.pi # =u translated in [-pi,pi[
  # involute_to_circle of center (OX,OY), radius B and initial_angle = s with the parameter u
  px = OX+math.cos(s)*B*px0-math.sin(s)*B*py0
  py = OY+math.sin(s)*B*px0+math.cos(s)*B*py0
  ti = math.fmod(ti0+s+3*math.pi, 2*math.pi) - math.pi #=u+s translated in [-pi,pi[
  # return
  r_itc=(px, py, ti)
  return(r_itc)

def search_point_of_involute_to_circle(ai_center, ai_base_radius, ai_initial_angle, ai_orientation, ai_altitude, ai_step, ai_precision):
  """ Compute the coordinates of the intersection (P) of an involute_to_circle curve and a circle of raidus ai_altitude
      ai_center: center of the base circle and of the other circle (O)
      ai_base_radius: radius of the base circle (B)
      ai_initial_angle : angle (xOS) with (S) start of of the involute_to_circle
      ai_orientation: orienation of the involute_to_circle: 1=CCW -1=CW
      ai_altitude: radius of the other circle
      ai_step: initial increment of the parameter to converge to (P)
      ai_precision: required precision to get closer to ai_altitude
      it returns: the paramter u, the angle (xOP), the Cartesian coordinates of (P), the tangent inclination (xPt)
  """
  #print("dbg974: ai_center:", ai_center)
  #print("dbg975: ai_base_radius:", ai_base_radius)
  #print("dbg976: ai_initial_angle:", ai_initial_angle)
  #print("dbg977: ai_orientation:", ai_orientation)
  #print("dbg978: ai_altitude:", ai_altitude)
  #print("dbg979: ai_step:", ai_step)
  #print("dbg980: ai_precision:", ai_precision)
  # use notation of the documentation
  OX = ai_center[0]
  OY = ai_center[1]
  B = ai_base_radius
  s = ai_initial_angle
  rd = ai_orientation
  R = ai_altitude
  # check the paramter
  if(R<B):
    print("ERR098: Error, the altitude {:0.2f} is smaller than the base_diameter {:0.2f}".format(R, B))
    sys.exit(2)
  ### method 1
  ## converge to P
  #u = 0
  #step = ai_step
  #error = -2*ai_precision
  #iteration_cnt = 0
  #while(abs(error)>ai_precision):
  #  iteration_cnt += 1
  #  #print("dbg351: iteration_cnt: {:d}  u: {:0.6f}  step: {:0.6f}  error: {:0.6f}".format(iteration_cnt, u, step, error))
  #  (px, py, ti) = involute_to_circle((OX,OY), B, s, rd, u)
  #  OP = math.sqrt((px-OX)**2+(py-OY)**2)
  #  sign_old_error = math.copysign(1, error)
  #  error = OP-R
  #  sign_new_error = math.copysign(1, error)
  #  if(sign_old_error*sign_new_error<0):
  #    step = step/2
  #  if(sign_new_error<0):
  #    u=u+step
  #  else:
  #    u=u-step
  ## we get u, px, py and ti
  ## calcultation of a = angle (xOP)
  #a = math.atan2((py-OY)/OP, (px-OX)/OP)
  #r_spoitc = (u, a, px, py, ti)
  ### method 2
  u2 = math.sqrt((R/B)**2-1)
  a2 = s+rd*(u2-math.atan(u2))
  ## compare the result of the two methods
  #if(abs(u2-u)>2*ai_precision)2:
  #  print("ERR877: Error in the calculation of u {:0.3f} or u2 {:0.3f}".format(u, u2))
  #  sys.exit(2)
  #if(abs(a2-a)>2*ai_precision):
  #  print("ERR878: Error in the calculation of a {:0.3f} or a2 {:0.3f}".format(a, a2))
  #  sys.exit(2)
  (px2, py2, ti2) = involute_to_circle((OX,OY), B, s, rd, u2)
  # return
  r_spoitc = (u2, a2, px2, py2, ti2)
  return(r_spoitc)

def sample_of_gear_tooth_profile(ai_center, ai_base_radius, ai_initial_angle, ai_orientation, ai_thickness_offset, ai_parameter):
  """ Compute the Cartesian coordinates of Q a point of a gear_tooth_profile with the parameter u
      ai_center: center of the base circle (O)
      ai_base_radius: radius of the base circle (B)
      ai_initial_angle : angle (xOS) with (S) start of of the involute_to_circle
      ai_orientation: orienation of the involute_to_circle: 1=CCW -1=CW
      ai_thickness_offset: translation apply to P. The translation is perpendicular to the tangent. Positive if move away from (O). Negative if move closer to (O)
      it returns: the Cartesian coordinates of (Q) and the tangent inclination (xPt)
  """
  (px, py, ti) = involute_to_circle(ai_center, ai_base_radius, ai_initial_angle, ai_orientation, ai_parameter)
  #rd = ai_orientation
  #qx = px + ai_thickness_offset*math.cos(ti-rd*math.pi/2) # cos(a-pi/2)=sin(a)   cos(a+pi/2)=-sin(a)
  #qy = py + ai_thickness_offset*math.sin(ti-rd*math.pi/2) # sin(a-pi/2)=-cos(a)  sin(a+pi/2)=cos(a)
  qx = px + ai_orientation*ai_thickness_offset*math.sin(ti)
  qy = py - ai_orientation*ai_thickness_offset*math.cos(ti)
  # return
  r_sogtp = (qx, qy, ti)
  return(r_sogtp)

def calc_low_level_gear_parameters(ai_param):
  """ From the hight level parameters relative to a gearwheel (or gearbar) and returns the low level parameters required to compute the gearwheel outline
  """
  # get the hight level parameters
  g_type  = ai_param['gear_type']
  g_n     = ai_param['full_tooth_nb']
  g_m     = ai_param['module']
  g_pr    = ai_param['primitive_radius']
  g_adp   = ai_param['addendum_dedendum_parity']
  g_thh   = ai_param['tooth_half_height']
  g_ar    = ai_param['addendum_radius']
  g_dr    = ai_param['dedendum_radius']
  g_brp   = ai_param['positive_base_radius']
  g_brn   = ai_param['negative_base_radius']
  g_ox    = ai_param['center_ox']
  g_oy    = ai_param['center_oy']
  g_rbr   = ai_param['gear_router_bit_radius']
  g_hr    = ai_param['hollow_radius']
  g_irp   = ai_param['positive_involute_resolution']
  g_irn   = ai_param['negative_involute_resolution']
  g_stp   = ai_param['positive_skin_thickness']
  g_stn   = ai_param['negative_skin_thickness']
  g_ptn   = ai_param['portion_tooth_nb']
  g_pfe   = ai_param['portion_first_end']
  g_ple   = ai_param['portion_last_end']
  g_bi    = ai_param['gearbar_inclination']
  g_sp    = ai_param['positive_slope_angle']
  g_sn    = ai_param['negative_slope_angle']
  g_ah    = ai_param['addendum_height']
  g_dh    = ai_param['dedendum_height']
  g_hh    = ai_param['hollow_height']
  # precision
  radian_epsilon = math.pi/1000
  radian_epsilon_2 = math.pi/10000
  # gear characteristic
  g_ks = 1 # addendum_dedendum_sign for external and linear gear
  g_pc = 1 # position coefficient
  if(g_type=='i'): # internal gear
    g_ks = -1
  elif(g_type=='l'): # linear gear
    g_pc = 0
  ### check
  # tooth height check
  #
  if(g_ks*(g_pr-g_dr)<0):
    print("ERR985: Error, g_pr {:0.2f} and g_dr {:0.2f} are not in the correct order!".format(g_pr, g_dr))
    sys.exit(2)
  if(g_ks*(g_ar-g_pr)<0):
    print("ERR986: Error, g_pr {:0.2f} and g_ar {:0.2f} are not in the correct order!".format(g_pr, g_ar))
    sys.exit(2)
  # involute resolution check
  if(g_irp<1):
    print("ERR786: Error, g_irp {:d} must be equal or bigger than 1!".format(g_irp))
    sys.exit(2)
  if(g_irn<1):
    print("ERR787: Error, g_irn {:d} must be equal or bigger than 1!".format(g_irn))
    sys.exit(2)
  ### calculation of the low level parameters
  r_low_parameters = ()
  if((g_type=='e')or(g_type=='i')):
    ### search points
    initial_step = (g_ar-g_dr)/4
    pi_module_angle = 2*math.pi/g_n
    # intersection of positive involute and the primitive circle
    if(g_brp>g_pr-radian_epsilon):
      print("ERR987: Error, g_brp {:0.2f} is bigger than g_pr {:0.2f}!".format(g_brp, g_pr))
      sys.exit(2)
    (ippu, ippa, ippx, ippy, ippti) = search_point_of_involute_to_circle((g_ox, g_oy), g_brp, 0, 1, g_pr, initial_step, radian_epsilon_2)
    # intersection of negative involute and the primitive circle
    if(g_brn>g_pr-radian_epsilon):
      print("ERR988: Error, g_brn {:0.2f} is bigger than g_pr {:0.2f}!".format(g_brp, g_pr))
      sys.exit(2)
    (inpu, inpa, inpx, inpy, inpti) = search_point_of_involute_to_circle((g_ox, g_oy), g_brn, 0, -1, g_pr, initial_step, radian_epsilon_2)
    # intersection of positive involute and the addendum circle
    ipau=0; ipaa=0;
    if(g_brp<g_ar): # check for internal gear
      (ipau, ipaa, ipax, ipay, ipati) = search_point_of_involute_to_circle((g_ox, g_oy), g_brp, 0, 1, g_ar, initial_step, radian_epsilon_2)
    # intersection of negative involute and the addendum circle
    inau=0; inaa=0;
    if(g_brn<g_ar): # check for internal gear
      (inau, inaa, inax, inay, inati) = search_point_of_involute_to_circle((g_ox, g_oy), g_brn, 0, -1, g_ar, initial_step, radian_epsilon_2)
    # intersection of positive involute and the dedendum circle
    ipdu=0; ipda=0;
    if(g_brp<g_dr): # check for external gear
      (ipdu, ipda, ipdx, ipdy, ipdti) = search_point_of_involute_to_circle((g_ox, g_oy), g_brp, 0, 1, g_dr, initial_step, radian_epsilon_2)
    # intersection of negative involute and the dedendum circle
    indu=0; inda=0;
    if(g_brn<g_dr): # check for external gear
      (indu, inda, indx, indy, indti) = search_point_of_involute_to_circle((g_ox, g_oy), g_brn, 0, -1, g_dr, initial_step, radian_epsilon_2)
    #
    full_positive_involute = g_ks*(ipaa-ipda)
    full_negative_involute = -1*g_ks*(inaa-inda)
    addendum_positive_involute = g_ks*(ipaa-ippa)
    addendum_negative_involute = -1*g_ks*(inaa-inpa)
    dedendum_positive_involute = g_ks*(ippa-ipda)
    dedendum_negative_involute = -1*g_ks*(inpa-inda)
    #print("dbg646: full_positive_involute: {:0.3f}  full_negative_involute: {:0.3f}  addendum_positive_involute: {:0.3f}  addendum_negative_involute: {:0.3f}  dedendum_positive_involute: {:0.3f}  dedendum_negative_involute: {:0.3f}".format(full_positive_involute, full_negative_involute, addendum_positive_involute, addendum_negative_involute, dedendum_positive_involute, dedendum_negative_involute))
    addendum_angle = pi_module_angle*g_adp-(addendum_positive_involute+addendum_negative_involute)
    if(addendum_angle*g_ar<radian_epsilon): # a bit stricter than 0
      print("ERR989: Error, the addendum_angle {:0.2f} is negative or too small!".format(addendum_angle))
      sys.exit(2)
    dedendum_angle = pi_module_angle*(1-g_adp)-(dedendum_positive_involute+dedendum_negative_involute)
    if(dedendum_angle*g_dr<2*g_rbr+radian_epsilon): # a bit stricter than router_bit_radius
      print("ERR990: Error, the dedendum_angle {:0.2f} is negative or too small compare to the router_bit_radius {:0.2f} ({:0.2f} < {:0.2f})!".format(dedendum_angle, g_rbr, dedendum_angle*g_dr, 2*g_rbr))
      sys.exit(2)
    if(g_type=='e'): # negative > hollow > positive
      # low1: to create the gear-profile outline
      i1_base = g_brn
      i1_offset = addendum_angle/2-inaa
      i1_sign = -1
      i1u_nb = g_irn
      i1u_ini = inau
      i1u_inc = (indu-inau)/i1u_nb # <0
      i1_thickness = g_stn
      i2_base = g_brp
      i2_offset = pi_module_angle-addendum_angle/2-ipaa
      i2_sign = 1
      i2u_nb = g_irp
      i2u_ini = ipdu
      i2u_inc = (ipau-ipdu)/i2u_nb # >0
      i2_thickness = g_stp
      ha1 = addendum_angle/2 + full_negative_involute
      # low2: to calculate g2_position
      #i1_primitive_offset = addendum_angle/2-inpa #>0
      #i2_primitive_offset = -1*(addendum_angle/2+ippa) #<0
      i1_primitive_offset = addendum_angle/2+addendum_negative_involute #>0
      i2_primitive_offset = -1*(addendum_angle/2+addendum_positive_involute) #<0
      i1_offset2 = addendum_angle/2-inaa # >0
      i2_offset2 = -1*(addendum_angle/2+ipaa) # <0
      driven_ip_base = g_brp
      driven_ip_offset = i2_offset2
      driven_in_base = g_brn
      driven_in_offset = i1_offset2
    elif(g_type=='i'): # positive > hollow > negative
      # low1
      i1_base = g_brp
      i1_offset = addendum_angle/2-ipaa
      i1_sign = 1
      i1u_nb = g_irp
      i1u_ini = ipau
      i1u_inc = (ipdu-ipau)/i1u_nb # >0
      i1_thickness = g_stp
      i2_base = g_brn
      i2_offset = pi_module_angle-addendum_angle/2-inaa
      i2_sign = -1
      i2u_nb = g_irn
      i2u_ini = indu
      i2u_inc = (inau-indu)/i2u_nb # >0
      i2_thickness = g_stn
      ha1 = addendum_angle/2 + full_positive_involute
      # low2
      # gearring with positive rotation, push with positive involute
      i1_primitive_offset = addendum_angle/2+addendum_positive_involute #>0
      i2_primitive_offset = -1*(addendum_angle/2+addendum_negative_involute) #<0
      i1_offset2 = addendum_angle/2-ipaa
      i2_offset2 = -1*addendum_angle/2-inaa
      driven_ip_base = g_brp
      driven_ip_offset = i1_offset2
      driven_in_base = g_brn
      driven_in_offset = i2_offset2
      #print("dbg663: ipaa {:0.3f}".format(ipaa))
    #
    gear_type = g_type
    #pi_module_angle = 2*math.pi/g_n
    hl1 = g_dr
    hl2 = g_hr
    #ha1 = addendum_angle/2 + full_negative_involute or full_positive_involute
    ha2 = ha1 + dedendum_angle
    hrbr = g_rbr
    hlm = hl2*math.cos(dedendum_angle/2) # this is to ensure nice junction of split gearwheel
    ham = ha1 + dedendum_angle/2
    tlm = g_ar*math.cos(addendum_angle/2) # this is to ensure nice junction of split gearwheel
    ox = g_ox
    oy = g_oy
    if(g_ptn==0):
      portion_tooth_nb = g_n
      closed = True
    else:
      portion_tooth_nb = g_ptn
      closed = False
    first_end = g_pfe # 0: slope-top, 1: top-middle, 2: slope-bottom, 3: half-hollow
    last_end =  g_ple # 0: slope-top, 1: top-middle, 2: slope-bottom, 3: half-hollow
    # return
    make_low_parameters = (gear_type, pi_module_angle,
      i1_base, i1_offset, i1_sign, i1u_nb, i1u_ini, i1u_inc, i1_thickness,
      i2_base, i2_offset, i2_sign, i2u_nb, i2u_ini, i2u_inc, i2_thickness,
      hl1, hl2, ha1, ha2, hrbr, hlm, ham, tlm,
      ox, oy, portion_tooth_nb, first_end, last_end, closed)
    place_low_parameters = (gear_type, pi_module_angle, g_n, g_pr, ox, oy, g_ks, g_pc,
      i1_base, i1_primitive_offset, i1_offset2,
      i2_base, i2_primitive_offset, i2_offset2,
      driven_ip_base, driven_ip_offset, driven_in_base, driven_in_offset)
    # info
    info_txt = "Gear profile details:\n"
    info_txt += "positive involute: \t{:0.3f} (radian)  \t{:0.3f} (mm)  \t{:0.2f} %\n".format(full_positive_involute, g_pr*full_positive_involute, 100*full_positive_involute/pi_module_angle)
    info_txt += "negative involute: \t{:0.3f} (radian)  \t{:0.3f} (mm)  \t{:0.2f} %\n".format(full_negative_involute, g_pr*full_negative_involute, 100*full_negative_involute/pi_module_angle)
    info_txt += "top land:          \t{:0.3f} (radian)  \t{:0.3f} (mm)  \t{:0.2f} %\n".format(addendum_angle, g_ar*addendum_angle, 100*addendum_angle/pi_module_angle)
    info_txt += "bottom land:       \t{:0.3f} (radian)  \t{:0.3f} (mm)  \t{:0.2f} %\n".format(dedendum_angle, g_dr*dedendum_angle, 100*dedendum_angle/pi_module_angle)
  elif(g_type=='l'):
    # linear gear low_1
    pi_module = g_m * math.pi
    positive_addendum = g_ah*math.tan(g_sp)
    positive_dedendum = abs(g_dh)*math.tan(g_sp)
    negative_addendum = g_ah*math.tan(g_sn)
    negative_dedendum = abs(g_dh)*math.tan(g_sn)
    top_land = pi_module*g_adp-(positive_addendum+negative_addendum)
    bottom_land = pi_module*(1-g_adp)-(positive_dedendum+negative_dedendum)
    if(top_land<radian_epsilon):
      print("ERR858: Error, the linear gear top-land {:0.3f} is negative or too small!".format(top_land))
      sys.exit(2)
    if(bottom_land<2*g_rbr+radian_epsilon):
      print("ERR859: Error, the linear gear bottom-land {:0.3f} is too small compare to the gear_router_bit_radius {:0.3f}".format(bottom_land, g_rbr))
      sys.exit(2)
    bar_tooth_nb = g_n
    if(g_ptn>0):
      bar_tooth_nb = g_ptn
    gb_p_offset = -1*(top_land/2+positive_addendum)
    gb_n_offset = top_land/2+negative_addendum
    # linear gear low_2
    i1_base = g_sn
    i1_primitive_offset = -1*(top_land/2+negative_addendum)
    i1_offset2 = -1*(top_land/2+negative_addendum+negative_dedendum)
    i2_base = g_sp
    i2_primitive_offset = top_land/2+positive_addendum
    i2_offset2 = top_land/2+positive_addendum+positive_dedendum
    driven_ip_base = g_sp
    driven_ip_offset = i2_primitive_offset
    driven_in_base = g_sn
    driven_in_offset = i1_primitive_offset
    # return
    make_low_parameters = (g_type, pi_module, g_ox, g_oy, g_bi, bar_tooth_nb, g_pfe, g_ple, g_sp, g_sn, g_ah, g_dh, g_hh, g_rbr, g_stp, g_stn, gb_p_offset, gb_n_offset)
    place_low_parameters = (g_type, pi_module, g_n, g_pr, g_ox, g_oy, g_ks, g_pc,
      i1_base, i1_primitive_offset, i1_offset2,
      i2_base, i2_primitive_offset, i2_offset2,
      driven_ip_base, driven_ip_offset, driven_in_base, driven_in_offset)
    # info
    full_positive_slope = positive_addendum + positive_dedendum
    full_negative_slope = negative_addendum + negative_dedendum
    info_txt = "Gearbar profile details:\n"
    info_txt += "positive slope: \t{:0.3f} (mm)  \t{:0.2f} %\n".format(full_positive_slope, 100*full_positive_slope/pi_module)
    info_txt += "negative slope: \t{:0.3f} (mm)  \t{:0.2f} %\n".format(full_negative_slope, 100*full_negative_slope/pi_module)
    info_txt += "top land:          \t{:0.3f} (mm)  \t{:0.2f} %\n".format(top_land, 100*top_land/pi_module)
    info_txt += "bottom land:       \t{:0.3f} (mm)  \t{:0.2f} %\n".format(bottom_land, 100*bottom_land/pi_module)
  else:
    print("ERR740: Error, the gear_type {:s} doesn't exist!".format(g_type))
    sys.exit(2)
  #return
  r_low_parameters = (make_low_parameters, place_low_parameters, info_txt)
  return(r_low_parameters)

def involute_outline(ai_ox, ai_oy, ai_base_radius, ai_offset, ai_sign, ai_u_nb, ai_u_ini, ai_u_inc, ai_thickness, ai_tooth_angle):
  """ from subset of low-level parameter, generates an involute_to_circle format B outline
  """
  # precision
  #radian_epsilon=math.pi/1000 # unefficient because this function is used often
  radian_epsilon = gp_radian_epsilon
  #
  u = ai_u_ini
  involute_C = []
  for sampling in range(ai_u_nb+1):
    #print("dbg443: u:", u)
    if(abs(u)<radian_epsilon): # for rounding error
      u=0
    (qx, qy, ti) = sample_of_gear_tooth_profile((ai_ox,ai_oy), ai_base_radius, ai_tooth_angle+ai_offset, ai_sign, ai_thickness, u)
    involute_C.append((qx, qy, ti-(ai_sign-1)/2*math.pi))
    u += ai_u_inc
  #print("dbg444: involute_C:", involute_C)
  r_involute_B = cnc25d_api.smooth_outline_c_curve(involute_C, radian_epsilon, 0, "involute_outline")
  return(r_involute_B)

def gearwheel_profile_outline(ai_low_parameters, ai_angle_position):
  """ create the outline of a gear definied by ai_low_parameters
      The reference of a gearwheel is the middle of its first tooth.
      ai_angle_position sets the reference of the gearwheel.
  """
  # get ai_low_parameters
  (gear_type, pi_module_angle,
    i1_base, i1_offset, i1_sign, i1u_nb, i1u_ini, i1u_inc, i1_thickness,
    i2_base, i2_offset, i2_sign, i2u_nb, i2u_ini, i2u_inc, i2_thickness,
    hl1, hl2, ha1, ha2, hrbr, hlm, ham, tlm,
    ox, oy, portion_tooth_nb, first_end, last_end, closed) = ai_low_parameters
  # precision
  #radian_epsilon = math.pi/1000
  radian_epsilon = gp_radian_epsilon
  # construct the final_outline
  r_final_outline = []
  tooth_angle = ai_angle_position
  ### start of the gearwheel_portion
  if(first_end>0):
    half_hollow = []
    start_of_profile_B = []
    if(first_end==1):
      start_of_profile_B = [(ox+tlm*math.cos(tooth_angle), oy+tlm*math.sin(tooth_angle))]
    else:
      start_of_profile_B = involute_outline(ox, oy, i2_base, i2_offset, i2_sign, i2u_nb, i2u_ini, i2u_inc, i2_thickness, tooth_angle-pi_module_angle)
      # gearwheel hollow
      if(first_end==3):
        hollow_A = []
        hollow_A.append((ox+hlm*math.cos(tooth_angle-pi_module_angle+ham), oy+hlm*math.sin(tooth_angle-pi_module_angle+ham), 0))
        hollow_A.append((ox+hl2*math.cos(tooth_angle-pi_module_angle+ha2), oy+hl2*math.sin(tooth_angle-pi_module_angle+ha2), hrbr))
        hollow_A.append((ox+hl1*math.cos(tooth_angle-pi_module_angle+ha2), oy+hl1*math.sin(tooth_angle-pi_module_angle+ha2), 0))
        hollow_B = cnc25d_api.cnc_cut_outline(hollow_A, "hollow")
        half_hollow = hollow_B[0:-1]
    # assembly
    r_final_outline.extend(half_hollow)
    r_final_outline.extend(start_of_profile_B)
  ### bulk of the gearwheel_portion
  for tooth in range(portion_tooth_nb):
    # first involute
    first_involute_B = involute_outline(ox, oy, i1_base, i1_offset, i1_sign, i1u_nb, i1u_ini, i1u_inc, i1_thickness, tooth_angle)
    # gearwheel hollow
    hollow_A = []
    hollow_A.append((ox+hl1*math.cos(tooth_angle+ha1), oy+hl1*math.sin(tooth_angle+ha1), 0))
    hollow_A.append((ox+hl2*math.cos(tooth_angle+ha1), oy+hl2*math.sin(tooth_angle+ha1), hrbr))
    hollow_A.append((ox+hl2*math.cos(tooth_angle+ha2), oy+hl2*math.sin(tooth_angle+ha2), hrbr))
    hollow_A.append((ox+hl1*math.cos(tooth_angle+ha2), oy+hl1*math.sin(tooth_angle+ha2), 0))
    hollow_B = cnc25d_api.cnc_cut_outline(hollow_A, "hollow")
    # second involute
    second_involute_B = involute_outline(ox, oy, i2_base, i2_offset, i2_sign, i2u_nb, i2u_ini, i2u_inc, i2_thickness, tooth_angle)
    # assembly
    r_final_outline.extend(first_involute_B)
    r_final_outline.extend(hollow_B[1:-1])
    r_final_outline.extend(second_involute_B)
    # prepare the next tooth
    tooth_angle += pi_module_angle
  ### end of bulk
  if(last_end>0):
    half_hollow = []
    end_of_profile_B = []
    if(first_end==1):
      end_of_profile_B = [(ox+tlm*math.cos(tooth_angle), oy+tlm*math.sin(tooth_angle))]
    else:
      end_of_profile_B = involute_outline(ox, oy, i1_base, i1_offset, i1_sign, i1u_nb, i1u_ini, i1u_inc, i1_thickness, tooth_angle)
      # gearwheel hollow
      if(first_end==3):
        hollow_A = []
        hollow_A.append((ox+hl1*math.cos(tooth_angle+ha1), oy+hl1*math.sin(tooth_angle+ha1), 0))
        hollow_A.append((ox+hl2*math.cos(tooth_angle+ha1), oy+hl2*math.sin(tooth_angle+ha1), hrbr))
        hollow_A.append((ox+hlm*math.cos(tooth_angle+ham), oy+hlm*math.sin(tooth_angle+ham), 0))
        hollow_B = cnc25d_api.cnc_cut_outline(hollow_A, "hollow")
        half_hollow = hollow_B[1:]
    # assembly
    r_final_outline.extend(end_of_profile_B)
    r_final_outline.extend(half_hollow)
  if(closed):
    r_final_outline.append(r_final_outline[0]) # closed the outline in case of full gearwheel
  #return
  return(r_final_outline)

def ideal_involute_tooth_outline(ai_low_parameters, ai_angle_position, ai_thickness_coeff):
  """ create the ideal tooth_profile over the first tooth of an intern or extern gearwheel
  """
  # precision
  #radian_epsilon=math.pi/1000 # unefficient because this function is used often
  radian_epsilon = gp_radian_epsilon
  # get ai_low_parameters
  (gear_type, pi_module_angle,
    i1_base, i1_offset, i1_sign, i1u_nb, i1u_ini, i1u_inc, i1_thickness,
    i2_base, i2_offset, i2_sign, i2u_nb, i2u_ini, i2u_inc, i2_thickness,
    hl1, hl2, ha1, ha2, hrbr, hlm, ham, tlm,
    ox, oy, portion_tooth_nb, first_end, last_end, closed) = ai_low_parameters
  # precision
  ideal = 8 # additional_sampling_for_ideal_curve. it's a multiplicator
  # initialization
  tooth_angle = ai_angle_position
  # construct the ideal_tooth_outline over the first tooth
  # first_involute
  first_involute = []
  u = i2u_ini
  ideal_i2u_inc = float(i2u_inc)/ideal
  for sampling in range(ideal*i2u_nb+1):
    if(abs(u)<radian_epsilon): # for rounding error
      u=0
    (qx, qy, ti) = sample_of_gear_tooth_profile((ox,oy), i2_base, tooth_angle-pi_module_angle+i2_offset, i2_sign, ai_thickness_coeff*i2_thickness, u)
    first_involute.append((qx, qy))
    u += ideal_i2u_inc
  # second_involute
  second_involute = []
  u = i1u_ini
  ideal_i1u_inc = float(i1u_inc)/ideal
  for sampling in range(ideal*i1u_nb+1):
    if(abs(u)<radian_epsilon): # for rounding error
      u=0
    (qx, qy, ti) = sample_of_gear_tooth_profile((ox,oy), i1_base, tooth_angle+i1_offset, i1_sign, ai_thickness_coeff*i1_thickness, u)
    second_involute.append((qx, qy))
    u += ideal_i1u_inc
  # assembly
  r_ideal_tooth_outline = []
  r_ideal_tooth_outline.extend(first_involute)
  r_ideal_tooth_outline.extend(second_involute)
  #return
  return(r_ideal_tooth_outline)

def slope_outline(ai_ox, ai_oy, ai_bi, ai_offset, ai_slope_angle, ai_sign, ai_top_height, ai_bottom_height, ai_thickness, ai_bottom_router_bit, ai_tooth_position):
  """ from subset of low-level parameter, generates a gearbear_tooth_slope format B outline
  """
  # precision
  #radian_epsilon=math.pi/1000 # unefficient because this function is used often
  radian_epsilon = gp_radian_epsilon
  #
  slope_angle = ai_bi + ai_sign*ai_slope_angle
  thickness_angle = slope_angle - ai_sign*math.pi/2
  top_height = ai_top_height/math.cos(ai_slope_angle)
  bottom_height = ai_bottom_height/math.cos(ai_slope_angle)
  #
  top_x = ai_ox + (ai_tooth_position+ai_offset)*math.cos(ai_bi+math.pi/2) + top_height*math.cos(slope_angle) + ai_thickness*math.cos(thickness_angle)
  top_y = ai_oy + (ai_tooth_position+ai_offset)*math.sin(ai_bi+math.pi/2) + top_height*math.sin(slope_angle) + ai_thickness*math.sin(thickness_angle)
  bottom_x = ai_ox + (ai_tooth_position+ai_offset)*math.cos(ai_bi+math.pi/2) - bottom_height*math.cos(slope_angle) + ai_thickness*math.cos(thickness_angle)
  bottom_y = ai_oy + (ai_tooth_position+ai_offset)*math.sin(ai_bi+math.pi/2) - bottom_height*math.sin(slope_angle) + ai_thickness*math.sin(thickness_angle)
  #
  if(ai_sign==-1):
    r_slope_B = ((top_x, top_y, 0),(bottom_x, bottom_y, ai_bottom_router_bit))
  elif(ai_sign==1):
    r_slope_B = ((bottom_x, bottom_y, ai_bottom_router_bit),(top_x, top_y, 0))
  # return
  return(r_slope_B)

def gearbar_profile_outline(ai_low_parameters, ai_tangential_position):
  """ create the outline of a gearbar definied by ai_low_parameters
      The reference of a gearbar is the middle of the middle tooth.
      ai_tangential_position sets the reference of the gearbar.
  """
  # get ai_low_parameters
  (g_type, pi_module, g_ox, g_oy, g_bi, bar_tooth_nb, g_pfe, g_ple, g_sp, g_sn, g_ah, g_dh, g_hh, g_rbr, g_stp, g_stn, gb_p_offset, gb_n_offset) = ai_low_parameters
  # construct the final_outline
  r_final_outline = []
  half_tooth_nb =  int(bar_tooth_nb/2)
  cyclic_tangential_position = math.fmod(ai_tangential_position, half_tooth_nb*pi_module) # to avoid the gearbar move away from its gearwheel
  tangential_position = cyclic_tangential_position - half_tooth_nb*pi_module # the position reference is the middle of the middle tooth
  # start of the gearbar
  gearbar_A = []
  if(g_pfe==3): # start on hollow_middle
    ideal_slope_n = slope_outline(gb_ox, g_oy, g_bi, gb_n_offset, g_sn, -1, g_ah, g_dh+g_hh, 0, 0, tangential_position-pi_module)
    ideal_slope_p = slope_outline(gb_ox, g_oy, g_bi, gb_p_offset, g_sp,  1, g_ah, g_dh+g_hh, 0, 0, tangential_position)
    hollow_middle_x = (ideal_slope_n[1][0]+ideal_slope_p[0][0])/2
    hollow_middle_y = (ideal_slope_n[1][1]+ideal_slope_p[0][1])/2
    gearbar_A.append((hollow_middle_x, hollow_middle_y, 0)) # hollow middle
    gearbar_A.extend(slope_outline(g_ox, g_oy, g_bi, gb_p_offset, g_sp,  1, g_ah, g_dh+g_hh, g_stp, g_rbr, tangential_position)) # positive slope
  elif(g_pfe==2): # start on the positive slope
    gearbar_A.extend(slope_outline(g_ox, g_oy, g_bi, gb_p_offset, g_sp,  1, g_ah, g_dh+g_hh, g_stp, 0, tangential_position)) # positive slope
  elif(g_pfe==1): # start on the top middle
    ideal_slope_p = slope_outline(g_ox, g_oy, g_bi, gb_p_offset, g_sp,  1, g_ah, g_dh+g_hh, 0, 0, tangential_position)
    ideal_slope_n = slope_outline(g_ox, g_oy, g_bi, gb_n_offset, g_sn, -1, g_ah, g_dh+g_hh, 0, 0, tangential_position)
    top_middle_x = (ideal_slope_p[1][0]+ideal_slope_n[0][0])/2
    top_middle_y = (ideal_slope_p[1][1]+ideal_slope_n[0][1])/2
    gearbar_A.append((top_middle_x, top_middle_y, 0)) # top middle
  if(gearbar_A!=[]):
    gearbar_B = cnc25d_api.cnc_cut_outline(gearbar_A, "start of gearbar")
    r_final_outline.extend(gearbar_B)
  # bulk of the gearbar
  for tooth in range(bar_tooth_nb):
    gearbar_A = []
    gearbar_A.extend(slope_outline(g_ox, g_oy, g_bi, gb_n_offset, g_sn, -1, g_ah, g_dh+g_hh, g_stn, g_rbr, tangential_position)) # negative slope
    gearbar_A.extend(slope_outline(g_ox, g_oy, g_bi, gb_p_offset, g_sp,  1, g_ah, g_dh+g_hh, g_stp, g_rbr, tangential_position+pi_module)) # positive slope
    #print("dbg745: gearbar_A:", gearbar_A)
    gearbar_B = cnc25d_api.cnc_cut_outline(gearbar_A, "bulk of gearbar")
    r_final_outline.extend(gearbar_B)
    # prepare the next tooth
    tangential_position += pi_module
  # end of the gearbar
  gearbar_A = []
  if(g_ple==3): # stop on hollow_middle
    gearbar_A.extend(slope_outline(g_ox, g_oy, g_bi, gb_n_offset, g_sn, -1, g_ah, g_dh+g_hh, g_stn, g_rbr, tangential_position)) # negative slope
    ideal_slope_n = slope_outline(g_ox, g_oy, g_bi, gb_n_offset, g_sn, -1, g_ah, g_dh+g_hh, 0, 0, tangential_position)
    ideal_slope_p = slope_outline(g_ox, g_oy, g_bi, gb_p_offset, g_sp,  1, g_ah, g_dh+g_hh, 0, 0, tangential_position+pi_module)
    hollow_middle_x = (ideal_slope_n[1][0]+ideal_slope_p[0][0])/2
    hollow_middle_y = (ideal_slope_n[1][1]+ideal_slope_p[0][1])/2
    gearbar_A.append((hollow_middle_x, hollow_middle_y, 0)) # hollow middle
  elif(g_ple==2): # stop on the negative slope
    gearbar_A.extend(slope_outline(g_ox, g_oy, g_bi, gb_n_offset, g_sn, -1, g_ah, g_dh+g_hh, g_stn, 0, tangential_position)) # negative slope
  elif(g_ple==1): # stop on the top middle
    ideal_slope_p = slope_outline(g_ox, g_oy, g_bi, gb_p_offset, g_sp,  1, g_ah, g_dh+g_hh, 0, 0, tangential_position)
    ideal_slope_n = slope_outline(g_ox, g_oy, g_bi, gb_n_offset, g_sn, -1, g_ah, g_dh+g_hh, 0, 0, tangential_position)
    top_middle_x = (ideal_slope_p[1][0]+ideal_slope_n[0][0])/2
    top_middle_y = (ideal_slope_p[1][1]+ideal_slope_n[0][1])/2
    gearbar_A.append((top_middle_x, top_middle_y, 0)) # top middle
  if(gearbar_A!=[]):
    gearbar_B = cnc25d_api.cnc_cut_outline(gearbar_A, "end of gearbar")
    r_final_outline.extend(gearbar_B)
  #return
  return(r_final_outline)

def ideal_linear_tooth_outline(ai_low_parameters, ai_tangential_position, ai_thickness_coeff):
  """ create the ideal tooth_profile over the first tooth of a gearbar
  """
  # get ai_low_parameters
  (g_type, pi_module, g_ox, g_oy, g_bi, bar_tooth_nb, g_pfe, g_ple, g_sp, g_sn, g_ah, g_dh, g_hh, g_rbr, g_stp, g_stn, gb_p_offset, gb_n_offset) = ai_low_parameters
  half_tooth_nb =  int(bar_tooth_nb/2)
  cyclic_tangential_position = math.fmod(ai_tangential_position, half_tooth_nb*pi_module) # to avoid the gearbar move away from its gearwheel
  #tangential_position = cyclic_tangential_position - half_tooth_nb*pi_module # the position reference is the middle of the middle tooth
  tangential_position = cyclic_tangential_position
  # tooth
  tooth_A = []
  tooth_A.extend(slope_outline(g_ox, g_oy, g_bi, gb_p_offset, g_sp,  1, g_ah, g_dh, ai_thickness_coeff*g_stp, 0, tangential_position))
  tooth_A.extend(slope_outline(g_ox, g_oy, g_bi, gb_n_offset, g_sn, -1, g_ah, g_dh, ai_thickness_coeff*g_stn, 0, tangential_position))
  r_ideal_tooth_outline_B = cnc25d_api.cnc_cut_outline(tooth_A, "bulk of gearbar")
  #return
  return(r_ideal_tooth_outline_B)

def gear_profile_outline(ai_low_parameters, ai_angle_position):
  """ create the format B outline of a gear definied by ai_low_parameters
      ai_angle_position sets the gear position.
  """
  r_gear_profile_outline_B = []
  g_type = ai_low_parameters[0]
  if((g_type=='e')or(g_type=='i')):
    r_gear_profile_outline_B = gearwheel_profile_outline(ai_low_parameters, ai_angle_position)
  elif(g_type=='l'):
    r_gear_profile_outline_B = gearbar_profile_outline(ai_low_parameters, ai_angle_position)
  #return
  return(r_gear_profile_outline_B)

def ideal_tooth_outline(ai_low_parameters, ai_angle_position, ai_thickness_coeff):
  """ create the ideal tooth_profile over the first tooth of a gear (i, e or l)
  """
  r_ideal_tooth_outline = []
  g_type = ai_low_parameters[0]
  if((g_type=='e')or(g_type=='i')):
    r_ideal_tooth_outline = ideal_involute_tooth_outline(ai_low_parameters, ai_angle_position, ai_thickness_coeff)
  elif(g_type=='l'):
    r_ideal_tooth_outline = ideal_linear_tooth_outline(ai_low_parameters, ai_angle_position, ai_thickness_coeff)
  #return
  return(r_ideal_tooth_outline)

def calc_real_force_angle(ai_g1_type, ai_g1_pr, ai_g1_br, ai_g2_type, ai_g2_pr, ai_g2_br, ai_aal, ai_g1_sa, ai_g2_sa):
  """ calculate the real_force_angle depending also on the additional inter-axis length
  """
  if((ai_g1_type=='e')and(ai_g2_type=='e')):# depending on gear_type
    r_real_force_angle = math.acos(float(ai_g1_br+ai_g2_br)/(ai_g1_pr+ai_g2_pr+ai_aal))
  elif((ai_g1_type=='i')and(ai_g2_type=='e')): # i-e
    if(ai_g2_pr>ai_g1_pr):
      print("ERR546: Error, the gearring radius {:0.3f} must be bigger gearwheel radius {:0.3f}".format(ai_g1_pr, ai_g2_pr))
      sys.exit(2)
    r_real_force_angle = math.acos(float(ai_g1_br-ai_g2_br)/(ai_g1_pr-(ai_g2_pr+ai_aal)))
  elif((ai_g1_type=='e')and(ai_g2_type=='i')): # e-i
    if(ai_g1_pr>ai_g2_pr):
      print("ERR547: Error, the gearring radius {:0.3f} must be bigger gearwheel radius {:0.3f}".format(ai_g2_pr, ai_g1_pr))
      sys.exit(2)
    r_real_force_angle = math.acos(float(ai_g2_br-ai_g1_br)/(ai_g2_pr-(ai_g1_pr+ai_aal)))
  elif((ai_g1_type=='l')and(ai_g2_type=='e')): # l-e
    r_real_force_angle = ai_g1_sa
  elif((ai_g1_type=='e')and(ai_g2_type=='l')): # e-l
    r_real_force_angle = ai_g2_sa
  else:
    print("ERR221: Error, the gear type combination {:s}-{:s} does not exist!".format(ai_g1_type, ai_g2_type))
    sys.exit(2)
  return(r_real_force_angle)

def g2_position_calcultion(ai_g1_low_parameters, ai_g2_low_parameters, ai_rotation_direction, ai_g1_position, ai_aal, ai_g1g2_a):
  """ calculation of the angle position of the second gear and other related parameters (speed, friction)
  """
  # get ai_g1_low_parameters
  (g1_gear_type, g1_pi_module_angle, g1_n, g1_pr, g1_ox, g1_oy, g1_ks, g1_pc,
    g1_i1_base, g1_i1_primitive_offset, g1_i1_offset2,
    g1_i2_base, g1_i2_primitive_offset, g1_i2_offset2,
    g1_driven_ip_base, g1_driven_ip_offset, g1_driven_in_base, g1_driven_in_offset) = ai_g1_low_parameters
  # get ai_g2_low_parameters
  (g2_gear_type, g2_pi_module_angle, g2_n, g2_pr, g2_ox, g2_oy, g2_ks, g2_pc,
    g2_i1_base, g2_i1_primitive_offset, g2_i1_offset2,
    g2_i2_base, g2_i2_primitive_offset, g2_i2_offset2,
    g2_driven_ip_base, g2_driven_ip_offset, g2_driven_in_base, g2_driven_in_offset) = ai_g2_low_parameters
  # precision
  #radian_epsilon = math.pi/1000
  radian_epsilon = gp_radian_epsilon
  # select parameter depending on ai_rotation_direction
  if(ai_rotation_direction==1): # rotation_direction positive (g1 driving, g2 driven) : g1_negative_involute with g2_negative_involute
    g1_primitive_offset = g1_i1_primitive_offset
    g1_br = g1_i1_base
    g1_involute_offset = g1_i1_offset2
    g1_sa = g1_i1_base
  else:
    g1_primitive_offset = g1_i2_primitive_offset
    g1_br = g1_i2_base
    g1_involute_offset = g1_i2_offset2
    g1_sa = g1_i2_base
  # g2 parameter depend on g1_ks and rotation_direction
  if(ai_rotation_direction*g1_ks==1):
    g2_br = g2_driven_in_base
    g2_involute_offset = g2_driven_in_offset
    g2_sa = g2_driven_in_base
  else:
    g2_br = g2_driven_ip_base
    g2_involute_offset = g2_driven_ip_offset
    g2_sa = g2_driven_ip_base
  ## gear system related
  # real_force_angle
  real_force_angle = calc_real_force_angle(g1_gear_type, g1_pr, g1_br, g2_gear_type, g2_pr, g2_br, ai_aal, g1_sa, g2_sa)
  #print("dbg743: real_force_angle:", real_force_angle)
  # length KL (see documentation  graphic gear_position.svg)
  #AB = g1_pr+g2_pr+ai_aal
  AB = abs(g1_ks*g1_pc*g1_pr+g2_ks*g2_pc*g2_pr+ai_aal)
  # alternative for AB
  AB2 = math.sqrt((g2_ox-g1_ox)**2+(g2_oy-g1_oy)**2)
  if(abs(AB2-AB)>radian_epsilon):
    print("ERR314: Error with the calculation of AB {:0.3f} or {:0.3f}".format(AB, AB2))
    sys.exit(2)
  #KL = math.sqrt(AB**2 - (g1_br*(1+float(g2_n)/g1_n))**2) # kind of pythagor
  #KL = math.sqrt(AB**2 - (g1_br+g2_br)**2) # kind of pythagor
  KL = math.sin(real_force_angle)*AB
  #print("dbg631: KL {:0.5f}".format(KL))
  ## g1 related
  # get the angle of the closest middle of addendum to the contact point
  aa = ai_g1_position + g1_primitive_offset - ai_g1g2_a
  while(abs(aa)>g1_pi_module_angle/2+radian_epsilon):
    if(aa>0):
      aa = aa - g1_pi_module_angle
    else:
      aa = aa + g1_pi_module_angle
  contact_g1_tooth_angle = aa - g1_primitive_offset + ai_g1g2_a
  contact_g1_tooth_relative_angle = aa - g1_primitive_offset # relative to the inter-axis
  # g1_involute_offset_angle (see the documentation for the exact definition)
  #g1_involute_offset_angle = contact_g1_tooth_relative_angle + g1_involute_offset
  # g1_contact_u : involute parameter for g1 of the contact point
  #g1_contact_u = real_force_angle + ai_rotation_direction*g1_involute_offset_angle
  g1_contact_u = real_force_angle + ai_rotation_direction * g1_ks * (contact_g1_tooth_relative_angle + g1_involute_offset)
  #print("dbg558: g1_involute_offset {:0.3f}  contact_g1_tooth_relative_angle {:0.3f}  real_force_angle {:0.3f}".format(g1_involute_offset, contact_g1_tooth_relative_angle, g1_involute_offset))
  # contact point coordinates (method 1)
  (cx, cy, ti) = sample_of_gear_tooth_profile((g1_ox, g1_oy), g1_br, contact_g1_tooth_angle+g1_involute_offset, -1*g1_ks*ai_rotation_direction, 0, g1_contact_u)
  #print("dbg858: contact point (method1): cx: {:0.2f}  cy: {:0.2f}  ti: {:0.2f}".format(cx, cy, ti))
  ## triangle ABC
  # length of AC
  AC = math.sqrt((cx-g1_ox)**2+(cy-g1_oy)**2)
  # length of BC
  BC = math.sqrt((cx-g2_ox)**2+(cy-g2_oy)**2)
  # angle CBA
  if(AC+BC==AB):
  #if(abs(AC+BC-AB)<radian_epsilon):
    print("WARN468: Warning, the triangle ABC is flat")
    BAC = 0
    ABC = 0
  elif(AC+BC<AB):
    print("ERR478: Error of length in the triangle ABC")
    sys.exit(20)
  else:
    # law of cosinus (Al-Kashi) in ABC
    BAC = math.acos(float(AB**2+AC**2-BC**2)/(2*AB*AC))
    ABC = math.acos(float(AB**2+BC**2-AC**2)/(2*AB*BC))
    #print("dbg569: BAC {:0.3f}   ABC {:0.3f}".format(BAC, ABC))
    BAC = math.fmod(BAC+5*math.pi/2, math.pi)-math.pi/2
    ABC = math.fmod(ABC+5*math.pi/2, math.pi)-math.pi/2
    # alternative
    xAB = math.atan2(g2_oy-g1_oy, g2_ox-g1_ox)
    xAC = math.atan2(cy-g1_oy, cx-g1_ox)
    #BAC2 = math.fmod(xAC-xAB+5*math.pi, 2*math.pi)-math.pi
    BAC2 = math.fmod(xAC-xAB+9*math.pi/2, math.pi)-math.pi/2
    xBA = math.atan2(g1_oy-g2_oy, g1_ox-g2_ox)
    xBC = math.atan2(cy-g2_oy, cx-g2_ox)
    #ABC2 = math.fmod(xBC-xBA+5*math.pi, 2*math.pi)-math.pi
    ABC2 = math.fmod(xBC-xBA+9*math.pi/2, math.pi)-math.pi/2
    #print("dbg557: xBA {:0.3f}  xBC {:0.3f}".format(xBA, xBC))
    # sign BAC, ABC
    #if(BAC2<0):
    #  BAC = -1*BAC
    #  ABC = -1*ABC
    BAC = math.copysign(BAC, BAC2)
    ABC = -1*g1_ks*g2_ks* math.copysign(ABC, BAC2)
    # check BAC and BAC2
    if(abs(BAC2-BAC)>radian_epsilon):
      print("ERR689: Error in the calculation of BAC {:0.3f} or BAC2 {:0.3f} !".format(BAC, BAC2))
      sys.exit(2)
    # check ABC and ABC2
    if(abs(ABC2-ABC)>radian_epsilon):
      print("ERR688: Error in the calculation of ABC {:0.3f} or ABC2 {:0.3f} !".format(ABC, ABC2))
      sys.exit(2)
  #print("dbg334: BAC: {:0.3f}".format(BAC))
  #print("dbg335: ABC: {:0.3f}".format(ABC))
  ## speed / radial angle
  g1_sra = ai_rotation_direction*g1_ks*real_force_angle+BAC
  g2_sra = ai_rotation_direction*g1_ks*real_force_angle+ABC
  # alternative
  g1_sra2 = ai_rotation_direction*g1_ks*math.atan(g1_contact_u)
  if(abs(g1_sra2-g1_sra)>radian_epsilon):
    print("ERR414: Error in calculation of g1_sra {:0.3f} or g1_sra2 {:0.3f}".format(g1_sra, g1_sra2))
    sys.exit(2)
  ## speed of c1 (contact point of g1)
  # c1 speed
  c1_speed = AC*g1_rotation_speed
  c1_speed_radial = c1_speed*math.cos(g1_sra)
  c1_speed_tangential = c1_speed*math.sin(g1_sra)
  ### g2_position, g2_contact_u, c2x, c2y, c2_speed_radial, c2_speed, c2_speed_tangential, g2_rotation_speed
  if((g2_gear_type=='e')or(g2_gear_type=='i')):
    ## g2_contact_u : involute parameter for g2 of the contact point
    # several mathods:
    #g2_contact_u1 = float(KL - g1_contact_u*g1_br)/g2_br
    g2_contact_u1 = g1_ks*float(KL - g2_ks*g1_contact_u*g1_br)/g2_br
    g2_contact_u2 = math.tan(abs(g2_sra))
    g2_contact_u3 = math.sqrt((float(BC)/g2_br)**2-1)
    if(abs(g2_contact_u2-g2_contact_u1)>radian_epsilon):
      print("ERR331: Error in the calculation of g2_contact_u1 {:0.3f} or g2_contact_u2 {:0.3f}".format(g2_contact_u1, g2_contact_u2))
      sys.exit(2)
    if(abs(g2_contact_u3-g2_contact_u1)>radian_epsilon):
      print("ERR332: Error in the calculation of g2_contact_u1 {:0.3f} or g2_contact_u3 {:0.3f}".format(g2_contact_u1, g2_contact_u3))
      sys.exit(2)
    g2_contact_u = g2_contact_u1 # select the method for g2_contact_u
    ## c2_position
    #g2_position = ai_g1g2_a + math.pi - ai_rotation_direction*(real_force_angle - g2_contact_u) - g2_involute_offset
    g2_position = ai_g1g2_a + (1+g1_ks*g2_ks)/2*math.pi - ai_rotation_direction*g1_ks*(real_force_angle - g2_contact_u) - g2_involute_offset
    # c2 coordinates
    (c2x, c2y, t2i) = sample_of_gear_tooth_profile((g2_ox, g2_oy), g2_br, g2_position+g2_involute_offset, -1*ai_rotation_direction*g1_ks, 0, g2_contact_u)
    if(abs(math.fmod(ti-t2i, math.pi/2))>radian_epsilon):
      print("ERR874: Error, the tangents ti {:0.3f} and ti2 {:0.3f} are not equal (modulo pi)".format(ti, t2i))
      sys.exit(2)
    #print("dbg632: g2_ox {:0.3f}  g2_oy {:0.3f}  g2_br {:0.3f}".format(g2_ox, g2_oy, g2_br))
    ## speed of c2 (contact point of g2)
    c2_speed_radial = c1_speed_radial
    c2_speed = float(c2_speed_radial)/math.cos(g2_sra)
    c2_speed_tangential = c2_speed*math.sin(g2_sra)
    # alternative
    c2_speed_tangential2 = ai_rotation_direction*g1_ks*c2_speed_radial*g2_contact_u
    if(abs(c2_speed_tangential2-c2_speed_tangential)>radian_epsilon):
      print("ERR336: Error in the calculation of c2_speed_tangential {:0.3f} or c2_speed_tangential2 {:0.3f}".format(c2_speed_tangential, c2_speed_tangential2))
      sys.exit(2)
    g2_rotation_speed = float(c2_speed)/BC
  elif(g2_gear_type=='l'): # linear-gear (aka gearbar)
    g2_contact_u = g1_contact_u*g1_br-KL
    g2_position = g2_contact_u/math.cos(g2_sa) - g2_involute_offset
    c2y = -1*g2_contact_u*math.sin(g2_sa)
    c2x = g2_position + g2_involute_offset + c2y*math.tan(g2_sa)
    if(abs(math.fmod(ti - (-1*ai_rotation_direction*g2_sa), math.pi/2))>radian_epsilon):
      print("ERR875: Error, the tangents ti {:0.3f} and slope g2_sa {:0.3f} are not equal (modulo pi)".format(ti, g2_sa))
      sys.exit(2)
    c2_speed_radial = c1_speed_radial
    c2_speed = float(c2_speed_radial)/math.cos(g2_sa)
    c2_speed_tangential = c2_speed*math.sin(g2_sa)
    g2_rotation_speed = c2_speed
  # friction between g1 and g2
  tangential_friction = c2_speed_tangential - c1_speed_tangential
  ## speed outline
  # scale the outline
  scaled_c1_speed_radial = c1_speed_radial*speed_scale # *g1_module *g1_pr ???
  scaled_c1_speed_tangential = c1_speed_tangential*speed_scale
  scaled_c2_speed_radial = c2_speed_radial*speed_scale # *g2_module *g2_pr ???
  scaled_c2_speed_tangential = c2_speed_tangential*speed_scale
  # normal-tangential reference frame
  nxa = ti+ai_rotation_direction*math.pi/2
  txa = nxa+math.pi/2
  #
  c1rx = cx+scaled_c1_speed_radial*math.cos(nxa)
  c1ry = cy+scaled_c1_speed_radial*math.sin(nxa)
  c1_speed_outline = ((cx, cy), # contact point
    (c1rx, c1ry), # c1 radial speed
    (c1rx+scaled_c1_speed_tangential*math.cos(txa), c1ry+scaled_c1_speed_tangential*math.sin(txa)), # c1 tangential speed
    (cx, cy)) # close
  c2rx = c2x+scaled_c2_speed_radial*math.cos(nxa)
  c2ry = c2y+scaled_c2_speed_radial*math.sin(nxa)
  c2_speed_outline = ((c2x, c2y),
    (c2rx, c2ry), # c2 radial speed
    (c2rx+scaled_c2_speed_tangential*math.cos(txa), c2ry+scaled_c2_speed_tangential*math.sin(txa)), # c2 tangential speed
    (c2x, c2y)) # close
  # return
  r_position = (g2_position, g2_rotation_speed, tangential_friction, c1_speed_outline, c2_speed_outline)
  return(r_position)

def info_on_real_force_angle(ai_g1_param, ai_g2_param, ai_sys_param, ai_rotation_direction):
  """ Analytic calculation to check the real_force_angle (including the additional_inter_axis_length) and the force_path_length
  """
  ### positive_rotation
  # external / external : negative_involute / negative_involute
  # external / internal : negative_involute / negative_involute
  # internal / external : positive_involute / positive_involute # exception !
  # external / linear   : negative_involute / negative_involute
  # linear   / external : negative_involute / negative_involute
  if(ai_rotation_direction==1):
    rotation_name = 'Positive'
  elif(ai_rotation_direction==-1):
    rotation_name = 'Negative'
  else:
    print("ERR663: Error, ai_rotation_direction {:d} can only be 1 or -1!".format(ai_rotation_direction))
    sys.exit(2)
  # get the interesting high-level parameters
  rd = ai_rotation_direction
  g1_type = ai_g1_param['gear_type']
  g1_sign = ai_g1_param['gear_sign']
  g1_n    = ai_g1_param['full_tooth_nb']
  g1_pr   = ai_g1_param['primitive_radius']
  g1_ar   = ai_g1_param['addendum_radius']
  g1_ah   = ai_g1_param['addendum_height']
  g1_bl   = ai_g1_param['gearbar_length']
  g1_ox   = ai_g1_param['center_ox']
  g1_oy   = ai_g1_param['center_oy']
  g2_type = ai_g2_param['gear_type']
  g2_sign = ai_g2_param['gear_sign']
  g2_n    = ai_g2_param['full_tooth_nb']
  g2_pr   = ai_g2_param['primitive_radius']
  g2_ar   = ai_g2_param['addendum_radius']
  g2_ah   = ai_g2_param['addendum_height']
  g2_bl   = ai_g2_param['gearbar_length']
  g2_ox   = ai_g2_param['center_ox']
  g2_oy   = ai_g2_param['center_oy']
  g1g2_a  = ai_sys_param['g1g2_angle']
  aal     = ai_sys_param['additional_inter_axis_length']
  if(rd*g1_sign==1):
    involute_name = 'Negative'
    g1_br = ai_g1_param['negative_base_radius']
    g2_br = ai_g2_param['negative_base_radius']
    g1_sa = ai_g1_param['negative_slope_angle']
    g2_sa = ai_g2_param['negative_slope_angle']
  else:
    involute_name = 'Positive'
    g1_br = ai_g1_param['positive_base_radius']
    g2_br = ai_g2_param['positive_base_radius']
    g1_sa = ai_g1_param['positive_slope_angle']
    g2_sa = ai_g2_param['positive_slope_angle']
  # start creating the info text
  r_info = ""
  #r_info += "Info on Real Force Angle {:s}:\n".format(rotation_name)
  #print("dbg311: ai_g1_br:", ai_g1_br)
  # depending on gear_type
  #real_force_angle = math.acos(float(ai_g1_br*(ai_g1_n+ai_g2_n))/((ai_g1_pr+ai_g2_pr+ai_aal)*ai_g1_n))
  real_force_angle = calc_real_force_angle(g1_type, g1_pr, g1_br, g2_type, g2_pr, g2_br, aal, g1_sa, g2_sa)
  #r_info += "{:s} Real Force Angle = {:0.2f} radian ({:0.2f} degree)\n".format(rotation_name, real_force_angle, real_force_angle*180/math.pi)
  # coordinate of C (intersection of axis-line and force-line)
  #AC = float((ai_g1_pr+ai_g2_pr+ai_aal)*ai_g1_n)/(ai_g1_n+ai_g2_n)
  AC = g1_br/math.cos(real_force_angle)
  CX = g1_ox + math.cos(g1g2_a)*AC
  CY = g1_oy + math.sin(g1g2_a)*AC
  # force line equation
  real_force_inclination = g1g2_a + rd*(math.pi/2 - real_force_angle) # angle (Ox, force)
  Flx = math.sin(real_force_inclination)
  Fly = -1*math.cos(real_force_inclination)
  Fk = -1*(Flx*CX+Fly*CY)
  # F2: intersection of the force line and the addendum_circle_1
  if((g1_type=='e')or(g1_type=='i')):
    S2X = CX + g1_pr/g1_n*math.cos(g1g2_a+rd*math.pi/2) # S2: define the side of the intersection line-circle
    S2Y = CY + g1_pr/g1_n*math.sin(g1g2_a+rd*math.pi/2)
    (F2X,F2Y, line_circle_intersection_status) = small_geometry.line_circle_intersection((Flx, Fly, Fk), (g1_ox, g1_oy), g1_ar, (S2X,S2Y), real_force_inclination, "F2 calcultation")
    if(line_circle_intersection_status==2):
      print("ERR125: Error with the intersection of the force line and the addendum_circle_1")
      sys.exit(2)
  elif(g1_type=='l'):
    LX = g1_ox+g1_ah*math.cos(g1g2_a)
    LY = g1_oy+g1_ah*math.sin(g1g2_a)
    Blx = math.sin(g1g2_a+math.pi/2)
    Bly = -1*math.cos(g1g2_a+math.pi/2)
    Bk = -1*(Blx*LX+Bly*LY)
    (F2X, F2Y, line_line_intersection_status) = small_geometry.line_line_intersection((Flx, Fly, Fk), (Blx, Bly, Bk), "F2 calcultation with gearbar")
    if(line_line_intersection_status==2):
      print("ERR127: Error with the intersection of the force line and the gearbar addendum line")
      sys.exit(2)
  # F1: intersection of the force line and the addendum_circle_2
  if((g2_type=='e')or(g2_type=='i')):
    S1X = CX + g2_pr/g2_n*math.cos(g1g2_a-rd*math.pi/2) # S1: define the side of the intersection line-circle
    S1Y = CY + g2_pr/g2_n*math.sin(g1g2_a-rd*math.pi/2)
    (F1X,F1Y, line_circle_intersection_status) = small_geometry.line_circle_intersection((Flx, Fly, Fk), (g2_ox, g2_oy), g2_ar, (S1X,S1Y), real_force_inclination+math.pi, "F1 calcultation")
    if(line_circle_intersection_status==2):
      print("ERR126: Error with the intersection of the force line and the addendum_circle_2")
      sys.exit(2)
  elif(g2_type=='l'):
    LX = g2_ox+g1_ah*math.cos(g1g2_a+math.pi)
    LY = g2_oy+g1_ah*math.sin(g1g2_a+math.pi)
    Blx = math.sin(g1g2_a+math.pi/2)
    Bly = -1*math.cos(g1g2_a+math.pi/2)
    Bk = -1*(Blx*LX+Bly*LY)
    (F1X, F1Y, line_line_intersection_status) = small_geometry.line_line_intersection((Flx, Fly, Fk), (Blx, Bly, Bk), "F1 calcultation with gearbar")
    if(line_line_intersection_status==2):
      print("ERR129: Error with the intersection of the force line and the gearbar addendum line")
      sys.exit(2)
  ### action_line_outline
  r_action_line_outline = ((F1X, F1Y), (F2X, F2Y))
  # length of F1F2
  F1F2 = math.sqrt((F2X-F1X)**2+(F2Y-F1Y)**2)
  #r_info += "length of the tooth {:s} contact path: {:0.2f}\n".format(involute_name, F1F2)
  r_info += "{:s} rotation, {:s}-{:s} involute {:s}. Real Force Angle = {:0.2f} radian ({:0.2f} degree). Contact path length: {:0.2f}\n".format(rotation_name, g1_type, g2_type, involute_name, real_force_angle, real_force_angle*180/math.pi, F1F2)
  # angle (F1AF2)
  if((g1_type=='e')or(g1_type=='i')):
    AF1 = float(math.sqrt((F1X-g1_ox)**2+(F1Y-g1_oy)**2))
    xAF1 = math.atan2((F1Y-g1_oy)/AF1, (F1X-g1_ox)/AF1)
    AF2 = float(g1_ar)
    xAF2 = math.atan2((F2Y-g1_oy)/AF2, (F2X-g1_ox)/AF2)
    F1AF2 = abs(math.fmod(xAF2-xAF1+5*math.pi, 2*math.pi)-math.pi)
    F1AF2p = F1AF2*g1_n/(2*math.pi)
    r_info += "tooth {:s} contact path angle from gearwheel1: {:0.2f} radian ({:0.2f} degree) {:0.2f}% of tooth length\n".format(involute_name, F1AF2, F1AF2*180/math.pi, F1AF2p*100)
  elif(g1_type=='l'):
    F1F2t = F1F2*math.cos(g1_sa)
    F1F2p = float(F1F2t)*g1_n/g1_bl
    r_info += "tooth {:s} contact path from gearbar1 tangential length {:0.2f} (mm) {:0.2f}% of tooth length\n".format(involute_name, F1F2t, F1F2p*100)
  # angle (F1EF2)
  if((g2_type=='e')or(g2_type=='i')):
    EF2 = float(math.sqrt((F2X-g2_ox)**2+(F2Y-g2_oy)**2))
    xEF2 = math.atan2((F2Y-g2_oy)/EF2, (F2X-g2_ox)/EF2)
    EF1 = float(g2_ar)
    xEF1 = math.atan2((F1Y-g2_oy)/EF1, (F1X-g2_ox)/EF1)
    F1EF2 = abs(math.fmod(xEF2-xEF1+5*math.pi, 2*math.pi)-math.pi)
    F1EF2p = F1EF2*g2_n/(2*math.pi)
    r_info += "tooth {:s} contact path angle from gearwheel2: {:0.2f} radian ({:0.2f} degree) {:0.2f}% of tooth length\n".format(involute_name, F1EF2, F1EF2*180/math.pi, F1EF2p*100)
  elif(g2_type=='l'):
    F1F2t = F1F2*math.cos(g2_sa)
    F1F2p = float(F1F2t)*g2_n/g2_bl
    r_info += "tooth {:s} contact path from gearbar2 tangential length {:0.2f} (mm) {:0.2f}% of tooth length\n".format(involute_name, F1F2t, F1F2p*100)
  # return
  r_iorfa = (r_info, r_action_line_outline)
  return(r_iorfa)

def gear_high_level_parameter_to_text(ai_prefix_txt, ai_param):
  """ Create a string that contains the gear high-level parameters
  """
  r_txt = "\n"
  r_txt += ai_prefix_txt+"\n"
  r_txt += "gear_type:                \t{:s}\t".format(ai_param['gear_type'])
  r_txt += "tooth_nb:                 \t{:d}\n".format(ai_param['full_tooth_nb'])
  r_txt += "gear_module:              \t{:0.3f}\n".format(ai_param['module'])
  r_txt += "primitive radius:         \t{:0.3f}   \tdiameter: {:0.3f}\n".format(ai_param['primitive_radius'], 2*ai_param['primitive_radius'])
  r_txt += "addendum-dedendum parity: \t{:0.2f} %\n".format(100*ai_param['addendum_dedendum_parity'])
  r_txt += "tooth half height:        \t{:0.3f}\n".format(ai_param['tooth_half_height'])
  r_txt += "positive base radius:     \t{:0.3f}   \tdiameter: {:0.3f}\n".format(ai_param['positive_base_radius'], 2*ai_param['positive_base_radius'])
  r_txt += "negative base radius:     \t{:0.3f}   \tdiameter: {:0.3f}\n".format(ai_param['negative_base_radius'], 2*ai_param['negative_base_radius'])
  r_txt += "addendum radius:          \t{:0.3f}   \tdiameter: {:0.3f}\n".format(ai_param['addendum_radius'], 2*ai_param['addendum_radius'])
  r_txt += "dedendum radius:          \t{:0.3f}   \tdiameter: {:0.3f}\n".format(ai_param['dedendum_radius'], 2*ai_param['dedendum_radius'])
  r_txt += "gear hollow radius:       \t{:0.3f}   \tdiameter: {:0.3f}\n".format(ai_param['hollow_radius'], 2*ai_param['hollow_radius'])
  r_txt += "router-bit radius:        \t{:0.3f}   \tdiameter:  {:0.3f}\n".format(ai_param['gear_router_bit_radius'], 2*ai_param['gear_router_bit_radius'])
  r_txt += "gear center (x, y):       \t{:0.3f}   \t {:0.3f}\n".format(ai_param['center_ox'], ai_param['center_oy'])
  r_txt += "profile resolution (positive, negative):       \t{:d}     \t{:d}\n".format(ai_param['positive_involute_resolution'], ai_param['negative_involute_resolution'])
  r_txt += "profile skin thickness (positive, negative):   \t{:0.3f}  \t{:0.3f}\n".format(ai_param['positive_skin_thickness'], ai_param['negative_skin_thickness'])
  r_txt += "gear portion:   \ttooth_nb: {:d}   \tstart: {:d}  \tstop: {:d}\n".format(ai_param['portion_tooth_nb'], ai_param['portion_first_end'], ai_param['portion_last_end'])
  r_txt += "first tooth position angle:   \t{:0.3f} (radian)  \t{:0.3f} (degree)\n".format(ai_param['initial_angle'], ai_param['initial_angle']*180/math.pi)
  r_txt += "linear gear: inclination: {:0.3f} (radian)  {:0.3f} (degree)  positive slope: {:0.3f} (radian)  {:0.3f} (degree)  negative slope: {:0.3f} (radian)  {:0.3f}\n".format(ai_param['gearbar_inclination'], ai_param['gearbar_inclination']*180/math.pi, ai_param['positive_slope_angle'], ai_param['positive_slope_angle']*180/math.pi, ai_param['negative_slope_angle'], ai_param['negative_slope_angle']*180/math.pi)
  return(r_txt)


################################################################
# the most important function to be used in other scripts
################################################################

def gear_profile(
      ### first gear
      # general
      ai_gear_type = 'e',
      ai_gear_tooth_nb = 0,
      ai_gear_module = 0.0,
      ai_gear_primitive_diameter = 0.0,
      ai_gear_addendum_dedendum_parity = 50.0,
      # tooth height
      ai_gear_tooth_half_height = 0.0,
      ai_gear_addendum_height_pourcentage = 100.0,
      ai_gear_dedendum_height_pourcentage = 100.0,
      ai_gear_hollow_height_pourcentage = 25.0,
      ai_gear_router_bit_radius = 0.1,
      # positive involute
      ai_gear_base_diameter = 0.0,
      ai_gear_force_angle = 0.0,
      ai_gear_tooth_resolution = 3,
      ai_gear_skin_thickness = 0.0,
      # negative involute (if zero, negative involute = positive involute)
      ai_gear_base_diameter_n = 0.0,
      ai_gear_force_angle_n = 0.0,
      ai_gear_tooth_resolution_n = 0,
      ai_gear_skin_thickness_n = 0.0,
      ### second gear
      # general
      ai_second_gear_type = 'e',
      ai_second_gear_tooth_nb = 0,
      ai_second_gear_primitive_diameter = 0.0,
      ai_second_gear_addendum_dedendum_parity = 0.0,
      # tooth height
      ai_second_gear_tooth_half_height = 0.0,
      ai_second_gear_addendum_height_pourcentage = 100.0,
      ai_second_gear_dedendum_height_pourcentage = 100.0,
      ai_second_gear_hollow_height_pourcentage = 25.0,
      ai_second_gear_router_bit_radius = 0.0,
      # positive involute
      ai_second_gear_base_diameter = 0.0,
      ai_second_gear_tooth_resolution = 0,
      ai_second_gear_skin_thickness = 0.0,
      # negative involute (if zero, negative involute = positive involute)
      ai_second_gear_base_diameter_n = 0.0,
      ai_second_gear_tooth_resolution_n = 0,
      ai_second_gear_skin_thickness_n = 0.0,
      ### gearbar specific
      ai_gearbar_slope = 0.0,
      ai_gearbar_slope_n = 0.0,
      ### position
      # first gear position
      ai_center_position_x = 0.0,
      ai_center_position_y = 0.0,
      ai_gear_initial_angle = 0.0,
      # second gear position
      ai_second_gear_position_angle = 0.0,
      ai_second_gear_additional_axis_length = 0.0,
      ### portion
      ai_portion_tooth_nb = 0,
      ai_portion_first_end = 0,
      ai_portion_last_end =0,
      ### output
      ai_gear_profile_height = 1.0,
      ai_simulation_enable = False,
      ai_output_file_basename = ''):
  """
  The main function of the script.
  It generates a gear_profile according to the function arguments
  """
  ## epsilon for rounding
  radian_epsilon = math.pi/1000
  ##### gear-profile high-level parameters
  g1_param = {}   # first gear high-level parameters
  g2_param = {}   # second gear high-level parameters
  sys_param = {}  # gear-system high-level parameters
  # gear_type
  # g1_type
  if((ai_gear_type=='e')or(ai_gear_type=='i')or(ai_gear_type=='l')):
    g1_type = ai_gear_type
  else:
    print("ERR111: Error, the gear_type {:s} is not valid!".format(ai_gear_type))
    sys.exit(2)
  # g2_type
  if((ai_second_gear_type=='e')or(ai_second_gear_type=='i')or(ai_second_gear_type=='l')):
    g2_type = ai_second_gear_type
  else:
    print("ERR511: Error, the gear_type {:s} is not valid!".format(ai_second_gear_type))
    sys.exit(2)
  # check of the type cross compatibility
  if((g1_type=='i')and(g2_type!='e')):
    print("ERR512: Error, internal gear is only compatible with external gear. g1_type: {:s}  g2_type: {:s}".format(g1_type, g2_type))
    sys.exit(2)
  if((g1_type=='l')and(g2_type!='e')):
    print("ERR512: Error, linear gear is only compatible with external gear. g1_type: {:s}  g2_type: {:s}".format(g1_type, g2_type))
    sys.exit(2)
  g1_param['gear_type'] = g1_type
  g2_param['gear_type'] = g2_type
  # tooth_nb
  g1_n = ai_gear_tooth_nb
  if(g1_n==0):
    print("ERR112: Error, the gear_tooth_nb must be set!")
    sys.exit(2)
  if(g1_n<3):
    print("ERR113: Error, the gear_tooth_nb {:d} must be equal or bigger than 3!".format(g1_n))
    sys.exit(2)
  g2_n = ai_second_gear_tooth_nb
  g2_exist = False
  if(g2_n!=0):
    g2_exist = True
  if(g2_exist and (g1_n<3)):
    print("ERR114: Error, the second_gear_tooth_nb {:d} must be equal or bigger than 3!".format(g2_n))
    sys.exit(2)
  #g1_param['gear_exist'] = True
  #g2_param['gear_exist'] = g2_exist
  sys_param['second_gear_exist'] = g2_exist
  g1_param['full_tooth_nb'] = g1_n
  g2_param['full_tooth_nb'] = g2_n
  # module
  g1_m = 1
  g1_m_set = False
  if(ai_gear_module>0):
    g1_m = ai_gear_module
    g1_m_set = True
  if(ai_gear_primitive_diameter>0):
    if(g1_m_set):
      print("ERR115: Error, the gear_module is already set to {:0.2f}!".format(g1_m))
      sys.exit(2)
    else:
      if((g1_type=='i')or(g1_type=='e')):
        g1_m = float(ai_gear_primitive_diameter)/g1_n
      elif(g1_type=='l'):
        g1_m = float(ai_gear_primitive_diameter)/g1_n/math.pi
      g1_m_set = True
  if(ai_second_gear_primitive_diameter>0):
    if(not g2_exist):
      print("ERR116: Error, set second_gear_tooth_nb to use second_gear_primitive_diameter")
      sys.exit(2)
    elif(g1_m_set):
      print("ERR117: Error, the gear_module is already set to {:0.2f}!".format(g1_m))
      sys.exit(2)
    else:
      if((g2_type=='i')or(g2_type=='e')):
        g1_m = float(ai_second_gear_primitive_diameter)/g2_n
      elif(g2_type=='l'):
        g1_m = float(ai_second_gear_primitive_diameter)/g2_n/math.pi
      g1_m_set = True
  g2_m = g1_m
  g1_param['module'] = g1_m
  g2_param['module'] = g2_m
  g1_param['pi_module'] = g1_m * math.pi
  g2_param['pi_module'] = g2_m * math.pi
  # primitive radius
  g1_pr = 0
  if((g1_type=='i')or(g1_type=='e')):
    g1_pr = float(g1_m*g1_n)/2
  g2_pr = 0
  if((g2_type=='i')or(g2_type=='e')):
    g2_pr = float(g2_m*g2_n)/2
  g1_param['primitive_radius'] = g1_pr
  g2_param['primitive_radius'] = g2_pr
  # addendum_dedendum_parity
  g1_adp = float(ai_gear_addendum_dedendum_parity)/100
  if((g1_adp<=0)or(g1_adp>=1)):
    print("ERR118: Error, the gear_addendum_dedendum_parity {:0.2f} must be set strictly between 0% and 100%!".format(ai_gear_addendum_dedendum_parity))
    sys.exit(2)
  g2_adp = 1-g1_adp
  if(ai_second_gear_addendum_dedendum_parity>0):
    if(not g2_exist):
      print("ERR119: Error, set second_gear_tooth_nb to use second_gear_addendum_dedendum_parity")
      sys.exit(2)
    else:
      print("WARN211: Warning, second_gear_addendum_dedendum_parity is used for irregular cases.")
      g2_adp = ai_second_gear_addendum_dedendum_parity
  if((g2_adp<=0)or(g2_adp>=1)):
    print("ERR119: Error, the second_gear_addendum_dedendum_parity {:0.2f} must be set strictly between 0% and 100%!".format(ai_second_gear_addendum_dedendum_parity))
    sys.exit(2)
  g1_param['addendum_dedendum_parity'] = g1_adp
  g2_param['addendum_dedendum_parity'] = g2_adp
  # inter-axis additional length
  aal = ai_second_gear_additional_axis_length
  if(aal>0):
    if(not g2_exist):
      print("ERR120: Error, set second_gear_tooth_nb to use second_gear_additional_axis_length")
      sys.exit(2)
    else:
      print("WARN212: Warning, second_gear_additional_axis_length is used for irregular cases.")
  sys_param['additional_inter_axis_length'] = aal
  ### tooth_height
  # external / linear :  hollow < dedendum < primitive < addendum
  # internal          :  addendum < primitive < dedendum < hollow
  # addendum_sign
  g1_as = -1 if(g1_type=='i') else 1
  g2_as = -1 if(g2_type=='i') else 1
  # position_coefficient
  g1_pc = 0 if(g1_type=='l') else 1
  g2_pc = 0 if(g2_type=='l') else 1
  g1_param['gear_sign'] = g1_as
  g2_param['gear_sign'] = g2_as
  g1_param['position_coefficient'] = g1_pc
  g2_param['position_coefficient'] = g2_pc
  g1_param['center_to_reference_length'] = g1_as * g1_pc * g1_pr
  g2_param['center_to_reference_length'] = g2_as * g2_pc * g2_pr
  # g1
  g1_thh = g1_m
  if(ai_gear_tooth_half_height>0):
    g1_thh = ai_gear_tooth_half_height
  g1_a_delta = g1_thh*float(ai_gear_addendum_height_pourcentage)/100 # addendum delta
  g1_d_delta = g1_thh*float(ai_gear_dedendum_height_pourcentage)/100 # dedendum delta
  g1_ar = g1_pr + g1_as*g1_a_delta # addendum radius
  g1_dr = g1_pr - g1_as*g1_d_delta # dedendum radius
  g1_small_r = min(g1_ar, g1_dr) # small radius
  g1_big_r = max(g1_ar, g1_dr) # big radius
  # g2
  g2_thh = g2_m
  if(ai_second_gear_tooth_half_height>0):
    g2_thh = ai_second_gear_tooth_half_height
  g2_a_delta = g2_thh*float(ai_second_gear_addendum_height_pourcentage)/100 # addendum delta
  g2_d_delta = g2_thh*float(ai_second_gear_dedendum_height_pourcentage)/100 # dedendum delta
  g2_ar = g2_pr + g2_as*g2_a_delta # addendum radius
  g2_dr = g2_pr - g2_as*g2_d_delta # dedendum radius
  g2_small_r = min(g2_ar, g2_dr) # small radius
  g2_big_r = max(g2_ar, g2_dr) # big radius
  if(g1_a_delta>aal+g2_d_delta):
    print("WARN213: Warning, the addendum {:0.2f} of the first gear is too big, other the dedendum {:0.2f} of the other gear is too small (second_gear_additional_axis_length={:0.2f})!".format(g1_a_delta, g2_d_delta, aal))
  if(g2_a_delta>aal+g1_d_delta):
    print("WARN214: Warning, the addendum {:0.2f} of the second gear is too big, other the dedendum {:0.2f} of the other gear is too small (second_gear_additional_axis_length={:0.2f})!".format(g2_a_delta, g1_d_delta, aal))
  if(g1_a_delta+g2_a_delta<aal):
    print("WARN215: Warning, the (second_gear_additional_axis_length {:0.2f} is too big compare to the addendum {:0.2f} and {:0.2f}!".format(aal, g1_a_delta, g2_a_delta))
  g1_param['tooth_half_height'] = g1_thh # g1
  g1_param['addendum_height']   = g1_a_delta
  g1_param['dedendum_height']   = g1_d_delta
  g1_param['addendum_radius']   = g1_ar
  g1_param['dedendum_radius']   = g1_dr
  g1_param['smaller_radius']    = g1_small_r
  g1_param['bigger_radius']     = g1_big_r
  g1_param['real_tooth_hight']  = g1_a_delta + g1_d_delta
  g2_param['tooth_half_height'] = g2_thh # g2
  g2_param['addendum_height']   = g2_a_delta
  g2_param['dedendum_height']   = g2_d_delta
  g2_param['addendum_radius']   = g2_ar
  g2_param['dedendum_radius']   = g2_dr
  g2_param['smaller_radius']    = g2_small_r
  g2_param['bigger_radius']     = g2_big_r
  g2_param['real_tooth_hight']  = g2_a_delta + g2_d_delta
  ### base radius
  # positive involute : positive_base_radius
  g1_brp = g1_small_r
  g1_brp_set = False
  if(ai_gear_base_diameter>0):
    g1_brp = ai_gear_base_diameter
    g1_brp_set = True
  if(ai_second_gear_base_diameter>0):
    if(not g2_exist):
      print("ERR121: Error, set second_gear_tooth_nb to use second_gear_base_diameter")
      sys.exit(2)
    elif(g1_brp_set):
      print("ERR122: Error, gear_base_diameter is already set to {:0.2f}".format(g1_brp*2))
      sys.exit(2)
    else:
      g1_brp = float(ai_second_gear_base_diameter*g1_n)/g2_n
      g1_brp_set = True
  if(ai_gear_force_angle>0):
    if(g1_brp_set):
      print("ERR123: Error, gear_base_diameter is already set to {:0.2f}".format(g1_brp*2))
      sys.exit(2)
    else:
      g1_brp = g1_pr*math.cos(ai_gear_force_angle)
      g1_brp_set = True
  g2_brp = float(g1_brp*g2_n)/g1_n
  # negative involute : negative_base_radius
  g1_brn = g1_brp
  g1_brn_set = False
  if(ai_gear_base_diameter_n>0):
    g1_brn = ai_gear_base_diameter_n
    g1_brn_set = True
  if(ai_second_gear_base_diameter_n>0):
    if(not g2_exist):
      print("ERR121: Error, set second_gear_tooth_nb to use second_gear_base_diameter_n")
      sys.exit(2)
    elif(g1_brn_set):
      print("ERR122: Error, gear_base_diameter_n is already set to {:0.2f}".format(g1_brn*2))
      sys.exit(2)
    else:
      g1_brn = float(ai_second_gear_base_diameter_n*g1_n)/g2_n
      g1_brn_set = True
  if(ai_gear_force_angle_n>0):
    if(g1_brn_set):
      print("ERR123: Error, gear_base_diameter is already set to {:0.2f}".format(g1_brn*2))
      sys.exit(2)
    else:
      g1_brn = g1_pr*math.cos(ai_gear_force_angle_n)
      g1_brn_set = True
  g2_brn = float(g1_brn*g2_n)/g1_n
  # base radius check
  if((g1_type=='e')or(g1_type=='i')):
    if(g1_brp>g1_small_r):
      print("WARN216: Warning, g1_brp {:0.2f} is bigger than g1_small_r {:0.2f}".format(g1_brp, g1_small_r))
    if(g1_brn>g1_small_r):
      print("WARN246: Warning, g1_brn {:0.2f} is bigger than g1_small_r {:0.2f}".format(g1_brn, g1_small_r))
    if(g1_brp!=g1_brn):
      print("WARN218: Warning, g1_brp {:0.2f} and g1_brn {:0.2f} are different. The gear_tooth are asymmetrical!".format(g1_brp, g1_brn))
    if(g1_brp>g1_big_r):
      print("ERR616: Error, g1_brp {:0.2f} is bigger than g1_big_r {:0.2f}".format(g1_brp, g1_big_r))
      sys.exit(2)
    if(g1_brn>g1_big_r):
      print("ERR646: Error, g1_brn {:0.2f} is bigger than g1_big_r {:0.2f}".format(g1_brn, g1_big_r))
      sys.exit(2)
  if((g2_type=='e')or(g2_type=='i')):
    if(g2_exist and (g2_brp>g2_small_r)):
      print("WARN217: Warning, g2_brp {:0.2f} is bigger than g2_small_r {:0.2f}".format(g2_brp, g2_small_r))
    if(g2_exist and (g2_brn>g2_small_r)):
      print("WARN247: Warning, g2_brn {:0.2f} is bigger than g2_small_r {:0.2f}".format(g2_brn, g2_small_r))
    if(g2_exist and (g2_brp>g2_big_r)):
      print("ERR617: Error, g2_brp {:0.2f} is bigger than g2_big_r {:0.2f}".format(g2_brp, g2_big_r))
      sys.exit(2)
    if(g2_exist and (g2_brn>g2_big_r)):
      print("ERR647: Error, g2_brn {:0.2f} is bigger than g2_big_r {:0.2f}".format(g2_brn, g2_big_r))
      sys.exit(2)
  g1_param['positive_base_radius'] = g1_brp
  g2_param['positive_base_radius'] = g2_brp
  g1_param['negative_base_radius'] = g1_brn
  g2_param['negative_base_radius'] = g2_brn
  ## linear gear base_radius = slope angle
  # g1_sp g1_sn
  g1_sp = 0
  g1_sp_set = False
  g1_sn = 0
  g1_sn_set = False
  if(ai_gear_type=='l'):
    if(ai_gearbar_slope>0):
      g1_sp = ai_gearbar_slope
      g1_sp_set = True
    if(ai_gear_force_angle>0):
      if(not g1_sp_set):
        g1_sp = ai_gear_force_angle
        g1_sp_set = True
    if(not g1_sp_set):
      print("ERR541: Error, the slope angle of the linear gear 1 is not set!")
      sys.exit(2)
    g1_sn = g1_sp
    g1_sn_set = False
    if(ai_gearbar_slope_n>0):
      g1_sn = ai_gearbar_slope_n
      g1_sn_set = True
    if(ai_gear_force_angle_n>0):
      if(not g2_sn_set):
        g1_sn = ai_gear_force_angle_n
        g1_sn_set = True
  g1_param['positive_slope_angle'] = g1_sp
  g1_param['negative_slope_angle'] = g1_sn
  # g2_sp g2_sn
  g2_sp = 0
  g2_sp_set = False
  g2_sn = 0
  g2_sn_set = False
  if(ai_second_gear_type=='l'):
    if(ai_gearbar_slope>0):
      g2_sp = ai_gearbar_slope
      g2_sp_set = True
    if(ai_gear_force_angle>0):
      if(not g2_sp_set):
        g2_sp = ai_gear_force_angle
        g2_sp_set = True
    if(not g2_sp_set):
      print("ERR542: Error, the slope angle of the linear gear 2 is not set!")
      sys.exit(2)
    g2_sn = g2_sp
    g2_sn_set = False
    if(ai_gearbar_slope_n>0):
      g2_sn = ai_gearbar_slope_n
      g2_sn_set = True
    if(ai_gear_force_angle_n>0):
      if(not g2_sn_set):
        g2_sn = ai_gear_force_angle_n
        g2_sn_set = True
  g2_param['positive_slope_angle'] = g2_sp
  g2_param['negative_slope_angle'] = g2_sn
  # initial position
  g1_ia = ai_gear_initial_angle
  g1_ix = ai_center_position_x
  g1_iy = ai_center_position_y
  g1g2_a = ai_second_gear_position_angle
  g2_ia = 0 # will be computed later
  inter_axis_length = g1_pc*g1_pr+(g1_as*g2_as)*g2_pc*g2_pr+g1_as*aal
  g2_ix = g1_ix + inter_axis_length*math.cos(g1g2_a)
  g2_iy = g1_iy + inter_axis_length*math.sin(g1g2_a)
  g1_param['center_ox']     = g1_ix
  g1_param['center_oy']     = g1_iy
  g1_param['initial_angle'] = g1_ia
  g2_param['center_ox']     = g2_ix
  g2_param['center_oy']     = g2_iy
  g2_param['initial_angle'] = g2_ia
  sys_param['g1g2_angle'] = g1g2_a
  sys_param['inter_axis_length'] = inter_axis_length
  # router_bit radius
  g1_rbr = ai_gear_router_bit_radius
  g2_rbr = g1_rbr
  if(ai_second_gear_router_bit_radius>0):
    if(not g2_exist):
      print("ERR124: Error, set second_gear_tooth_nb to use second_gear_router_bit_radius")
      sys.exit(2)
    else:
      g2_rbr = ai_second_gear_router_bit_radius
  g1_param['gear_router_bit_radius'] = g1_rbr
  g2_param['gear_router_bit_radius'] = g2_rbr
  # hollow
  g1_h_delta = g1_thh*float(ai_gear_hollow_height_pourcentage)/100
  if(g1_h_delta<g1_rbr):
    print("WARN218: Warning, g1_h_delta {:0.2f} is smaller than the router_bit_radius {:0.2f}. gear_hollow_height_pourcentage {:0.2f} should be set to {:0.2f}".format(g1_h_delta, g1_rbr, ai_gear_hollow_height_pourcentage, 100.0*g1_rbr/g1_thh))
    g1_h_delta = g1_rbr + 10*radian_epsilon
  g2_h_delta = g2_thh*float(ai_second_gear_hollow_height_pourcentage)/100
  if(g2_exist):
    if(g2_h_delta<g2_rbr):
      print("WARN219: Warning, g2_h_delta {:0.2f} is smaller than the second_router_bit_radius {:0.2f}. second_gear_hollow_height_pourcentage {:0.2f} should be set to {:0.2f}".format(g2_h_delta, g2_rbr, ai_second_gear_hollow_height_pourcentage, 100.0*g2_rbr/g2_thh))
      g2_h_delta = g2_rbr + 10*radian_epsilon
  g1_hr = g1_dr - g1_as*g1_h_delta
  g2_hr = g2_dr - g2_as*g2_h_delta
  g1_param['hollow_height'] = g1_h_delta
  g1_param['hollow_radius'] = g1_hr
  g2_param['hollow_height'] = g2_h_delta
  g2_param['hollow_radius'] = g2_hr
  # involute resolution
  g1_irp = ai_gear_tooth_resolution
  g1_irn = g1_irp
  if(ai_gear_tooth_resolution_n>0):
    g1_irn = ai_gear_tooth_resolution_n
  g2_irp = g1_irp
  if(ai_second_gear_tooth_resolution>0):
    g2_irp = ai_second_gear_tooth_resolution
  g2_irn = g2_irp
  if(ai_second_gear_tooth_resolution_n>0):
    g2_irn = ai_second_gear_tooth_resolution_n
  g1_param['positive_involute_resolution'] = g1_irp
  g1_param['negative_involute_resolution'] = g1_irn
  g2_param['positive_involute_resolution'] = g2_irp
  g2_param['negative_involute_resolution'] = g2_irn
  # skin_thickness
  g1_stp = ai_gear_skin_thickness
  g1_stn = g1_stp
  if(ai_gear_skin_thickness_n!=0):
    g1_stn = ai_gear_skin_thickness_n
  g2_stp = g1_stp
  if(ai_second_gear_skin_thickness!=0):
    g2_stp = ai_second_gear_skin_thickness
  g2_stn = g2_stp
  if(ai_second_gear_skin_thickness_n!=0):
    g2_stn = ai_second_gear_skin_thickness_n
  g1_param['positive_skin_thickness'] = g1_stp
  g1_param['negative_skin_thickness'] = g1_stn
  g2_param['positive_skin_thickness'] = g2_stp
  g2_param['negative_skin_thickness'] = g2_stn
  # portion
  g1_ptn = 0 # 0: full first gear
  g1_pfe = 0
  g1_ple = 0
  if(ai_portion_tooth_nb>1): # cut a portion of the first gear
    if(((g1_type=='e')or(g1_type=='i'))and(ai_portion_tooth_nb>=g1_n)):
      print("ERR553: Error, the portion {:d} of gearwheel is bigger than the maximal number of teeth {:d}!".format(ai_portion_tooth_nb, g1_n))
      sys.exit(2)
    g1_ptn = ai_portion_tooth_nb
    g1_pfe = ai_portion_first_end
    g1_ple = ai_portion_last_end
  g2_ptn = 0 # full second gear
  g2_pfe = 0
  g2_ple = 0
  g1_param['portion_tooth_nb']  = g1_ptn
  g1_param['portion_first_end'] = g1_pfe
  g1_param['portion_last_end']  = g1_ple
  g2_param['portion_tooth_nb']  = g2_ptn
  g2_param['portion_first_end'] = g2_pfe
  g2_param['portion_last_end']  = g2_ple
  # bar inclination (make only sense for the gearbar)
  g1_bi = g1g2_a
  g2_bi = g1g2_a + math.pi
  g1_param['gearbar_inclination']  = g1_bi
  g2_param['gearbar_inclination']  = g2_bi
  g1_param['gearbar_length']  = g1_n * g1_m * math.pi
  g2_param['gearbar_length']  = g2_n * g2_m * math.pi
  #
  #print("dbg341: g1_param:", g1_param)
  #print("dbg342: g2_param:", g2_param)
  #print("dbg343: sys_param:", sys_param)
  ## end of the construction of the high-level parameters

  ## compute the real_force_angle and the tooth_contact_path
  if(g2_exist):
    (real_force_info_p, positive_rotation_action_line_outline) = info_on_real_force_angle(g1_param, g2_param, sys_param,  1)
    (real_force_info_n, negative_rotation_action_line_outline) = info_on_real_force_angle(g1_param, g2_param, sys_param, -1)
    real_force_info = "Real force info:\n" + real_force_info_p + real_force_info_n

  ### generate the first gear outline
  (g1_make_low_param, g1_place_low_param, g1_info_low) = calc_low_level_gear_parameters(g1_param)
  g1_outline_B = gear_profile_outline(g1_make_low_param, g1_ia)
  # output info
  parameter_info_txt1 = gear_high_level_parameter_to_text("Gear-profile 1:", g1_param)
  parameter_info_txt1 += g1_info_low
  #print(parameter_info_txt1)

  ### simulation
  if(ai_simulation_enable):
    print("Launch the simulation with Tkinter ..")
    # initialization
    g1_ideal_involute = ideal_tooth_outline(g1_make_low_param, g1_ia, 0)
    g1_ideal_tooth = ideal_tooth_outline(g1_make_low_param, g1_ia, 1)
    parameter_info_txt = parameter_info_txt1
    if(g2_exist):
      #print("dbg369: Prepare the second gear ..")
      #print("dbg521: g2_high_parameters:", g2_high_parameters)
      g2_ia = 0
      (g2_make_low_param, g2_place_low_param, g2_info_low) = calc_low_level_gear_parameters(g2_param)
      #print("dbg653: g2_make_low_param:", g2_make_low_param)
      g2_outline_B = gear_profile_outline(g2_make_low_param, g2_ia)
      # output info
      parameter_info_txt2 = "\nGear system: ratio: {:0.3f}\n g1g2_a: {:0.3f}  \tadditional inter-axis length: {:0.3f}\n".format(float(g1_n)/g2_n, g1g2_a, aal)
      parameter_info_txt2 += real_force_info
      parameter_info_txt3 = gear_high_level_parameter_to_text("Gear-profile 2:", g2_param)
      parameter_info_txt3 += g2_info_low
      #print(parameter_info_txt2 + parameter_info_txt3)
      parameter_info_txt += parameter_info_txt2 + parameter_info_txt3
      #print("dbg689: g2_outline_B is ready")
    ### gear_profile parameter info in the log
    print(parameter_info_txt)
    ### static figure
    inter_axis_outline = ((g1_ix, g1_iy), (g2_ix, g2_iy))
    ### matplotlib curve table
    g1_position_curve_table = []
    g2_position_curve_table = []
    g2_rotation_speed_curve_table = []
    tangential_friction_curve_table = []
    # initialization to avoid strange matplotlib representation (particularly on g2_rotation_speed)
    #g1_position_curve_table.append(0.0)
    #g2_position_curve_table.append(0.0)
    #g2_rotation_speed_curve_table.append(1.0)
    #tangential_friction_curve_table.append(0.0)
    ### start Tkinter
    tk_root = Tkinter.Tk()
    my_canvas = cnc25d_api.Two_Canvas(tk_root)
    # callback functions for display_backend
    def sub_canvas_graphics(ai_rotation_direction, ai_angle_position):
      """ create the graphics and fill-up the matplotlib curve tables
      """
      #global g1_position_curve_table, g2_position_curve_table, g2_rotation_speed_curve_table, tangential_friction_curve_table # no need of global because just append element to lists
      ## gear position
      # g1_position
      g1_position = g1_ia+ai_angle_position
      ## get outline_B
      lg1_outline_B = gear_profile_outline(g1_make_low_param, g1_position)
      lg1_ideal_involute = ideal_tooth_outline(g1_make_low_param, g1_position, 0)
      lg1_ideal_tooth = ideal_tooth_outline(g1_make_low_param, g1_position, 1)
      if(g2_exist):
        # g2_position
        #g2_position = g2_ia-ai_angle_position # completely wrong, just waiting for the good formula
        g2_position_calcultion_stuff = g2_position_calcultion(g1_place_low_param, g2_place_low_param, ai_rotation_direction, g1_position, aal, g1g2_a)
        (g2_position, g2_rotation_speed, tangential_friction, c1_speed_outline, c2_speed_outline) = g2_position_calcultion_stuff
        lg2_outline_B = gear_profile_outline(g2_make_low_param, g2_position)
        lg2_ideal_involute = ideal_tooth_outline(g2_make_low_param, g2_position, 0)
        lg2_ideal_tooth = ideal_tooth_outline(g2_make_low_param, g2_position, 1)
        # action_line
        if(ai_rotation_direction==1):
          action_line_outline = positive_rotation_action_line_outline
        else:
          action_line_outline = negative_rotation_action_line_outline
      ## alternative to get outline_B
      #lg1_outline_B = cnc25d_api.outline_rotate(g1_outline_B, g1_ix, g1_iy, ai_angle_position)
      #lg1_ideal_involute = cnc25d_api.outline_rotate(g1_ideal_involute, g1_ix, g1_iy, ai_angle_position)
      #lg1_ideal_tooth = cnc25d_api.outline_rotate(g1_ideal_tooth, g1_ix, g1_iy, ai_angle_position)
      #if(g2_exist):
      #  lg2_outline_B = cnc25d_api.outline_rotate(g2_outline_B, g2_ix, g2_iy, -ai_angle_position)
      ## make graphic
      r_canvas_graphics = []
      r_canvas_graphics.append(('graphic_lines', cnc25d_api.outline_arc_line(lg1_outline_B, 'tkinter'), 'red', 1))
      r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line(lg1_ideal_involute, 'tkinter'), 'green', 1))
      r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line(lg1_ideal_tooth, 'tkinter'), 'blue', 1))
      if(g2_exist):
        r_canvas_graphics.append(('graphic_lines', cnc25d_api.outline_arc_line(lg2_outline_B, 'tkinter'), 'grey', 1))
        r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line(lg2_ideal_involute, 'tkinter'), 'green', 1))
        r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line(lg2_ideal_tooth, 'tkinter'), 'blue', 1))
        # speed overlay
        r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line(c1_speed_outline, 'tkinter'), 'yellow', 1))
        r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line(c2_speed_outline, 'tkinter'), 'orange', 1))
        # action line
        r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line(action_line_outline, 'tkinter'), 'brown', 1))
        # debug
        #r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line((g1_ix, g1_iy, g1_brp), 'tkinter'), 'brown', 1))
        #r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line((g1_ix, g1_iy, g1_brn), 'tkinter'), 'brown', 1))
        #r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line((g2_ix, g2_iy, g2_brp), 'tkinter'), 'brown', 1))
        #r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line((g2_ix, g2_iy, g2_brn), 'tkinter'), 'brown', 1))
        #r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line((g1_ix, g1_iy, g1_ar), 'tkinter'), 'green', 1))
        #r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line((g2_ix, g2_iy, g2_ar), 'tkinter'), 'green', 1))
      # inter-axis
      r_canvas_graphics.append(('overlay_lines', cnc25d_api.outline_arc_line(inter_axis_outline, 'tkinter'), 'green', 1))
      ## update matplotlib curve_table
      if(g2_exist):
        #print("dbg554: g1_position: {:0.3f}  g2_position: {:0.3f}  g2_rotation_speed: {:0.3f}  tangential_friction: {:0.3f}".format(g1_position, g2_position, g2_rotation_speed, tangential_friction))
        g1_position_curve_table.append(g1_position)
        g2_position_curve_table.append(g2_position)
        g2_rotation_speed_curve_table.append(g2_rotation_speed)
        tangential_friction_curve_table.append(tangential_friction)
        # to avoid the matplotlib exponential scale
        if(len(g2_rotation_speed_curve_table)==1):
          g2_rotation_speed_curve_table[0] = 1.01*g2_rotation_speed_curve_table[0]
      return(r_canvas_graphics)
    # matplotlib stuff
    gear_profile_mpl_curves = (('gear-profile analysis\n(with g1_rotation_speed = 1 radian/s)', 'g1_position_angle (simulation iteration)', 1),
      ('g1\nposition\n(radian)', g1_position_curve_table, 'gx'),
      ('g2\nposition\n(radian)', g2_position_curve_table, 'r+'),
      ('g2\nrotation_speed\n(radian/s)', g2_rotation_speed_curve_table, 'y.'),
      ('tangential\nfriction\n(mm/s)', tangential_friction_curve_table, 'bo'))
    # end of callback functions
    my_canvas.add_canvas_graphic_function(sub_canvas_graphics)
    my_canvas.add_parameter_info(parameter_info_txt)
    my_canvas.add_curve_graphic_table(gear_profile_mpl_curves)
    tk_root.mainloop()
    del (my_canvas, tk_root) # because Tkinter could be used again later in this script

  ### output files
  gp_figure = [g1_outline_B] # select the outlines to be writen in files
  cnc25d_api.generate_output_file(gp_figure, ai_output_file_basename, ai_gear_profile_height)

  r_gp = (g1_outline_B, g1_param, parameter_info_txt1)
  return(r_gp)

################################################################
# gear_profile argparse_to_function
################################################################

def gear_profile_argparse_wrapper(ai_gp_args):
  """
  wrapper function of gear_profile() to call it using the gear_profile_parser.
  gear_profile_parser is mostly used for debug and non-regression tests.
  """
  # run the simulation as default action
  run_simulation = False
  if(ai_gp_args.sw_simulation_enable or (ai_gp_args.sw_output_file_basename=='')):
    run_simulation = True
  #
  #print("dbg865: ai_gp_args.sw_second_gear_skin_thickness:", ai_gp_args.sw_second_gear_skin_thickness)
  # wrapper
  r_gp = gear_profile(
                      ### first gear
                      # general
                      ai_gear_type                      = ai_gp_args.sw_gear_type,
                      ai_gear_tooth_nb                  = ai_gp_args.sw_gear_tooth_nb,
                      ai_gear_module                    = ai_gp_args.sw_gear_module,
                      ai_gear_primitive_diameter        = ai_gp_args.sw_gear_primitive_diameter,
                      ai_gear_addendum_dedendum_parity  = ai_gp_args.sw_gear_addendum_dedendum_parity,
                      # tooth height
                      ai_gear_tooth_half_height           = ai_gp_args.sw_gear_tooth_half_height,
                      ai_gear_addendum_height_pourcentage = ai_gp_args.sw_gear_addendum_height_pourcentage,
                      ai_gear_dedendum_height_pourcentage = ai_gp_args.sw_gear_dedendum_height_pourcentage,
                      ai_gear_hollow_height_pourcentage   = ai_gp_args.sw_gear_hollow_height_pourcentage,
                      ai_gear_router_bit_radius           = ai_gp_args.sw_gear_router_bit_radius,
                      # positive involute
                      ai_gear_base_diameter       = ai_gp_args.sw_gear_base_diameter,
                      ai_gear_force_angle         = ai_gp_args.sw_gear_force_angle,
                      ai_gear_tooth_resolution    = ai_gp_args.sw_gear_tooth_resolution,
                      ai_gear_skin_thickness      = ai_gp_args.sw_gear_skin_thickness,
                      # negative involute (if zero, negative involute = positive involute)
                      ai_gear_base_diameter_n     = ai_gp_args.sw_gear_base_diameter_n,
                      ai_gear_force_angle_n       = ai_gp_args.sw_gear_force_angle_n,
                      ai_gear_tooth_resolution_n  = ai_gp_args.sw_gear_tooth_resolution_n,
                      ai_gear_skin_thickness_n    = ai_gp_args.sw_gear_skin_thickness_n,
                      ### second gear
                      # general
                      ai_second_gear_type                     = ai_gp_args.sw_second_gear_type,
                      ai_second_gear_tooth_nb                 = ai_gp_args.sw_second_gear_tooth_nb,
                      ai_second_gear_primitive_diameter       = ai_gp_args.sw_second_gear_primitive_diameter,
                      ai_second_gear_addendum_dedendum_parity = ai_gp_args.sw_second_gear_addendum_dedendum_parity,
                      # tooth height
                      ai_second_gear_tooth_half_height            = ai_gp_args.sw_second_gear_tooth_half_height,
                      ai_second_gear_addendum_height_pourcentage  = ai_gp_args.sw_second_gear_addendum_height_pourcentage,
                      ai_second_gear_dedendum_height_pourcentage  = ai_gp_args.sw_second_gear_dedendum_height_pourcentage,
                      ai_second_gear_hollow_height_pourcentage    = ai_gp_args.sw_second_gear_hollow_height_pourcentage,
                      ai_second_gear_router_bit_radius            = ai_gp_args.sw_second_gear_router_bit_radius,
                      # positive involute
                      ai_second_gear_base_diameter      = ai_gp_args.sw_second_gear_base_diameter,
                      ai_second_gear_tooth_resolution   = ai_gp_args.sw_second_gear_tooth_resolution,
                      ai_second_gear_skin_thickness     = ai_gp_args.sw_second_gear_skin_thickness,
                      # negative involute (if zero, negative involute = positive involute)
                      ai_second_gear_base_diameter_n    = ai_gp_args.sw_second_gear_base_diameter_n,
                      ai_second_gear_tooth_resolution_n = ai_gp_args.sw_second_gear_tooth_resolution_n,
                      ai_second_gear_skin_thickness_n   = ai_gp_args.sw_second_gear_skin_thickness_n,
                      ### gearbar specific
                      ai_gearbar_slope                  = ai_gp_args.sw_gearbar_slope,
                      ai_gearbar_slope_n                = ai_gp_args.sw_gearbar_slope_n,
                      ### position
                      # first gear position
                      ai_center_position_x                    = ai_gp_args.sw_center_position_x,
                      ai_center_position_y                    = ai_gp_args.sw_center_position_y,
                      ai_gear_initial_angle                   = ai_gp_args.sw_gear_initial_angle,
                      # second gear position
                      ai_second_gear_position_angle           = ai_gp_args.sw_second_gear_position_angle,
                      ai_second_gear_additional_axis_length    = ai_gp_args.sw_second_gear_additional_axis_length,
                      ### portion
                      ai_portion_tooth_nb     = ai_gp_args.sw_cut_portion[0],
                      ai_portion_first_end    = ai_gp_args.sw_cut_portion[1],
                      ai_portion_last_end     = ai_gp_args.sw_cut_portion[2],
                      ### output
                      ai_gear_profile_height  = ai_gp_args.sw_gear_profile_height,
                      ai_simulation_enable    = run_simulation,    # ai_gp_args.sw_simulation_enable,
                      ai_output_file_basename = ai_gp_args.sw_output_file_basename)
  return(r_gp)

################################################################
# self test
################################################################

def gear_profile_self_test():
  """
  This is the non-regression test of gear_profile.
  Look at the simulation Tk window to check errors.
  """
  test_case_switch = [
    ["simplest test"                                    , ""],
    ["simplest test with simulation"                    , "--simulation_enable"],
    ["simple reduction (ratio<1)"                       , "--second_gear_tooth_nb 21 --simulation_enable"],
    ["simple transmission (ratio=1)"                    , "--gear_tooth_nb 13 --second_gear_tooth_nb 13 --simulation_enable"],
    ["simple multiplication (ratio>1)"                  , "--gear_tooth_nb 19 --second_gear_tooth_nb 16 --simulation_enable"],
    ["big ratio and zoom"                               , "--gear_tooth_nb 19 --second_gear_tooth_nb 137 --simulation_zoom 4.0 --simulation_enable"],
    ["single gear with same primitive and base circle"  , "--gear_tooth_nb 17 --gear_base_diameter 17.0 --simulation_enable"],
    ["single gear with small base circle"               , "--gear_tooth_nb 27 --gear_base_diameter 23.5 --simulation_enable"],
    ["with first and second angle and inter-axis length" , "--second_gear_tooth_nb 21 --gear_initial_angle {:f} --second_gear_position_angle {:f} --second_gear_additional_axis_length 0.2 --simulation_enable".format(15*math.pi/180, 40.0*math.pi/180)],
    ["other with first and second angle"                , "--second_gear_tooth_nb 15 --gear_initial_angle  {:f} --second_gear_position_angle  {:f} --simulation_enable".format(-5*math.pi/180, 170.0*math.pi/180)],
    ["with force angle constraint"                      , "--gear_tooth_nb 17 --second_gear_tooth_nb 27 --gear_force_angle {:f} --simulation_enable".format(20*math.pi/180)],
    ["first base radius constraint"                     , "--gear_tooth_nb 26 --second_gear_tooth_nb 23 --gear_base_diameter 23.0 --simulation_enable"],
    ["second base radius constraint"                    , "--second_gear_tooth_nb 23 --second_gear_primitive_diameter 20.3 --simulation_enable"],
    ["fine draw resolution"                             , "--second_gear_tooth_nb 19 --gear_tooth_resolution 10 --simulation_enable"],
    ["ratio 1 and dedendum at 30%%"                     , "--second_gear_tooth_nb 17 --gear_dedendum_height_pourcentage 30.0 --second_gear_addendum_height_pourcentage 30.0 --simulation_enable"],
    ["ratio > 1 and dedendum at 40%%"                   , "--second_gear_tooth_nb 23 --gear_dedendum_height_pourcentage 40.0 --second_gear_addendum_height_pourcentage 40.0 --simulation_enable"],
    ["ratio > 1 and addendum at 80%%"                   , "--second_gear_tooth_nb 17 --gear_addendum_height_pourcentage 80.0 --second_gear_dedendum_height_pourcentage 80.0 --simulation_enable"],
    ["ratio > 1 and dedendum at 160%%"                  , "--second_gear_tooth_nb 21 --gear_dedendum_height_pourcentage 160.0 --simulation_enable"],
    ["ratio > 1 and small tooth height"                 , "--second_gear_tooth_nb 29 --gear_tooth_half_height 1.3 --second_gear_tooth_half_height 1.3 --simulation_enable"],
    ["ratio > 1 and big tooth height"                   , "--second_gear_tooth_nb 29 --gear_tooth_half_height 2.3 --second_gear_tooth_half_height 2.3 --simulation_enable"],
    ["ratio > 1 and addendum-dedendum parity"           , "--gear_tooth_nb 30 --second_gear_tooth_nb 37 --gear_addendum_dedendum_parity 60.0 --second_gear_addendum_dedendum_parity 40.0 --simulation_enable"],
    ["file generation"                                  , "--center_position_x 100 --center_position_y 50 --output_file_basename self_test_output/"],
    ["interior gear"                                    , "--second_gear_tooth_nb 14 --gear_type ie --simulation_enable"],
    ["interior gear"                                    , "--gear_tooth_nb 25 --second_gear_tooth_nb 17 --gear_type ie --second_gear_position_angle {:f} --simulation_enable".format(30.0*math.pi/180)],
    ["interior second gear"                             , "--second_gear_tooth_nb 29 --gear_type ei --simulation_enable"],
    ["interior second gear"                             , "--second_gear_tooth_nb 24 --gear_type ei --second_gear_position_angle {:f} --simulation_enable".format(-75*math.pi/180)],
    ["interior gear"                                    , "--second_gear_tooth_nb 14 --gear_type ie --gear_addendum_height_pourcentage 75.0 --simulation_enable"],
    ["gearbar"                                     , "--gear_type ce --gear_tooth_nb 3 --second_gear_tooth_nb 20 --gear_primitive_diameter 15 --gear_base_diameter 20 --simulation_enable"],
    ["gearbar with angle"                          , "--gear_type ce --gear_tooth_nb 12 --second_gear_tooth_nb 20 --gear_primitive_diameter 40 --gear_base_diameter 20 --gear_initial_angle {:f} --simulation_enable".format(40*math.pi/180)]]
  #print("dbg741: len(test_case_switch):", len(test_case_switch))
  gear_profile_parser = argparse.ArgumentParser(description='Command line interface for the function gear_profile().')
  gear_profile_parser = gear_profile_add_argument(gear_profile_parser, 0)
  gear_profile_parser = cnc25d_api.generate_output_file_add_argument(gear_profile_parser)
  for i in range(len(test_case_switch)):
    l_test_switch = test_case_switch[i][1]
    print("{:2d} test case: '{:s}'\nwith switch: {:s}".format(i, test_case_switch[i][0], l_test_switch))
    l_args = l_test_switch.split()
    #print("dbg414: l_args:", l_args)
    st_args = gear_profile_parser.parse_args(l_args)
    r_gpst = gear_profile_argparse_wrapper(st_args)
  return(r_gpst)

################################################################
# gear_profile command line interface
################################################################

def gear_profile_cli(ai_args=None):
  """ command line interface of gear_profile.py when it is used in standalone
  """
  # gear_profile parser
  gear_profile_parser = argparse.ArgumentParser(description='Command line interface for the function gear_profile().')
  gear_profile_parser = gear_profile_add_argument(gear_profile_parser, 0)
  gear_profile_parser = cnc25d_api.generate_output_file_add_argument(gear_profile_parser)
  # add switch for self_test
  gear_profile_parser.add_argument('--run_self_test','--rst', action='store_true', default=False, dest='sw_run_self_test',
    help='Generate several corner cases of parameter sets and display the Tk window where you should check the gear running.')
  effective_args = cnc25d_api.get_effective_args(ai_args)
  gp_args = gear_profile_parser.parse_args(effective_args)
  print("dbg111: start making gear_profile")
  if(gp_args.sw_run_self_test):
    r_gp = gear_profile_self_test()
  else:
    r_gp = gear_profile_argparse_wrapper(gp_args)
  print("dbg999: end of script")
  return(r_gp)

################################################################
# main
################################################################

# this works with python and freecad :)
if __name__ == "__main__":
  FreeCAD.Console.PrintMessage("gear_profile.py says hello!\n")
  #my_gp = gear_profile_cli()
  #my_gp = gear_profile_cli("--gear_tooth_nb 17".split())
  #my_gp = gear_profile_cli("--gear_tooth_nb 17 --gear_module 10 --gear_router_bit_radius 3.0".split())
  my_gp = gear_profile_cli("--gear_tooth_nb 17 --gear_module 10 --gear_router_bit_radius 3.0 --second_gear_tooth_nb 20".split())
  #my_gp = gear_profile_cli("--gear_tooth_nb 17 --output_file_basename test_output/toto1".split())
  #my_gp = gear_profile_cli("--gear_tooth_nb 17 --output_file_basename gear_profile_example_1.svg".split())
  #my_gp = gear_profile_cli("--gear_tooth_nb 17 --cut_portion 7 3 3 --output_file_basename gear_profile_example_2.svg".split())
  #my_gp = gear_profile_cli("--gear_tooth_nb 20 --gear_force_angle {:0.3f} --gear_force_angle_n {:0.3f} --output_file_basename gear_profile_example_3.svg".format(25*math.pi/180, 35*math.pi/180,).split())


