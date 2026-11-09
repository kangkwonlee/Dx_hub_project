"""Bins and RGB cubes on the robot desk, copied from the workbench prop (simulation/assets/props/workbench_v0.usda, measured
2026-10-07; recorded with it since 2026-10-21). The scan has none. Only the bins (BoxA/B, kinematic) and the six 4.5 cm cubes
(CubeA_*/CubeB_*, 20 g rigid bodies) are copied with their looks; its desks and partition are left out (the layout has the
scanned Desk6 pair and desk_partition.py). The prims keep the workbench names and local frame under one Xform, so
common/cube_task.py can use that Xform as its workbench root: the workbench frame sits on the desk centre with seat A, the
robot's side (y < 0, facing +y), on the north desk where the scanned SG2 stands, i.e. turned 180 deg."""
import os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'workbench_v0.usda')  # copy of skillforge simulation/assets/props/workbench_v0.usda
X, Y, YAW = -3.50, 14.50, 180.0  # desk centre (the two 60 cm desks meet at y 14.5), seat A to the north
SRC_TOP = 0.72  # workbench desk top; the layout's is desk_top
KEEP = ('Looks', 'BoxA', 'BoxB', 'CubeA_red', 'CubeA_green', 'CubeA_blue', 'CubeB_red', 'CubeB_green', 'CubeB_blue')


def add(stage, hall, desk_top, src=SRC):
    from pxr import Gf, Sdf, UsdGeom

    root = f'{hall}/RobotDesk_CubeSet'
    layer = stage.GetRootLayer()
    Sdf.CreatePrimInLayer(layer, root)
    ok = Sdf.CopySpec(Sdf.Layer.FindOrOpen(src), '/Workbench', layer, root)  # targets inside /Workbench follow the copy
    assert ok, src
    spec = layer.GetPrimAtPath(root)
    spec.specifier = Sdf.SpecifierDef
    spec.typeName = 'Xform'
    for child in [c.name for c in spec.nameChildren if c.name not in KEEP]:
        del spec.nameChildren[child]
    for key in [k for k in spec.ListInfoKeys() if k not in ('specifier', 'typeName')]:
        spec.ClearInfo(key)
    xf = UsdGeom.Xformable(stage.GetPrimAtPath(root))
    xf.AddTranslateOp().Set(Gf.Vec3d(X, Y, desk_top - SRC_TOP))
    xf.AddRotateZOp().Set(YAW)
    return root
