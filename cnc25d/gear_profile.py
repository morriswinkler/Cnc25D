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
It's actually a single function with the design parameters as input.
The function writes STL, DXF and SVG files if an output basename is given as argument.
The function can also display a small Tk windows for gear simulation.
Finally, the backends used are: FreeCAD (for GUI rendering, STL and DXF export), mozman dxfwrite, mozman svgwrite and Tkinter.
The function return the gear-profile as FreeCAD Part object.
"""

################################################################
# header for Python / FreeCAD compatibility
################################################################

import cnc25d_api
cnc25d_api.importing_freecad()

#print("FreeCAD.Version:", FreeCAD.Version())
#FreeCAD.Console.PrintMessage("Hello from PrintMessage!\n") # avoid using this method because it is not printed in the FreeCAD GUI

################################################################
# import
################################################################

import math
import sys, argparse
from datetime import datetime
import os, errno
#
import Part
from FreeCAD import Base

################################################################
# gear_profile_argparse
################################################################

"""
The gear_profile_parser defines and structures the arguments of gear_profile().
It's mostly used for debug and non-regression test.
Argument default values are defined here.
"""
gear_profile_parser = argparse.ArgumentParser(description='Command line interface for the function gear_profile().')
# first gear_profile parameters
gear_profile_parser.add_argument('--gear_type','--gt', action='store', default='ee', dest='sw_gear_type',
  help="Select the type of gear. Possible values: 'ee', 'ie', 'ce', 'ei' and 'ce'. Default: 'ee'")
gear_profile_parser.add_argument('--gear_tooth_nb','--gtn', action='store', type=int, default=17, dest='sw_gear_tooth_nb',
  help="Set the number of teeth of the first gear_profile.")
gear_profile_parser.add_argument('--gear_module','--gm', action='store', type=float, default=1.0, dest='sw_gear_module',
  help="Set the module of the gear. It influences the gear_profile diameters.")
gear_profile_parser.add_argument('--gear_primitive_diameter','--gpd', action='store', type=float, default=0.0, dest='sw_gear_primitive_diameter',
  help="If not set to zero, redefine the gear module to get this primitive diameter of the first gear_profile. Default: 0. If cremailliere, it redefines the length.")
gear_profile_parser.add_argument('--gear_base_diameter','--gbd', action='store', type=float, default=0.0, dest='sw_gear_base_diameter',
  help="If not set to zero, redefine the base diameter of the first gear_profile. Default: 0. If cremailliere, it redefines the tooth slope angle.")
gear_profile_parser.add_argument('--gear_tooth_half_height','--gthh', action='store', type=float, default=0.0, dest='sw_gear_tooth_half_height',
  help="If not set to zero, redefine the tooth half height of the first gear_profile. Default: 0.0")
gear_profile_parser.add_argument('--gear_addendum_dedendum_parity','--gadp', action='store', type=float, default=50.0, dest='sw_gear_addendum_dedendum_parity',
  help="Set the addendum / dedendum parity of the first gear_profile. Default: 50.0%%")
gear_profile_parser.add_argument('--gear_addendum_height_pourcentage','--gahp', action='store', type=float, default=100.0, dest='sw_gear_addendum_height_pourcentage',
  help="Set the addendum height of the first gear_profile in pourcentage of the tooth half height. Default: 100.0%%")
gear_profile_parser.add_argument('--gear_dedendum_height_pourcentage','--gdhp', action='store', type=float, default=100.0, dest='sw_gear_dedendum_height_pourcentage',
  help="Set the dedendum height of the first gear_profile in pourcentage of the tooth half height. Default: 100.0%%")
gear_profile_parser.add_argument('--gear_hollow_height_pourcentage','--ghhp', action='store', type=float, default=25.0, dest='sw_gear_hollow_height_pourcentage',
  help="Set the hollow height of the first gear_profile in pourcentage of the tooth half height. Default: 25.0%%")
gear_profile_parser.add_argument('--gear_router_bit_radius','--grr', action='store', type=float, default=1.0, dest='sw_gear_router_bit_radius',
  help="Set the router_bit radius used to create the gear hollow of the first gear_profile. Default: 1.0")
gear_profile_parser.add_argument('--gear_initial_angle','--gia', action='store', type=float, default=0.0, dest='sw_gear_initial_angle',
  help="Set the gear reference angle (in Radian). Default: 0.0")
# gear contact parameters
gear_profile_parser.add_argument('--second_gear_position_angle','--sgpa', action='store', type=float, default=0.0, dest='sw_second_gear_position_angle',
  help="Angle in Radian that sets the postion on the second gear_profile. Default: 0.0")
gear_profile_parser.add_argument('--second_gear_additional_axe_length','--sgaal', action='store', type=float, default=0.0, dest='sw_second_gear_additional_axe_length',
  help="Set an additional value for the inter-axe length between the first and the second gear_profiles. Default: 0.0")
gear_profile_parser.add_argument('--gear_force_angle','--gfa', action='store', type=float, default=0.0, dest='sw_gear_force_angle',
  help="If not set to zero, redefine the second_gear_additional_axe_length to get this force angle at the gear contact. Default: 0.0")
# second gear_profile parameters
gear_profile_parser.add_argument('--second_gear_tooth_nb','--sgtn', action='store', type=int, default=17, dest='sw_second_gear_tooth_nb',
  help="Set the number of teeth of the second gear_profile.")
gear_profile_parser.add_argument('--second_gear_primitive_diameter','--sgpd', action='store', type=float, default=0.0, dest='sw_second_gear_primitive_diameter',
  help="If not set to zero, redefine the gear module to get this primitive diameter of the second gear_profile. Default: 0.0. If cremailliere, it redefines the length.")
gear_profile_parser.add_argument('--second_gear_base_diameter','--sgbd', action='store', type=float, default=0.0, dest='sw_second_gear_base_diameter',
  help="If not set to zero, redefine the base diameter of the second gear_profile. Default: 0.0. If cremailliere, it redefines the tooth slope angle.")
gear_profile_parser.add_argument('--second_gear_tooth_half_height','--sgthh', action='store', type=float, default=0.0, dest='sw_second_gear_tooth_half_height',
  help="If not set to zero, redefine the tooth half height of the second gear_profile. Default: 0.0")
gear_profile_parser.add_argument('--second_gear_addendum_dedendum_parity','--sgadp', action='store', type=float, default=50.0, dest='sw_second_gear_addendum_dedendum_parity',
  help="Set the addendum / dedendum parity of the second gear_profile. Default: 50.0%%")
gear_profile_parser.add_argument('--second_gear_addendum_height_pourcentage','--sgahp', action='store', type=float, default=100.0, dest='sw_second_gear_addendum_height_pourcentage',
  help="Set the addendum height of the second gear_profile in pourcentage of the tooth half height. Default: 100.0%%")
gear_profile_parser.add_argument('--second_gear_dedendum_height_pourcentage','--sgdhp', action='store', type=float, default=100.0, dest='sw_second_gear_dedendum_height_pourcentage',
  help="Set the dedendum height of the second gear_profile in pourcentage of the tooth half height. Default: 100.0%%")
gear_profile_parser.add_argument('--second_gear_hollow_height_pourcentage','--sghhp', action='store', type=float, default=25.0, dest='sw_second_gear_hollow_height_pourcentage',
  help="Set the hollow height of the second gear_profile in pourcentage of the tooth half height. Default: 25.0%%")
gear_profile_parser.add_argument('--second_gear_router_bit_radius','--sgrr', action='store', type=float, default=1.0, dest='sw_second_gear_router_bit_radius',
  help="Set the router_bit radius used to create the gear hollow of the second gear_profile. Default: 1.0")
# portion parameter
gear_profile_parser.add_argument('--portion_tooth_nb','--ptn', action='store', type=int, default=0, dest='sw_portion_tooth_nb',
  help="If not set to zero, cut a portion of the first gear_profile according to this portion tooth number. Default: 0")
# part split parameter
gear_profile_parser.add_argument('--part_split','--ps', action='store', type=int, default=1, dest='sw_part_split',
  help="Split the first gear_profile in N (=part_split) parts that can be glued together to create the gear wheel. Two series of N parts are created. N=1 doesn't split the gear_profile. Default: 1")
# center position parameters
gear_profile_parser.add_argument('--center_position_x','--cpx', action='store', type=float, default=0.0, dest='sw_center_position_x',
  help="Set the x-position of the first gear_profile center. Default: 0.0")
gear_profile_parser.add_argument('--center_position_y','--cpy', action='store', type=float, default=0.0, dest='sw_center_position_y',
  help="Set the y-position of the first gear_profile center. Default: 0.0")
# firt gear_profile extrusion (currently only linear extrusion is possible)
gear_profile_parser.add_argument('--gear_profile_height','--gwh', action='store', type=float, default=1.0, dest='sw_gear_profile_height',
  help="Set the height of the linear extrusion of the first gear_profile. Default: 1.0")
# manufacturing technology related
gear_profile_parser.add_argument('--gear_tooth_resolution','--gtr', action='store', type=int, default=3, dest='sw_gear_tooth_resolution',
  help="It sets the number of intermediate points of the gear tooth profile. Default: 3")
gear_profile_parser.add_argument('--gear_skin_thickness','--gst', action='store', type=float, default=0.0, dest='sw_gear_skin_thickness',
  help="Add or remove radial thickness on the gear tooth profile. Default: 0.0")
# simulation
gear_profile_parser.add_argument('--simulation_enable','--se', action='store_true', default=False, dest='sw_simulation_enable',
  help='It display a Tk window where you can observe the gear running. Check with your eyes if the geometry is working.')
# output
gear_profile_parser.add_argument('--output_file_basename','--ofb', action='store', default='', dest='sw_output_file_basename',
  help="If not set to the empty string (the default value), it generates a bunch of design files starting with this basename.")
# self_test
gear_profile_parser.add_argument('--self_test_enable','--ste', action='store_true', default=False, dest='sw_self_test_enable',
  help='Generate several corner cases of parameter sets and display the Tk window where you should check the gear running.')
    
################################################################
# the most important function to be used in other scripts
################################################################

def gear_profile(
      ai_gear_type,
      ai_gear_tooth_nb,
      ai_gear_module,
      ai_gear_primitive_diameter,
      ai_gear_base_diameter,
      ai_gear_tooth_half_height,
      ai_gear_addendum_dedendum_parity,
      ai_gear_addendum_height_pourcentage,
      ai_gear_dedendum_height_pourcentage,
      ai_gear_hollow_height_pourcentage,
      ai_gear_router_bit_radius,
      ai_gear_initial_angle,
      ai_second_gear_position_angle,
      ai_second_gear_additional_axe_length,
      ai_gear_force_angle,
      ai_second_gear_tooth_nb,
      ai_second_gear_primitive_diameter,
      ai_second_gear_base_diameter,
      ai_second_gear_tooth_half_height,
      ai_second_gear_addendum_dedendum_parity,
      ai_second_gear_addendum_height_pourcentage,
      ai_second_gear_dedendum_height_pourcentage,
      ai_second_gear_hollow_height_pourcentage,
      ai_second_gear_router_bit_radius,
      ai_portion_tooth_nb,
      ai_part_split,
      ai_center_position_x,
      ai_center_position_y,
      ai_gear_profile_height,
      ai_gear_tooth_resolution,
      ai_gear_skin_thickness,
      ai_simulation_enable,
      ai_output_file_basename):
  """
  The main function of the script.
  It generates a gear_profile according to the function arguments
  """
  ## check parameter coherence

  r_gw = 1
  return(r_gw)

################################################################
# gear_profile argparse_to_function
################################################################

def gear_profile_argparse(ai_gp_args):
  """
  wrapper function of gear_profile() to call it using the gear_profile_parser.
  gear_profile_parser is mostly used for debug and non-regression tests.
  """
  r_gp = gear_profile(
            ai_gp_args.sw_gear_type,
            ai_gp_args.sw_gear_tooth_nb,
            ai_gp_args.sw_gear_module,
            ai_gp_args.sw_gear_primitive_diameter,
            ai_gp_args.sw_gear_base_diameter,
            ai_gp_args.sw_gear_tooth_half_height,
            ai_gp_args.sw_gear_addendum_dedendum_parity,
            ai_gp_args.sw_gear_addendum_height_pourcentage,
            ai_gp_args.sw_gear_dedendum_height_pourcentage,
            ai_gp_args.sw_gear_hollow_height_pourcentage,
            ai_gp_args.sw_gear_router_bit_radius,
            ai_gp_args.sw_gear_initial_angle,
            ai_gp_args.sw_second_gear_position_angle,
            ai_gp_args.sw_second_gear_additional_axe_length,
            ai_gp_args.sw_gear_force_angle,
            ai_gp_args.sw_second_gear_tooth_nb,
            ai_gp_args.sw_second_gear_primitive_diameter,
            ai_gp_args.sw_second_gear_base_diameter,
            ai_gp_args.sw_second_gear_tooth_half_height,
            ai_gp_args.sw_second_gear_addendum_dedendum_parity,
            ai_gp_args.sw_second_gear_addendum_height_pourcentage,
            ai_gp_args.sw_second_gear_dedendum_height_pourcentage,
            ai_gp_args.sw_second_gear_hollow_height_pourcentage,
            ai_gp_args.sw_second_gear_router_bit_radius,
            ai_gp_args.sw_portion_tooth_nb,
            ai_gp_args.sw_part_split,
            ai_gp_args.sw_center_position_x,
            ai_gp_args.sw_center_position_y,
            ai_gp_args.sw_gear_profile_height,
            ai_gp_args.sw_gear_tooth_resolution,
            ai_gp_args.sw_gear_skin_thickness,
            ai_gp_args.sw_simulation_enable,
            ai_gp_args.sw_output_file_basename)
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
    ["with first and second angle and inter-axe length" , "--second_gear_tooth_nb 21 --gear_initial_angle {:f} --second_gear_position_angle {:f} --second_gear_additional_axe_length 0.2 --simulation_enable".format(15*math.pi/180, 40.0*math.pi/180)],
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
    ["cremailliere"                                     , "--gear_type ce --gear_tooth_nb 3 --second_gear_tooth_nb 20 --gear_primitive_diameter 15 --gear_base_diameter 20 --simulation_enable"],
    ["cremailliere with angle"                          , "--gear_type ce --gear_tooth_nb 12 --second_gear_tooth_nb 20 --gear_primitive_diameter 40 --gear_base_diameter 20 --gear_initial_angle {:f} --simulation_enable".format(40*math.pi/180)]]
  #print("dbg741: len(test_case_switch):", len(test_case_switch))
  for i in range(len(test_case_switch)):
    l_test_switch = test_case_switch[i][1]
    print("{:2d} test case: '{:s}'\nwith switch: {:s}".format(i, test_case_switch[i][0], l_test_switch))
    l_args = l_test_switch.split()
    #print("dbg414: l_args:", l_args)
    st_args = gear_profile_parser.parse_args(l_args)
    r_gpst = gear_profile_argparse(st_args)
  return(r_gpst)

################################################################
# gear_profile command line interface
################################################################

def gear_profile_cli():
  """ command line interface of gear_profile.py when it is used in standalone
  """
  # this ensure the possible to use the script with python and freecad
  # You can not use argparse and FreeCAD together, so it's actually useless !
  # Running this script, FreeCAD will just use the argparse default values
  arg_index_offset=0
  if(sys.argv[0]=='freecad'): # check if the script is used by freecad
    arg_index_offset=1
    if(len(sys.argv)>=2):
      if(sys.argv[1]=='-c'): # check if the script is used by freecad -c
        arg_index_offset=2
  effective_args = sys.argv[arg_index_offset+1:]
  #print("dbg115: effective_args:", str(effective_args))
  #FreeCAD.Console.PrintMessage("dbg116: effective_args: %s\n"%(str(effective_args)))
  gp_args = gear_profile_parser.parse_args(effective_args)
  print("dbg111: start making gear_profile")
  if(gp_args.sw_self_test_enable):
    r_gp = gear_profile_self_test()
  else:
    r_gp = gear_profile_argparse(gp_args)
  print("dbg999: end of script")
  return(r_gp)

################################################################
# main
################################################################

# this works with python and freecad :)
if __name__ == "__main__":
  FreeCAD.Console.PrintMessage("gear_profile.py says hello!\n")
  my_gw = gear_profile_cli()
  #Part.show(my_gw)

