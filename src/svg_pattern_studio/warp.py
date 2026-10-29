"""Vector-preserving trapezoid warp for SVG layer geometry.

SVG's built-in affine transforms cannot turn a rectangle into a trapezoid.
This module remaps paths to actual vector coordinates, so the output remains
editable SVG without a raster displacement filter or external dependency.
"""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from typing import Callable

TOKENS = re.compile(r"[MLCZmlcz]|[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?")


def warp_enabled(layer: dict) -> bool:
    return any(float(layer.get(key, default)) != default for key, default in (
        ("warp_top", 100), ("warp_bottom", 100),
        ("warp_top_shift", 0), ("warp_bottom_shift", 0),
    ))


def _warp_factors(y: float, h: float, layer: dict) -> tuple[float, float]:
    t = y / h
    top = float(layer.get("warp_top", 100)) / 100
    bottom = float(layer.get("warp_bottom", 100)) / 100
    top_shift = float(layer.get("warp_top_shift", 0)) / 100
    bottom_shift = float(layer.get("warp_bottom_shift", 0)) / 100
    return top + (bottom - top) * t, top_shift + (bottom_shift - top_shift) * t


def warp_point(x: float, y: float, w: float, h: float, layer: dict) -> tuple[float, float]:
    factor, shift = _warp_factors(y, h, layer)
    return w / 2 + (x - w / 2) * factor + shift * w, y


def unwarp_point(x: float, y: float, w: float, h: float, layer: dict) -> tuple[float, float]:
    factor, shift = _warp_factors(y, h, layer)
    if factor <= 0:
        raise ValueError("Trapezoid width must remain positive")
    return w / 2 + (x - w / 2 - shift * w) / factor, y


def transformed_point(x: float, y: float, w: float, h: float, layer: dict) -> tuple[float, float]:
    """Apply translate, rotate, scale (SVG order), followed by nonlinear warp."""
    scale = max(.2, min(4., float(layer.get("scale", 1))))
    angle = math.radians(float(layer.get("rotation", 0)))
    cx, cy = w / 2, h / 2
    u, v = (x - cx) * scale, (y - cy) * scale
    px = cx + u * math.cos(angle) - v * math.sin(angle) + float(layer.get("x", 0)) * w / 100
    py = cy + u * math.sin(angle) + v * math.cos(angle) + float(layer.get("y", 0)) * h / 100
    return warp_point(px, py, w, h, layer)


def untransformed_point(x: float, y: float, w: float, h: float, layer: dict) -> tuple[float, float]:
    """Inverse mapping, used to render paths beyond all visible edges."""
    x, y = unwarp_point(x, y, w, h, layer)
    scale = max(.2, min(4., float(layer.get("scale", 1))))
    a = math.radians(float(layer.get("rotation", 0)))
    u = (x - w / 2 - float(layer.get("x", 0)) * w / 100) / scale
    v = (y - h / 2 - float(layer.get("y", 0)) * h / 100) / scale
    return w / 2 + math.cos(a)*u + math.sin(a)*v, h / 2 - math.sin(a)*u + math.cos(a)*v


def _mapped_path(d: str, mapper: Callable) -> str:
    """Supports emitted M/L/C/Z paths; curves become sampled vector polylines."""
    tokens = TOKENS.findall(d)
    out: list[str] = []
    index = 0
    command = None
    current = (0., 0.)
    start = current
    while index < len(tokens):
        if tokens[index].upper() in ('M','L','C','Z') and tokens[index].isalpha():
            command = tokens[index].upper()
            index += 1
        if command is None:
            raise ValueError("Invalid generated path")
        if command == 'Z':
            out.append('Z')
            current = start
            command = None
            continue
        if command in ('M','L'):
            if index + 1 >= len(tokens):
                raise ValueError('Truncated point in path')
            point = (float(tokens[index]), float(tokens[index+1]))
            index += 2
            if command == 'M':
                x, y = mapper(*point)
                out.append(f'M{x:.2f} {y:.2f}')
                start = point
                command = 'L'
            else:
                # x' depends on x*y. Sample diagonal long segments when needed.
                count = max(1, min(32, math.ceil(abs(point[1]-current[1]) / 22)))
                for n in range(1, count+1):
                    t = n/count
                    x, y = mapper(current[0]+(point[0]-current[0])*t,
                                  current[1]+(point[1]-current[1])*t)
                    out.append(f'L{x:.2f} {y:.2f}')
            current = point
        elif command == 'C':
            if index + 5 >= len(tokens):
                raise ValueError('Truncated cubic in path')
            c1 = (float(tokens[index]), float(tokens[index+1]))
            c2 = (float(tokens[index+2]), float(tokens[index+3]))
            end = (float(tokens[index+4]), float(tokens[index+5]))
            index += 6
            for j in range(1, 25):
                t = j/24; u = 1-t
                x = u**3*current[0] + 3*u*u*t*c1[0] + 3*u*t*t*c2[0] + t**3*end[0]
                y = u**3*current[1] + 3*u*u*t*c1[1] + 3*u*t*t*c2[1] + t**3*end[1]
                xx, yy = mapper(x, y)
                out.append(f'L{xx:.2f} {yy:.2f}')
            current = end
    return ' '.join(out)


def warp_shapes(shapes: list[str], w: float, h: float, layer: dict) -> list[str]:
    """Warp each supported SVG primitive; preserve original appearance attrs."""
    mapper = lambda x, y: transformed_point(x, y, w, h, layer)
    result = []
    for shape in shapes:
        element = ET.fromstring(shape)
        tag = element.tag
        attrs = dict(element.attrib)
        if tag == 'path':
            attrs['d'] = _mapped_path(attrs['d'], mapper)
        elif tag in ('circle', 'ellipse'):
            cx, cy = float(attrs.pop('cx')), float(attrs.pop('cy'))
            if tag == 'circle':
                rx = ry = float(attrs.pop('r'))
            else:
                rx, ry = float(attrs.pop('rx')), float(attrs.pop('ry'))
            points = [(cx + rx*math.cos(i*math.tau/32),
                       cy + ry*math.sin(i*math.tau/32)) for i in range(32)]
            # closed polygon in path form, including small dot-field nodes
            mapped = [mapper(*p) for p in points]
            attrs['d'] = (f'M{mapped[0][0]:.2f} {mapped[0][1]:.2f} ' +
                          ' '.join(f'L{x:.2f} {y:.2f}' for x,y in mapped[1:]) + ' Z')
            tag = 'path'
        else:
            raise ValueError(f'Unsupported SVG primitive for warp: {tag}')
        # All generated values are numeric or from our internal shape generator.
        result.append(ET.tostring(ET.Element(tag, attrs), encoding='unicode', short_empty_elements=True))
    return result
