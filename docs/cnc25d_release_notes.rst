====================
Cnc25D Release Notes
====================

Release 0.1.11
--------------
Released on 2014-03-31

* low_torque_transmission
* gearlever

Release 0.1.10
--------------
Released on 2014-01-31

* refactoring/standardizing the designs with bare_design

Release 0.1.9
-------------
Released on 2013-12-13

* complete the Cnc25D API with generic functions for figures
* motor_lid
* bell
* bagel
* bell_bagel
* crest
* cross_cube
* gimbal

Release 0.1.8
-------------
Released on 2013-11-07

* add crenels to the gearwheel
* epicyclic-gearing
* axle_lid

Release 0.1.7
-------------
Released on 2013-10-07

* unify the test-environment of the macro-scripts
* use python-dictionary as function-argument for designs with many parameters
* gearring (aka annulus)
* gearbar (aka rack)
* split_gearwheel

Release 0.1.6
-------------
Released on 2013-09-25

* Use arc primitives for generating DXF and SVG files
* finalization of gear_profile.py and gearwheel.py

Release 0.1.5
-------------
Released on 2013-09-18

* GPL v3 is applied to this Python package.

Release 0.1.4
-------------
Released on 2013-09-11

* Python package created with setuptools (instead of distribute)
* add API function smooth_outline_c_curve() approximates a curve defined by points and tangents with arcs.
* integrate circle into the format-B
* add API functions working at the *figure-level*: figure_simple_display(), figure_to_freecad_25d_part(), ..
* remove API function cnc_cut_outline_fc()
* gear_profile.py generates and simulates gear-profiles
* gearwheel.py

Release 0.1.3
-------------
Released on 2013-08-13

* New API function outline_arc_line() converts an outline defined by points into an outline of four possible formats: Tkinter display, svgwrite, dxfwrite or FreeCAD Part.
* API function cnc_cut_outline() supports smoothing and enlarging line-line, line-arc and arc-arc corners.
* Additional API functions such as outline_rotate(), outline_reverse()
* All Cnc25D API function are gathered in the cnc25d_api module
* Box wood frame design example generates also BRep in addition to STL and DXF.
* Box wood frame design example support router_bit radius up to 4.9 mm with all others parameters at default.

Release 0.1.2
-------------
Released on 2013-06-18

* Box wood frame design example

Release 0.1.1
-------------
Released on 2013-06-05

* Experimenting distribute

Release 0.1.0
-------------
Released on 2013-06-04

* Initial release

