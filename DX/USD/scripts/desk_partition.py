"""Partition on the robot desk, where its two 60 x 100 cm desks meet (11/02 scan, 3588 points: y 14.521..14.554, x -3.87..-3.07,
from the desk top up to z 1.18; grey, scan colour about 0.46). The Desk6 assets have none. A box with a collider, so the arm meets it."""
X0, X1, Y, T, Z1 = -3.87, -3.07, 14.535, 0.03, 1.18


def add(stage, hall, desk_top):
    from pxr import Gf, Sdf, UsdGeom, UsdPhysics, UsdShade

    root = f'{hall}/Scan_DeskPartition_1'
    UsdGeom.Xform.Define(stage, root)
    m = UsdShade.Material.Define(stage, f'{root}/Look')
    sh = UsdShade.Shader.Define(stage, f'{m.GetPath()}/Shader')
    sh.CreateIdAttr('UsdPreviewSurface')
    sh.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(.6, .59, .56))
    sh.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(.8)
    m.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), 'surface')
    c = UsdGeom.Cube.Define(stage, f'{root}/panel')
    c.CreateSizeAttr(1.0)
    c.AddTranslateOp().Set(Gf.Vec3d((X0 + X1) / 2, Y, (desk_top + Z1) / 2))
    c.AddScaleOp().Set(Gf.Vec3f(X1 - X0, T, Z1 - desk_top))
    UsdShade.MaterialBindingAPI.Apply(c.GetPrim()).Bind(m)
    UsdPhysics.CollisionAPI.Apply(c.GetPrim())
