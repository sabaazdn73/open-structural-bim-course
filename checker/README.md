# bimcheck

The automatic grader of the Open Structural BIM Course. It reads an IFC model (or an exported SVG/PDF drawing,
or a CSV schedule), checks it against the TB-01 brief, and prints what passes and what fails.

```
python -m pip install .
python -m bimcheck list
python -m bimcheck 2.1 tb01.ifc
```

It works on the IFC data and the geometry (through IfcOpenShell), not on how a particular program writes the
file, so models from FreeCAD, Bonsai or any other IFC exporter are checked the same way.
