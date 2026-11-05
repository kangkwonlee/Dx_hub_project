"""Glass and wall corrections on the south line (user 2026-11-05).

South glass line: only Door_02 and Door_05 stay glass doors. Every other pane is deactivated and a wall covers its span up to the ceiling line, hiding the frame and header there. The 2026-11-02 scan has no points in Door_02, its leaf stands open beside Pane_03.

wall_004, west of the space north of that line: replaced by a two-leaf glass door between wall_037 and wall_043, with its baseboard removed.
"""
PANES = {'Pane_00': 0, 'Pane_01': 1, 'Pane_03': 3, 'Pane_04': 4, 'Pane_06': 6, 'Pane_07': 7, 'Pane_08': 8}
SPANS = ((-7.475, -4.975), (-4.075, -1.175), (-0.175, 3.645))  # x, each between the door posts' outer faces
Y0, Y1, Z1 = -15.25, -15.14, 2.74  # 1 cm past the header (y -15.24..-15.15) on each side
WALL_LOOK, COLLIDER_LIKE = 'Looks/wall_paint', 'Collision/wall_004_4'
DOOR_X, DOOR_Y0, DOOR_Y1, TOP = -7.535, -15.2, -13.045, 2.744  # wall_004's centre line, wall_037's north face, wall_043's south face
LEAVES, POST, LEAF_TOP, HEAD = 2, 0.05, 2.29, 2.34  # south line sizes: post 5 cm, leaf up to 2.29 m, header above 2.34 m
BOARD = (-7.66, -7.42, -15.25, -13.0)  # x0, x1, y0, y1 of the baseboard along wall_004's door part


def add(stage, building):
    from pxr import Gf, Sdf, UsdGeom, UsdPhysics, UsdShade, Vt

    for pane, n in PANES.items():
        stage.OverridePrim(f'{building}/Glass/B_SouthRooms/{pane}').SetActive(False)
        hit = [q for q in stage.GetPrimAtPath(f'{building}/Collision').GetChildren() if q.GetName().startswith(f'glass_B_SouthRooms_{n}_')]
        assert len(hit) == 1, pane
        hit[0].SetActive(False)
    look = UsdShade.Material(stage.GetPrimAtPath(f'{building}/{WALL_LOOK}'))
    label = stage.GetPrimAtPath(f'{building}/{COLLIDER_LIKE}').GetAttribute('semantics:labels:class').Get()
    for i, (x0, x1) in enumerate(SPANS):
        at, size = Gf.Vec3d((x0 + x1) / 2, (Y0 + Y1) / 2, Z1 / 2), Gf.Vec3f(x1 - x0, Y1 - Y0, Z1)
        c = UsdGeom.Cube.Define(stage, f'{building}/Walls/glass_wall_{i}')
        c.CreateSizeAttr(1.0)
        c.AddTranslateOp().Set(at)
        c.AddScaleOp().Set(size)
        UsdShade.MaterialBindingAPI.Apply(c.GetPrim()).Bind(look)
        k = UsdGeom.Cube.Define(stage, f'{building}/Collision/glass_wall_{i}')
        k.CreateSizeAttr(1.0)
        k.AddTranslateOp().Set(at)
        k.AddScaleOp().Set(size)
        k.CreatePurposeAttr('guide')
        UsdPhysics.CollisionAPI.Apply(k.GetPrim())
        if label is not None:
            k.GetPrim().AddAppliedSchema('SemanticsLabelsAPI:class')
            k.GetPrim().CreateAttribute('semantics:labels:class', Sdf.ValueTypeNames.TokenArray).Set(Vt.TokenArray(list(label)))
    west_door(stage, building)
    return len(PANES), len(SPANS), LEAVES


def box(stage, path, x0, x1, y0, y1, z0, z1, look):
    from pxr import Gf, UsdGeom, UsdShade

    c = UsdGeom.Cube.Define(stage, path)
    c.CreateSizeAttr(1.0)
    c.AddTranslateOp().Set(Gf.Vec3d((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    c.AddScaleOp().Set(Gf.Vec3f(x1 - x0, y1 - y0, z1 - z0))
    UsdShade.MaterialBindingAPI.Apply(c.GetPrim()).Bind(look)


def west_door(stage, building):
    import numpy as np
    from pxr import Gf, Sdf, UsdGeom, UsdPhysics, UsdShade, Vt

    stage.GetPrimAtPath(f'{building}/Walls/wall_004').SetActive(False)
    stage.GetPrimAtPath(f'{building}/Collision/wall_004_4').SetActive(False)
    # the baseboard is one triangle mesh: collapse the triangles along the door, face indices of its subset stay valid
    b = UsdGeom.Mesh(stage.GetPrimAtPath(f'{building}/Baseboards/Baseboards_kitchen'))
    p = np.array(b.GetPointsAttr().Get())
    idx = np.array(b.GetFaceVertexIndicesAttr().Get()).reshape(-1, 3)
    q = p[idx]
    gone = (q[..., 0].min(1) > BOARD[0]) & (q[..., 0].max(1) < BOARD[1]) & (q[..., 1].min(1) > BOARD[2]) & (q[..., 1].max(1) < BOARD[3])
    idx[gone] = idx[gone][:, :1]
    b.GetFaceVertexIndicesAttr().Set(Vt.IntArray(idx.ravel().tolist()))
    root = f'{building}/Glass/H_WestDoor'
    UsdGeom.Xform.Define(stage, root)
    look = lambda n: UsdShade.Material(stage.GetPrimAtPath(f'{building}/Looks/{n}'))
    x0, x1 = DOOR_X - 0.03, DOOR_X + 0.03
    edges = np.linspace(DOOR_Y0, DOOR_Y1, LEAVES + 1)
    for i, y in enumerate(edges):
        box(stage, f'{root}/Post_{i}', x0, x1, y - POST / 2, y + POST / 2, 0.0, HEAD, look('glass_frame'))
    for i, (a, c) in enumerate(zip(edges, edges[1:])):
        box(stage, f'{root}/Door_{i}', DOOR_X - 0.006, DOOR_X + 0.006, a, c, 0.04, LEAF_TOP, look('glass_frosted'))
    box(stage, f'{root}/RailBottom', x0, x1, DOOR_Y0, DOOR_Y1, 0.0, 0.04, look('glass_frame'))
    box(stage, f'{root}/RailTop', x0, x1, DOOR_Y0, DOOR_Y1, LEAF_TOP, HEAD, look('glass_frame'))
    box(stage, f'{root}/Header', DOOR_X - 0.045, DOOR_X + 0.045, DOOR_Y0, DOOR_Y1, HEAD, TOP, look('wall_paint'))
    c = UsdGeom.Cube.Define(stage, f'{building}/Collision/glass_H_WestDoor')
    c.CreateSizeAttr(1.0)
    c.AddTranslateOp().Set(Gf.Vec3d(DOOR_X, (DOOR_Y0 + DOOR_Y1) / 2, TOP / 2))
    c.AddScaleOp().Set(Gf.Vec3f(0.06, DOOR_Y1 - DOOR_Y0, TOP))
    c.CreatePurposeAttr('guide')
    UsdPhysics.CollisionAPI.Apply(c.GetPrim())
    c.GetPrim().AddAppliedSchema('SemanticsLabelsAPI:class')
    c.GetPrim().CreateAttribute('semantics:labels:class', Sdf.ValueTypeNames.TokenArray).Set(Vt.TokenArray(['glass_partition']))
    print('west door: baseboard triangles removed', int(gone.sum()))
