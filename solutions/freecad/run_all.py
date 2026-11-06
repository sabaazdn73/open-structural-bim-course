"""Build the FreeCAD solutions of every IFC exercise in one FreeCAD session; files go to $FC_OUT.

    QT_QPA_PLATFORM=offscreen freecad solutions/freecad/run_all.py
    xvfb-run freecad solutions/freecad/s5_drawings.py        (the drawings, on their own)

(FreeCAD runs a .py file given on the command line as a macro. Close FreeCAD when it is done, or
set FC_EXIT=1 to make it quit by itself.) Then check the files with the course checker:

    python solutions/freecad/check_all.py
"""
import os
import runpy
import sys
import traceback

import FreeCAD

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# s5_drawings (the drawings of sections 5 and 6) is run on its own, after this script:
#     xvfb-run freecad solutions/freecad/s5_drawings.py
# Draft's SVG exporter measures texts in the active 3D view, which a script that opens several
# documents loses (Gui.ActiveDocument becomes None).
SCRIPTS = ["s1_project", "s2_structure", "s3_foundations_rebar", "s4_types", "s7_1_phases",
           "s7_2_options", "s7_3_worksharing", "s7_4_model_health", "s7_5_clash", "s7_6_purge", "s7_7_template",
           "s7_8_export"]

if FreeCAD.GuiUp:
    import FreeCADGui
    FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/BIM").SetBool("FirstTime", False)
    FreeCADGui.activateWorkbench("BIMWorkbench")
for key in ("AskAgain", "ProjectAskAgain", "ConvertTypeAskAgain", "AskBeforeSaving", "SingleDocAskAgain"):
    FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/NativeIFC").SetBool(key, False)

failed = []
for name in SCRIPTS:
    path = os.path.join(HERE, name + ".py")
    if not os.path.exists(path):
        continue
    print("====", name)
    try:
        runpy.run_path(path, run_name="__main__")
    except Exception:
        traceback.print_exc()
        failed.append(name)
    # documents stay open: closing them leaves FreeCAD without an active 3D view in a script
print("failed:", failed or "none")
if os.environ.get("FC_EXIT"):
    os._exit(1 if failed else 0)
