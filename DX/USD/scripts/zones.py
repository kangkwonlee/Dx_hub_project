"""DX Hub named zones: floor polygons and flat name labels, hidden in the scene itself so robot cameras and lidar never see them; a control view turns /Zones on (view.usda).

Labels are meshes baked from a font, so they need no texture or UI. config: zones.json. The name, use and polygon are also stored as customData on each zone prim.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pxr import Gf, Sdf, UsdGeom, UsdShade, Vt

FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
LABEL_Z, FLOOR_Z, PLATE_MARGIN = 3.3, 0.015, 0.08  # labels above the tallest walls, so a view with the ceiling hidden sees them all
COLORS = {'robot': (0.05, 0.60, 0.20), 'seat': (0.10, 0.35, 0.95), 'entrance': (0.95, 0.35, 0.02), 'display': (0.60, 0.12, 0.85), 'storage': (0.85, 0.65, 0.05), 'sofa': (0.0, 0.55, 0.60), 'kitchen': (0.55, 0.35, 0.15)}
PLATE_SHADE = 0.3  # dark name plate in the zone's colour, under white text: the floor is bright


def glyph_quads(lines, height):
    """Text as runs of filled pixels merged into rectangles: (x0, y0, x1, y1) in metres, centred, y up."""
    px = 64
    font = ImageFont.truetype(FONT, px, index=1)
    w = max(int(font.getlength(t)) for t in lines) + 8
    h = (px + 14) * len(lines) + 8
    im = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(im)
    for i, t in enumerate(lines):
        d.text(((w - font.getlength(t)) / 2, 2 + i * (px + 14)), t, fill=255, font=font)
    a = np.asarray(im) > 110
    ys, xs = np.nonzero(a)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    s = height / a.shape[0]
    open_runs, quads = {}, []
    for r in range(a.shape[0] + 1):
        row = a[r] if r < a.shape[0] else np.zeros(a.shape[1], bool)
        edges = np.flatnonzero(np.diff(np.r_[0, row.astype(np.int8), 0]))
        runs = set(zip(edges[::2].tolist(), edges[1::2].tolist()))
        for run in list(open_runs):
            if run not in runs:
                quads.append((run[0], open_runs.pop(run), run[1], r))
        for run in runs:
            open_runs.setdefault(run, r)
    W, H = a.shape[1] * s, a.shape[0] * s
    return [(x0 * s - W / 2, H / 2 - y1 * s, x1 * s - W / 2, H / 2 - y0 * s) for x0, y0, x1, y1 in quads]


def material(stage, path, color, opacity):
    m = UsdShade.Material.Define(stage, path)
    sh = UsdShade.Shader.Define(stage, path + '/Shader')
    sh.CreateIdAttr('UsdPreviewSurface')
    sh.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    sh.CreateInput('emissiveColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    sh.CreateInput('opacity', Sdf.ValueTypeNames.Float).Set(opacity)
    sh.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(1.0)
    m.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), 'surface')
    return m


def mesh(stage, path, points, counts, indices, mat):
    g = UsdGeom.Mesh.Define(stage, path)
    g.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*p) for p in points]))
    g.CreateFaceVertexCountsAttr(counts)
    g.CreateFaceVertexIndicesAttr(indices)
    g.CreateDoubleSidedAttr(True)
    g.CreateSubdivisionSchemeAttr('none')
    UsdShade.MaterialBindingAPI.Apply(g.GetPrim()).Bind(mat)
    return g


def add(stage, root, config):
    zones = json.load(open(config, encoding='utf-8'))['zones']
    scope = UsdGeom.Scope.Define(stage, f'{root}/Zones')
    UsdGeom.Imageable(scope).MakeInvisible()
    mats = {}
    for kind, color in COLORS.items():
        plate = tuple(PLATE_SHADE * c for c in color)
        mats[kind] = (material(stage, f'{root}/Zones/Looks/floor_{kind}', color, 0.28), material(stage, f'{root}/Zones/Looks/plate_{kind}', plate, 1.0))
    text = material(stage, f'{root}/Zones/Looks/text', (1.0, 1.0, 1.0), 1.0)
    placed = 0
    for z in zones:
        if not z.get('polygon'):  # in the table only until it has a place
            continue
        path = f"{root}/Zones/{z['id']}"
        x = UsdGeom.Xform.Define(stage, path).GetPrim()
        x.SetCustomData({'name_ko': z['name_ko'], 'name_en': z['name_en'], 'use': z['use'], 'status': z['status'],
                         'center': Gf.Vec2d(*z['center']), 'polygon': Vt.Vec2dArray([Gf.Vec2d(*p) for p in z['polygon']])})
        floor, plate = mats[z['kind']]
        n = len(z['polygon'])
        if not z.get('no_floor'):  # a zone sharing another zone's floor draws only its label
            mesh(stage, f'{path}/Floor', [(p[0], p[1], FLOOR_Z) for p in z['polygon']], [n], list(range(n)), floor)
        quads = glyph_quads([z['name_ko'], z['name_en']], z.get('label_h', 0.42))
        cx, cy = z.get('label_at') or z['center']
        pts, idx = [], []
        for x0, y0, x1, y1 in quads:
            i = len(pts)
            pts += [(cx + x0, cy + y0, LABEL_Z), (cx + x1, cy + y0, LABEL_Z), (cx + x1, cy + y1, LABEL_Z), (cx + x0, cy + y1, LABEL_Z)]
            idx += [i, i + 1, i + 2, i + 3]
        mesh(stage, f'{path}/Label', pts, [4] * len(quads), idx, text)
        q = np.array(quads)
        x0, y0, x1, y1 = q[:, 0].min() - PLATE_MARGIN, q[:, 1].min() - PLATE_MARGIN, q[:, 2].max() + PLATE_MARGIN, q[:, 3].max() + PLATE_MARGIN
        z_p = LABEL_Z - 0.01
        mesh(stage, f'{path}/Plate', [(cx + x0, cy + y0, z_p), (cx + x1, cy + y0, z_p), (cx + x1, cy + y1, z_p), (cx + x0, cy + y1, z_p)], [4], [0, 1, 2, 3], plate)
        placed += 1
    return placed, len(zones)
