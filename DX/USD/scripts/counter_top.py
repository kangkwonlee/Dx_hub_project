"""Counter top over the kitchen bar's west side (user's tape 2026-11-03: 90 cm wide; 3D scan x -0.75..0.15, y 5.6..10.3, top z 1.12). The asset's bar has no overhang."""
X0, X1, Y0, Y1, Z0, Z1 = -0.75, 0.15, 5.6, 10.3, 1.09, 1.12


def add(stage, hall):
    from pxr import Gf, Sdf, UsdGeom, UsdPhysics, UsdShade

    root = f'{hall}/Scan_CounterTop_1'
    UsdGeom.Xform.Define(stage, root)
    m = UsdShade.Material.Define(stage, f'{root}/Look')
    sh = UsdShade.Shader.Define(stage, f'{m.GetPath()}/Shader')
    sh.CreateIdAttr('UsdPreviewSurface')
    sh.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(.9, .9, .89))
    sh.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(.3)
    m.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), 'surface')
    c = UsdGeom.Cube.Define(stage, f'{root}/top')
    c.CreateSizeAttr(1.0)
    c.AddTranslateOp().Set(Gf.Vec3d((X0 + X1) / 2, (Y0 + Y1) / 2, (Z0 + Z1) / 2))
    c.AddScaleOp().Set(Gf.Vec3f(X1 - X0, Y1 - Y0, Z1 - Z0))
    UsdShade.MaterialBindingAPI.Apply(c.GetPrim()).Bind(m)
    UsdPhysics.CollisionAPI.Apply(c.GetPrim())
