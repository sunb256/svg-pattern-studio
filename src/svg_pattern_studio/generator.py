"""Dependency-free SVG generative-art engine.

Use render_svg() from Streamlit or your own Python scripts. The output is
plain, editable SVG (not a raster image or HTML canvas).
"""

from __future__ import annotations

import math
import random
from typing import Any

TAU = math.tau
KINDS = (
    "Flowing waves",
    "Curved grid",
    "Organic contours",
    "Triangle mesh",
    "Radiating arcs",
    "Spirograph",
    "Perspective fan",
    "Hexagon grid",
    "Dot field",
)
FADES = ("None", "To right", "To left", "To bottom", "To top", "Center focus")

PRESETS: dict[str, dict[str, Any]] = {
    "Deep ocean": {
        "bg_start": "#0B153B", "bg_end": "#176AA3", "glow": 35,
        "layers": [
            {"kind": "Triangle mesh", "color": "#A8DAFF", "opacity": .25, "density": 18,
             "width": 1.0, "scale": 1.28, "x": -24, "y": -24, "rotation": -8, "fade": "To right", "seed": 11},
            {"kind": "Flowing waves", "color": "#B8EAFF", "opacity": .38, "density": 28,
             "width": 1.0, "scale": 1.0, "x": 3, "y": 35, "rotation": -9, "fade": "To top", "seed": 41},
            {"kind": "Radiating arcs", "color": "#83C7F5", "opacity": .17, "density": 18,
             "width": .8, "scale": 1.0, "x": 43, "y": 15, "rotation": 15, "fade": "To left", "seed": 81},
        ],
    },
    "Emerald topography": {
        "bg_start": "#092A33", "bg_end": "#126C71", "glow": 26,
        "layers": [
            {"kind": "Organic contours", "color": "#A2F3D7", "opacity": .44, "density": 32,
             "width": .9, "scale": 1.0, "x": 30, "y": 0, "rotation": -17, "fade": "To left", "seed": 24},
            {"kind": "Curved grid", "color": "#72C9F0", "opacity": .27, "density": 20,
             "width": .8, "scale": 1.16, "x": -21, "y": 19, "rotation": 15, "fade": "To top", "seed": 4},
        ],
    },
    "Violet currents": {
        "bg_start": "#21133E", "bg_end": "#67428F", "glow": 36,
        "layers": [
            {"kind": "Flowing waves", "color": "#DFABFF", "opacity": .48, "density": 37,
             "width": .9, "scale": 1.15, "x": 0, "y": 26, "rotation": 18, "fade": "To top", "seed": 72},
            {"kind": "Perspective fan", "color": "#90C3FF", "opacity": .30, "density": 30,
             "width": 1.0, "scale": 1.0, "x": -15, "y": -8, "rotation": -10, "fade": "To right", "seed": 18},
            {"kind": "Spirograph", "color": "#FFBBDF", "opacity": .16, "density": 15,
             "width": .6, "scale": .6, "x": 43, "y": -25, "rotation": 0, "fade": "None", "seed": 7},
        ],
    },
    "Quiet charcoal": {
        "bg_start": "#101824", "bg_end": "#344352", "glow": 12,
        "layers": [
            {"kind": "Hexagon grid", "color": "#B9C9D7", "opacity": .22, "density": 23,
             "width": .9, "scale": 1.0, "x": 0, "y": 0, "rotation": 3, "fade": "Center focus", "seed": 31},
            {"kind": "Radiating arcs", "color": "#B6DBFC", "opacity": .38, "density": 27,
             "width": 1.1, "scale": 1.17, "x": 34, "y": 16, "rotation": 25, "fade": "To left", "seed": 91},
        ],
    },
    "Warm sunset": {
        "bg_start": "#55264D", "bg_end": "#D07865", "glow": 22,
        "layers": [
            {"kind": "Organic contours", "color": "#FFE2BF", "opacity": .36, "density": 30,
             "width": 1.1, "scale": 1.05, "x": -27, "y": 2, "rotation": 14, "fade": "To right", "seed": 6},
            {"kind": "Perspective fan", "color": "#FFDEA9", "opacity": .24, "density": 33,
             "width": 1.0, "scale": 1.15, "x": 15, "y": 9, "rotation": -20, "fade": "To left", "seed": 17},
        ],
    },
}


def default_layer(kind: str = "Flowing waves", seed: int = 1) -> dict[str, Any]:
    return {
        "enabled": True, "kind": kind, "color": "#B3DFFF", "opacity": .38,
        "density": 24, "width": 1.0, "scale": 1.0, "x": 0, "y": 0,
        "rotation": 0, "fade": "None", "seed": seed,
    }


def preset_layers(name: str) -> list[dict[str, Any]]:
    """Return independent copies, so editing never mutates preset definitions."""
    return [default_layer(layer["kind"], layer["seed"]) | layer.copy()
            for layer in PRESETS[name]["layers"]]


def _points(coords: list[tuple[float, float]], closed: bool = False) -> str:
    if not coords:
        return ""
    out = [f"M{coords[0][0]:.1f} {coords[0][1]:.1f}"]
    out.extend(f"L{x:.1f} {y:.1f}" for x, y in coords[1:])
    if closed:
        out.append("Z")
    return " ".join(out)


def _path(points: list[tuple[float, float]], *, closed: bool = False) -> str:
    return f'<path d="{_points(points, closed)}"/>'


def _flowing_waves(w: int, h: int, n: int, rng: random.Random) -> list[str]:
    paths = []
    phase = rng.random() * TAU
    for i in range(n):
        level = (-.10 + i * 1.18 / max(1, n - 1)) * h
        pts = []
        # Draw well past the SVG bounds so translating/rotating curves does not
        # expose straight line endings inside the composition.
        for k in range(185):
            x = (-1.2 + 3.4 * k / 184) * w
            t = (x / w + .2) / 1.4
            y = (level + .14*h*math.sin(TAU*(1.07*t) + phase + i*.09)
                 + .065*h*math.sin(TAU*(2.15*t) - i*.11 + phase*.7))
            pts.append((x, y))
        paths.append(_path(pts))
    return paths


def _curved_grid(w: int, h: int, n: int, rng: random.Random) -> list[str]:
    paths = []
    shift = rng.random() * TAU
    for i in range(n):
        base = (-.12 + 1.24*i/max(1, n - 1)) * w
        pts = []
        for k in range(180):
            y = (-1.2 + 3.4*k/179)*h
            t = (y / h + .15) / 1.3
            x = base + .095*w*math.sin(TAU*(t*.9) + shift + i*.13)
            pts.append((x, y))
        paths.append(_path(pts))
    for i in range(max(4, round(n*h/w))):
        count = max(4, round(n*h/w))
        base = (-.12 + 1.24*i/max(1, count - 1))*h
        pts = []
        for k in range(180):
            x = (-1.2 + 3.4*k/179)*w
            t = (x / w + .15) / 1.3
            y = base + .105*h*math.sin(TAU*(t*.8) + shift*.8 + i*.14)
            pts.append((x, y))
        paths.append(_path(pts))
    return paths


def _organic_contours(w: int, h: int, n: int, rng: random.Random) -> list[str]:
    paths = []
    phase = rng.random()*TAU
    for i in range(n):
        r = (i + 2) / (n + 1)
        rx = w*(.035 + .63*r)
        ry = h*(.03 + .67*r)
        pts = []
        for k in range(121):
            a = k*TAU/120
            warp = 1 + .095*math.sin(3*a + phase + r*.8) + .05*math.sin(6*a - phase)
            x = w*.52 + rx*math.cos(a)*warp
            y = h*.51 + ry*math.sin(a)*warp
            pts.append((x, y))
        paths.append(_path(pts, closed=True))
    return paths


def _triangle_mesh(w: int, h: int, n: int, rng: random.Random) -> list[str]:
    nx = max(5, round(n*.7))
    ny = max(4, round(nx*h/w))
    dx, dy = w*1.4/nx, h*1.4/ny
    pts: list[list[tuple[float, float]]] = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            row.append((-.2*w + i*dx + rng.uniform(-.30, .30)*dx,
                        -.2*h + j*dy + rng.uniform(-.3, .3)*dy))
        pts.append(row)
    segments = []
    for j in range(ny+1):
        for i in range(nx):
            segments.append((pts[j][i], pts[j][i+1]))
    for j in range(ny):
        for i in range(nx+1):
            segments.append((pts[j][i], pts[j+1][i]))
    for j in range(ny):
        for i in range(nx):
            segments.append((pts[j][i], pts[j+1][i+1] if rng.random() < .5 else pts[j+1][i-1] if i else pts[j+1][i+1]))
    d = " ".join(f'M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}' for (x1,y1),(x2,y2) in segments)
    circles = [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="currentColor" stroke="none"/>'
               for row in pts for (x,y) in row if rng.random() < .7]
    return [f'<path d="{d}"/>'] + circles


def _radiating_arcs(w: int, h: int, n: int, rng: random.Random) -> list[str]:
    paths = []
    offset = rng.random()*TAU
    for i in range(n):
        r = (.04 + i*.85/max(1,n-1))
        rx, ry = .68*w*r, .92*h*r
        start = offset + i*.13
        sweep = math.radians(130 + (i*29)%170)
        pts = []
        for k in range(81):
            a = start + sweep*k/80
            pts.append((.51*w + rx*math.cos(a), .5*h + ry*math.sin(a)))
        paths.append(_path(pts))
    return paths


def _spirograph(w: int, h: int, n: int, rng: random.Random) -> list[str]:
    paths = []
    for i in range(max(3, n//4)):
        fx, fy = 2+(i%5), 3+((i+2)%6)
        ph = rng.random() * TAU
        rx, ry = w*(.23 + .015*i), h*(.28 + .009*i)
        pts=[]
        for k in range(300):
            t = TAU*k/299
            pts.append((w*.5 + rx*math.sin(fx*t + ph),
                        h*.5 + ry*math.sin(fy*t)))
        paths.append(_path(pts))
    return paths


def _perspective_fan(w: int, h: int, n: int, rng: random.Random) -> list[str]:
    paths = []
    cx, cy = w*.08, h*.92
    bend = rng.uniform(-.08,.08)
    for i in range(n):
        t = i / max(1,n-1)
        dest_x = w*(-.10 + 1.38*t)
        dest_y = h*(-.20 + .24*math.sin(t*math.pi))
        ctrl1x = w*(.07 + .17*t)
        ctrl1y = h*(.28 + .21*t + bend)
        ctrl2x = w*(.28 + .65*t)
        ctrl2y = h*(.03 + .4*t + bend)
        paths.append(f'<path d="M{cx:.1f} {cy:.1f} C{ctrl1x:.1f} {ctrl1y:.1f} {ctrl2x:.1f} {ctrl2y:.1f} {dest_x:.1f} {dest_y:.1f}"/>')
    return paths


def _hexagon_grid(w: int, h: int, n: int, rng: random.Random) -> list[str]:
    radius = min(w,h)/(5 + n*.38)
    dx = math.sqrt(3)*radius
    dy = radius*1.5
    paths=[]
    for j in range(-3, math.ceil(h/dy)+4):
        for i in range(-3, math.ceil(w/dx)+4):
            cx = i*dx + (j%2)*dx*.5
            cy = j*dy
            points = [(cx + radius*math.cos(math.pi/6 + k*TAU/6),
                       cy + radius*math.sin(math.pi/6 + k*TAU/6)) for k in range(6)]
            paths.append(_path(points, closed=True))
    return paths


def _dot_field(w: int, h: int, n: int, rng: random.Random) -> list[str]:
    nx=max(6,n+5)
    ny=max(4,round(nx*h/w))
    dots=[]
    for j in range(ny+1):
        for i in range(nx+1):
            x = i*w/nx + rng.uniform(-.22,.22)*w/nx
            y = j*h/ny + rng.uniform(-.22,.22)*h/ny
            size = .5 + 2.1*(.5 + .5*math.sin(i*.43+j*.32))
            dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="currentColor" stroke="none"/>')
    return dots


_RENDERERS = {
    "Flowing waves": _flowing_waves,
    "Curved grid": _curved_grid,
    "Organic contours": _organic_contours,
    "Triangle mesh": _triangle_mesh,
    "Radiating arcs": _radiating_arcs,
    "Spirograph": _spirograph,
    "Perspective fan": _perspective_fan,
    "Hexagon grid": _hexagon_grid,
    "Dot field": _dot_field,
}


def _fade_def(index: int, fade: str, w: int, h: int) -> str:
    if fade == "None":
        return ""
    mid = f"fade-mask-{index}"
    grad = f"fade-grad-{index}"
    if fade == "Center focus":
        definition = (f'<radialGradient id="{grad}"><stop offset="15%" stop-color="white"/>'
                      '<stop offset="100%" stop-color="black"/></radialGradient>')
    else:
        coords = {
            "To right": ("0%", "0%", "100%", "0%"),
            "To left": ("100%", "0%", "0%", "0%"),
            "To bottom": ("0%", "0%", "0%", "100%"),
            "To top": ("0%", "100%", "0%", "0%"),
        }
        x1,y1,x2,y2 = coords[fade]
        definition = (f'<linearGradient id="{grad}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
                      '<stop offset="0%" stop-color="white"/>'
                      '<stop offset="100%" stop-color="black"/></linearGradient>')
    return (definition + f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">'
            f'<rect width="{w}" height="{h}" fill="url(#{grad})"/></mask>')


def _viewport_bounds(w: int, h: int, layer: dict[str, Any]) -> tuple[float, float, float, float]:
    """Inverse-map the *actual visible SVG rectangle* into pattern coordinates.

    Geometric lines are constructed past this region, not merely past a fixed
    1600x480 rectangle that might be translated, scaled or rotated afterwards.
    """
    scale = max(.2, min(4., float(layer.get("scale", 1.))))
    a = math.radians(float(layer.get("rotation", 0)))
    ct, st = math.cos(a), math.sin(a)
    dx = float(layer.get("x", 0)) * w / 100
    dy = float(layer.get("y", 0)) * h / 100
    cx, cy = w/2, h/2
    corners = []
    # Add a physical margin so antialiased strokes never end exactly at edges.
    for xx in (-max(24, .06*w), w+max(24, .06*w)):
        for yy in (-max(24, .06*h), h+max(24, .06*h)):
            u, v = (xx-cx-dx)/scale, (yy-cy-dy)/scale
            corners.append((cx+ct*u+st*v, cy-st*u+ct*v))
    return (min(x for x,y in corners), max(x for x,y in corners),
            min(y for x,y in corners), max(y for x,y in corners))


def _web_long_lines(w: int, h: int, n: int, rng: random.Random,
                    kind: str, bounds: tuple[float,float,float,float]) -> list[str]:
    """Draw complete crossing paths; never use an arbitrary finite endpoint."""
    xlo,xhi,ylo,yhi = bounds
    xspan = xhi-xlo
    yspan = yhi-ylo
    phase = rng.random()*TAU
    paths = []
    if kind == "Flowing waves":
        for i in range(n):
            level = (-.10+i*1.18/max(1,n-1))*h
            pts=[]
            for k in range(241):
                x = xlo+xspan*k/240
                t = (x/w+.2)/1.4
                y=(level+.14*h*math.sin(TAU*1.07*t+phase+i*.09)
                   +.065*h*math.sin(TAU*2.15*t-i*.11+phase*.7))
                pts.append((x,y))
            paths.append(_path(pts))
    elif kind == "Curved grid":
        for i in range(n):
            base = (-.12+1.24*i/max(1,n-1))*w
            pts=[]
            for k in range(241):
                y=ylo+yspan*k/240
                t=(y/h+.15)/1.3
                pts.append((base+.095*w*math.sin(TAU*.9*t+phase+i*.13),y))
            paths.append(_path(pts))
        count=max(4,round(n*h/w))
        for i in range(count):
            base=(-.12+1.24*i/max(1,count-1))*h
            pts=[]
            for k in range(241):
                x=xlo+xspan*k/240
                t=(x/w+.15)/1.3
                pts.append((x,base+.105*h*math.sin(TAU*.8*t+phase*.8+i*.14)))
            paths.append(_path(pts))
    elif kind == "Perspective fan":
        # The old fan joined paths to an *inside-canvas* point, so every line
        # visibly ended there. The focus is now outside and each curve continues
        # past both horizontal boundaries, including after arbitrary transforms.
        for i in range(n):
            t = i/max(1,n-1)
            focus_x,focus_y = -.60*w,1.40*h
            target_x,target_y = 1.55*w,(-.45+.92*t)*h
            bend = (.05+.11*t)*h
            pts=[]
            for k in range(201):
                x=xlo+xspan*k/200
                u=(x-focus_x)/(target_x-focus_x)
                y=focus_y+(target_y-focus_y)*u + bend*math.sin(math.pi*u)
                pts.append((x,y))
            paths.append(_path(pts))
    else:
        raise ValueError(kind)
    return paths


def _stable_noise(seed: int, cell_x: int, cell_y: int, channel: int) -> float:
    """Deterministic per-world-cell noise: unaffected by visible bounds.

    Sequential RNG calls changed the mesh whenever its generated grid expanded
    or shifted. World-cell hashing lets the same seed be translated / rotated
    as a true copy, including diagonal edges and dots in shared cells.
    """
    mask = (1 << 64) - 1
    v = (seed + cell_x * 0x9E3779B97F4A7C15
         + cell_y * 0xBF58476D1CE4E5B9
         + channel * 0x94D049BB133111EB) & mask
    v = ((v ^ (v >> 30)) * 0xBF58476D1CE4E5B9) & mask
    v = ((v ^ (v >> 27)) * 0x94D049BB133111EB) & mask
    v ^= v >> 31
    return (v >> 11) / (1 << 53)


def _web_mesh(w:int,h:int,n:int,rng:random.Random,
              bounds:tuple[float,float,float,float], kind:str) -> list[str]:
    """World-anchored padded mesh, stable for copies with changed transforms."""
    xlo,xhi,ylo,yhi=bounds
    step=w/max(6,n*.72)
    nx=max(2,math.ceil((xhi-xlo)/step)+4)
    ny=max(2,math.ceil((yhi-ylo)/step)+4)
    if nx*ny > 8000:
        step *= math.sqrt(nx*ny/8000)
    first_x=math.floor(xlo/step)-2
    first_y=math.floor(ylo/step)-2
    nx=math.ceil(xhi/step)-first_x+3
    ny=math.ceil(yhi/step)-first_y+3
    seed = rng.getrandbits(64)
    if kind == "Triangle mesh":
        pts=[]
        for j in range(ny+1):
            row=[]
            gy=first_y+j
            for i in range(nx+1):
                gx=first_x+i
                row.append(((gx+(_stable_noise(seed,gx,gy,0)-.5)*.52)*step,
                            (gy+(_stable_noise(seed,gx,gy,1)-.5)*.52)*step))
            pts.append(row)
        seg=[]
        for j in range(ny+1):
            for i in range(nx):
                seg.append((pts[j][i],pts[j][i+1]))
        for j in range(ny):
            gy=first_y+j
            for i in range(nx+1):
                seg.append((pts[j][i],pts[j+1][i]))
            for i in range(nx):
                gx=first_x+i
                if _stable_noise(seed,gx,gy,2)<.5:
                    seg.append((pts[j][i],pts[j+1][i+1]))
                else:
                    seg.append((pts[j][i+1],pts[j+1][i]))
        d=' '.join(f'M{a:.1f} {b:.1f}L{c:.1f} {d:.1f}' for (a,b),(c,d) in seg)
        return [f'<path d="{d}"/>'] + [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="currentColor" stroke="none"/>'
                  for j,row in enumerate(pts) for i,(x,y) in enumerate(row)
                  if _stable_noise(seed,first_x+i,first_y+j,3)<.6]
    if kind == "Dot field":
        return [f'<circle cx="{(gx + (_stable_noise(seed,gx,gy,0)-.5)*.44)*step:.1f}" '
                f'cy="{(gy + (_stable_noise(seed,gx,gy,1)-.5)*.44)*step:.1f}" r="1.6" fill="currentColor" stroke="none"/>'
                for gy in range(first_y,first_y+ny+1) for gx in range(first_x,first_x+nx+1)]
    # Honeycomb tiles are closed rings, and generated outside the visible region.
    r=step*.64
    dx=math.sqrt(3)*r
    dy=1.5*r
    x0=math.floor(xlo/dx)*dx-3*dx
    y0=math.floor(ylo/dy)*dy-3*dy
    nx=math.ceil((xhi-x0)/dx)+4
    ny=math.ceil((yhi-y0)/dy)+4
    if nx*ny>8000:
        r*=math.sqrt(nx*ny/8000)
        dx=math.sqrt(3)*r;dy=1.5*r
        x0=math.floor(xlo/dx)*dx-3*dx
        y0=math.floor(ylo/dy)*dy-3*dy
        nx=math.ceil((xhi-x0)/dx)+4
        ny=math.ceil((yhi-y0)/dy)+4
    out=[]
    for j in range(ny+1):
        for i in range(nx+1):
            cx=x0+(i+(j%2)*.5)*dx
            cy=y0+j*dy
            out.append(_path([(cx+r*math.cos(math.pi/6+k*TAU/6),
                               cy+r*math.sin(math.pi/6+k*TAU/6)) for k in range(6)],closed=True))
    return out


def _web_shapes(w:int,h:int,n:int,rng:random.Random,kind:str,
                bounds:tuple[float,float,float,float]) -> list[str]:
    if kind in ("Flowing waves","Curved grid","Perspective fan"):
        return _web_long_lines(w,h,n,rng,kind,bounds)
    if kind in ("Triangle mesh","Hexagon grid","Dot field"):
        return _web_mesh(w,h,n,rng,bounds,kind)
    if kind == "Radiating arcs":
        # Formerly partial arcs stopped at arbitrary angles within the view.
        # Full ellipses preserve the arc appearance, without loose endpoints.
        return [f'<ellipse cx="{w*.52:.1f}" cy="{h*.51:.1f}" '
                f'rx="{w*(.07+.9*i/max(1,n-1)):.1f}" '
                f'ry="{h*(.09+1.2*i/max(1,n-1)):.1f}"/>' for i in range(n)]
    return _RENDERERS[kind](w,h,n,rng)


def render_svg(
    width: int,
    height: int,
    layers: list[dict[str, Any]],
    *,
    bg_start: str = "#0B153B",
    bg_end: str = "#176AA3",
    glow: int = 30,
    transparent: bool = False,
    edge_feather: int = 0,
    seamless: bool = False,
    vertical_feather: int = 0,
    vertical_anchor: str = "top",
) -> str:
    """Build a self-contained SVG. Layer order follows list order (later is on top)."""
    if not (200 <= width <= 6000 and 200 <= height <= 6000):
        raise ValueError("Width and height must be between 200 and 6000")
    for color in (bg_start, bg_end):
        if not (len(color)==7 and color[0]=='#' and all(c in '0123456789abcdefABCDEF' for c in color[1:])):
            raise ValueError("Expected hex color like #123ABC")
    if not 0 <= edge_feather <= 40:
        raise ValueError("edge_feather must be between 0 and 40 percent")
    if not 0 <= vertical_feather <= 50 or vertical_anchor not in ("top", "bottom", "center"):
        raise ValueError("Invalid vertical feather configuration")
    defs = [f'<clipPath id="canvas-clip"><rect width="{width}" height="{height}"/></clipPath>']
    if vertical_feather:
        top = vertical_anchor in ("bottom", "center")
        bottom = vertical_anchor in ("top", "center")
        fade = vertical_feather if vertical_anchor != "center" else min(48, vertical_feather)
        stops = (
            [f'<stop offset="0%" stop-color="black"/>',
             f'<stop offset="{fade}%" stop-color="white"/>']
            if top else [f'<stop offset="0%" stop-color="white"/>']
        )
        if bottom:
            stops.extend([f'<stop offset="{100-fade}%" stop-color="white"/>',
                          '<stop offset="100%" stop-color="black"/>'])
        else:
            stops.append('<stop offset="100%" stop-color="white"/>')
        defs.append('<linearGradient id="vertical-fade-gradient" x1="0%" y1="0%" x2="0%" y2="100%">'
                    + ''.join(stops) + '</linearGradient>'
                    f'<mask id="vertical-fade-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="{width}" height="{height}">'
                    f'<rect width="{width}" height="{height}" fill="url(#vertical-fade-gradient)"/></mask>')
    if edge_feather:
        # An alpha feather on both vertical edges removes hard cutoffs when a
        # decoration is narrower than the containing web page.
        right_start = 100 - edge_feather
        defs.append(
            '<linearGradient id="edge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">'
            '<stop offset="0%" stop-color="black"/>'
            f'<stop offset="{edge_feather}%" stop-color="white"/>'
            f'<stop offset="{right_start}%" stop-color="white"/>'
            '<stop offset="100%" stop-color="black"/></linearGradient>'
            f'<mask id="edge-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="{width}" height="{height}">'
            f'<rect width="{width}" height="{height}" fill="url(#edge-gradient)"/></mask>'
        )
    if not transparent:
        defs += [
            '<linearGradient id="background-gradient" x1="0%" y1="0%" x2="100%" y2="100%">'
            f'<stop offset="0%" stop-color="{bg_start}"/>'
            f'<stop offset="100%" stop-color="{bg_end}"/></linearGradient>',
            '<radialGradient id="soft-glow" cx="76%" cy="78%" r="75%">'
            '<stop offset="0%" stop-color="#FFFFFF" stop-opacity=".34"/>'
            '<stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient>',
        ]
    artwork = []
    if not transparent:
        artwork.append(f'<rect width="{width}" height="{height}" fill="url(#background-gradient)"/>')
        if glow:
            artwork.append(f'<rect width="{width}" height="{height}" fill="url(#soft-glow)" opacity="{max(0, min(100,glow))/100:.2f}"/>')
    for idx, layer in enumerate(layers):
        if not layer.get("enabled", True):
            continue
        kind = layer.get("kind", "Flowing waves")
        if kind not in _RENDERERS:
            raise ValueError(f"Unknown pattern: {kind}")
        color = layer.get("color", "#B3DFFF")
        if not (len(color)==7 and color[0]=='#' and all(c in '0123456789abcdefABCDEF' for c in color[1:])):
            raise ValueError("Expected hex layer color")
        density = max(5, min(55,int(layer.get("density",24))))
        rng = random.Random(int(layer.get("seed",1)))
        shapes = (_web_shapes(width, height, density, rng, kind,
                              _viewport_bounds(width, height, layer))
                  if seamless else _RENDERERS[kind](width, height, density, rng))
        fade = layer.get("fade", "None")
        if fade not in FADES:
            raise ValueError(f"Unknown fade: {fade}")
        defs.append(_fade_def(idx, fade, width, height))
        mask = f' mask="url(#fade-mask-{idx})"' if fade != "None" else ""
        opacity = max(0.,min(1.,float(layer.get("opacity",.4))))
        stroke_width = max(.1, min(8.,float(layer.get("width",1.))))
        scale = max(.2,min(4.,float(layer.get("scale",1.))))
        x = float(layer.get("x",0)) / 100 * width
        y = float(layer.get("y",0)) / 100 * height
        angle = float(layer.get("rotation",0))
        transform = (f'translate({x:.1f} {y:.1f}) translate({width/2:.1f} {height/2:.1f}) '
                     f'rotate({angle:.1f}) scale({scale:.3f}) translate({-width/2:.1f} {-height/2:.1f})')
        blend = layer.get("blend", "normal")
        if blend not in ("normal", "screen", "multiply", "overlay"):
            raise ValueError(f"Unknown blend mode: {blend}")
        blend_style = f' style="mix-blend-mode:{blend}"' if blend != "normal" else ""
        artwork.append(
            f'<g{mask}{blend_style}>'
            f'<g transform="{transform}" color="{color}" stroke="{color}" '
            f'stroke-width="{stroke_width:.2f}" fill="none" opacity="{opacity:.3f}" '
            'stroke-linecap="round" stroke-linejoin="round">'
            + ''.join(shapes) + '</g></g>'
        )
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="Generated geometric background">'
            '<defs>' + ''.join(defs) + '</defs>'
            f'<g clip-path="url(#canvas-clip)"' + (' mask="url(#vertical-fade-mask)"' if vertical_feather else (' mask="url(#edge-mask)"' if edge_feather else '')) + '>'
            + ''.join(artwork) + '</g></svg>')


if __name__ == "__main__":
    from pathlib import Path
    p = PRESETS["Deep ocean"]
    target = Path(__file__).with_name("example-background.svg")
    target.write_text(render_svg(1600, 900, preset_layers("Deep ocean"), **{k: p[k] for k in ("bg_start", "bg_end", "glow")}), encoding="utf-8")
    print(f"Saved {target}")
