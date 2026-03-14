#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


README_PATH = Path(__file__).resolve().parents[1] / "README.md"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "wiring-diagram.svg"
SHIELD_DIR = Path(__file__).resolve().parents[1] / "config" / "boards" / "shields" / "corne"
CORNE_DTSI = SHIELD_DIR / "corne.dtsi"
LEFT_OVERLAY = SHIELD_DIR / "corne_left.overlay"
RIGHT_OVERLAY = SHIELD_DIR / "corne_right.overlay"
PRO_MICRO_PINS = Path(__file__).resolve().parents[1] / "zmk" / "app" / "module" / "boards" / "nicekeyboards" / "nice_nano" / "arduino_pro_micro_pins.dtsi"

HALF_RE = re.compile(
    r"#### (Left|Right) Half Pin Assignments\n"
    r"- \*\*Rows.*?\*\*:\n"
    r"((?:  - Row \d+: Pin \d+\n)+)"
    r"- \*\*Columns.*?\*\*:\n"
    r"((?:  - Column \d+: Pin \d+\n)+)",
    re.MULTILINE,
)
PIN_RE = re.compile(r"- (Row|Column) (\d+): Pin (\d+)")
GPIO_RE = re.compile(r"&pro_micro\s+(\d+)\b")
GPIO_MAP_RE = re.compile(
    r"<(\d+)\s+0\s+&gpio(\d)\s+(\d+)\s+0>\s*/\*\s*(D\d+(?:/A\d+)?)\s*\*/"
)
CONNECTOR_BLOCK_RE = re.compile(r"pro_micro:\s+connector\s*\{(.*?)\n\s*\};", re.DOTALL)

ACTIVE_KEYS = {
    0: [0, 1, 2, 3, 4, 5],
    1: [0, 1, 2, 3, 4, 5],
    2: [0, 1, 2, 3, 4, 5],
    3: [3, 4, 5],
}


def parse_readme(path: Path) -> dict[str, dict[str, list[int]]]:
    text = path.read_text()
    halves: dict[str, dict[str, list[int]]] = {}
    for side, rows_block, cols_block in HALF_RE.findall(text):
        rows = parse_pin_block(rows_block, "Row")
        cols = parse_pin_block(cols_block, "Column")
        halves[side.lower()] = {"rows": rows, "cols": cols}
    if set(halves) != {"left", "right"}:
        raise SystemExit("Could not parse both left/right pin blocks from README.md")
    return halves


def parse_gpio_list(path: Path, property_name: str) -> list[int]:
    text = path.read_text()
    match = re.search(rf"{property_name}\s*=\s*(.*?);", text, re.DOTALL)
    if not match:
        raise SystemExit(f"Could not find {property_name} in {path}")
    return [int(pin) for pin in GPIO_RE.findall(match.group(1))]


def parse_nice_nano_labels() -> dict[int, str]:
    text = PRO_MICRO_PINS.read_text()
    connector_match = CONNECTOR_BLOCK_RE.search(text)
    if not connector_match:
        raise SystemExit("Could not parse nice!nano pro_micro connector block")
    connector_text = connector_match.group(1)
    labels: dict[int, str] = {}
    for pro_pin, gpio_bank, gpio_pin, pin_label in GPIO_MAP_RE.findall(connector_text):
        labels[int(pro_pin)] = f"P{gpio_bank}.{int(gpio_pin):02d}"
    if not labels:
        raise SystemExit("Could not parse nice!nano Pro Micro pin map")
    return labels


def parse_zmk_config() -> dict[str, object]:
    rows = parse_gpio_list(CORNE_DTSI, "row-gpios")
    left_cols = parse_gpio_list(LEFT_OVERLAY, "col-gpios")
    right_cols = parse_gpio_list(RIGHT_OVERLAY, "col-gpios")
    labels = parse_nice_nano_labels()
    return {
        "left": {"rows": rows, "cols": left_cols},
        "right": {"rows": rows, "cols": right_cols},
        "labels": labels,
    }


def parse_pin_block(block: str, kind: str) -> list[int]:
    items: dict[int, int] = {}
    for found_kind, index, pin in PIN_RE.findall(block):
        if found_kind != kind:
            continue
        items[int(index)] = int(pin)
    return [items[i] for i in sorted(items)]


def svg_text(x: float, y: float, value: str, **attrs: str) -> str:
    merged = {"x": f"{x}", "y": f"{y}", **attrs}
    attr_text = " ".join(f'{k}="{html.escape(v, quote=True)}"' for k, v in merged.items())
    return f"<text {attr_text}>{html.escape(value)}</text>"


def svg_rect(x: float, y: float, w: float, h: float, **attrs: str) -> str:
    merged = {"x": f"{x}", "y": f"{y}", "width": f"{w}", "height": f"{h}", **attrs}
    attr_text = " ".join(f'{k}="{html.escape(v, quote=True)}"' for k, v in merged.items())
    return f"<rect {attr_text} />"


def svg_line(x1: float, y1: float, x2: float, y2: float, **attrs: str) -> str:
    merged = {"x1": f"{x1}", "y1": f"{y1}", "x2": f"{x2}", "y2": f"{y2}", **attrs}
    attr_text = " ".join(f'{k}="{html.escape(v, quote=True)}"' for k, v in merged.items())
    return f"<line {attr_text} />"


def svg_circle(cx: float, cy: float, r: float, **attrs: str) -> str:
    merged = {"cx": f"{cx}", "cy": f"{cy}", "r": f"{r}", **attrs}
    attr_text = " ".join(f'{k}="{html.escape(v, quote=True)}"' for k, v in merged.items())
    return f"<circle {attr_text} />"


def draw_half(side: str, data: dict[str, list[int]], labels: dict[int, str], x: int, y: int) -> str:
    cell_w = 54
    cell_h = 54
    cols = 6
    rows = 4
    row_slot_h = 54
    col_slot_h = 44
    matrix_x = x + 190
    matrix_y = y + 70
    matrix_w = cols * cell_w
    matrix_h = rows * cell_h
    pro_x = x
    pro_y = y + 20
    pro_w = 245
    row_stub_x = matrix_x - 34
    col_stub_y = matrix_y + matrix_h + 28
    row_start_y = pro_y + 86
    col_start_y = row_start_y + len(data["rows"]) * row_slot_h + 18
    last_col_y = col_start_y + (len(data["cols"]) - 1) * col_slot_h + 30
    pro_h = last_col_y - pro_y + 18

    parts = [
        svg_text(x, y, f"{side.title()} Half", fill="#111827", **{"font-size": "24", "font-weight": "700"}),
        svg_text(
            x,
            y + 24,
            "Back view. Columns left->right.",
            fill="#4b5563",
            **{"font-size": "13"},
        ),
        svg_rect(pro_x, pro_y, pro_w, pro_h, rx="18", fill="#f8fafc", stroke="#0f172a", **{"stroke-width": "2"}),
        svg_text(pro_x + 18, pro_y + 30, "nice!nano", fill="#0f172a", **{"font-size": "20", "font-weight": "700"}),
        svg_text(pro_x + 18, pro_y + 50, "nRF GPIO pins only", fill="#475569", **{"font-size": "12"}),
        svg_rect(matrix_x - 18, matrix_y - 18, matrix_w + 36, matrix_h + 36, rx="18", fill="#fffbeb", stroke="#d97706", **{"stroke-width": "2"}),
        svg_text(matrix_x, matrix_y - 28, "Keyboard matrix", fill="#92400e", **{"font-size": "18", "font-weight": "700"}),
    ]

    for row_idx, pin in enumerate(data["rows"]):
        pin_y = row_start_y + row_idx * row_slot_h
        row_y = matrix_y + row_idx * cell_h + cell_h / 2
        parts.extend(
            [
                svg_rect(pro_x + 14, pin_y, pro_w - 28, 34, rx="10", fill="#fee2e2", stroke="#b91c1c", **{"stroke-width": "1.5"}),
                svg_text(pro_x + 24, pin_y + 22, f"{labels[pin]} -> R{row_idx}", fill="#7f1d1d", **{"font-size": "15", "font-weight": "700"}),
                svg_line(pro_x + pro_w - 14, pin_y + 17, row_stub_x, row_y, stroke="#dc2626", **{"stroke-width": "3"}),
                svg_line(row_stub_x, row_y, matrix_x + matrix_w, row_y, stroke="#dc2626", **{"stroke-width": "3"}),
                svg_text(matrix_x + matrix_w + 12, row_y + 5, f"R{row_idx}", fill="#991b1b", **{"font-size": "14", "font-weight": "700"}),
            ]
        )

    for col_idx, pin in enumerate(data["cols"]):
        pin_y = col_start_y + col_idx * col_slot_h
        col_x = matrix_x + col_idx * cell_w + cell_w / 2
        parts.extend(
            [
                svg_rect(pro_x + 14, pin_y, pro_w - 28, 30, rx="10", fill="#dbeafe", stroke="#1d4ed8", **{"stroke-width": "1.5"}),
                svg_text(pro_x + 24, pin_y + 20, f"{labels[pin]} -> C{col_idx}", fill="#1e3a8a", **{"font-size": "14", "font-weight": "700"}),
                svg_line(pro_x + pro_w - 14, pin_y + 15, col_x, col_stub_y, stroke="#2563eb", **{"stroke-width": "3"}),
                svg_line(col_x, matrix_y, col_x, col_stub_y, stroke="#2563eb", **{"stroke-width": "3"}),
                svg_text(col_x - 10, matrix_y - 28, f"C{col_idx}", fill="#1d4ed8", **{"font-size": "14", "font-weight": "700"}),
            ]
        )

    for row_idx in range(rows):
        for col_idx in range(cols):
            if col_idx not in ACTIVE_KEYS[row_idx]:
                continue
            key_x = matrix_x + col_idx * cell_w + 8
            key_y = matrix_y + row_idx * cell_h + 8
            cx = key_x + 19
            cy = key_y + 19
            parts.extend(
                [
                    svg_rect(key_x, key_y, 38, 38, rx="9", fill="#ffffff", stroke="#334155", **{"stroke-width": "1.5"}),
                    svg_circle(cx, cy, 7, fill="#111827"),
                    svg_text(key_x + 4, key_y + 54, f"R{row_idx} C{col_idx}", fill="#475569", **{"font-size": "10"}),
                ]
            )

    return "\n".join(parts)


def build_svg(config: dict[str, object]) -> str:
    halves = {
        "left": config["left"],
        "right": config["right"],
    }
    labels = config["labels"]
    width = 1540
    height = 760
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Arial, sans-serif; }",
        "</style>",
        svg_rect(0, 0, width, height, fill="#f8fafc"),
        svg_text(40, 42, "Corne wiring diagram", fill="#020617", **{"font-size": "32", "font-weight": "700"}),
        svg_text(40, 68, "Generated from README.md pin assignments", fill="#475569", **{"font-size": "16"}),
        draw_half("left", halves["left"], labels, 40, 110),
        draw_half("right", halves["right"], labels, 810, 110),
        svg_text(40, 730, "Rows = red, Columns = blue. Bottom row only has switches on C3-C5.", fill="#334155", **{"font-size": "14"}),
    ]
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Corne wiring SVG from ZMK shield config.")
    parser.add_argument("-i", "--input", type=Path, default=README_PATH, help="Unused legacy arg; kept for compatibility")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT, help="Output SVG path")
    args = parser.parse_args()

    config = parse_zmk_config()
    svg = build_svg(config)
    args.output.write_text(svg)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
