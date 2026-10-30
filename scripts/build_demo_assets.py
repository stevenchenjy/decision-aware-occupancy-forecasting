#!/usr/bin/env python3
"""Build factual overview and social-preview graphics from fixed demo metrics.

Requires Pillow only for the PNG. The browser and notebook do not need it.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    from PIL import Image, ImageDraw, ImageFont

    data = json.loads((ROOT / "docs/demo/data.json").read_text())
    models = data["models"]
    output = ROOT / "docs/assets"
    output.mkdir(parents=True, exist_ok=True)
    colors = ["#13685e", "#80968f", "#bf7947"]
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="430" viewBox="0 0 1000 430" role="img" aria-labelledby="title desc">',
           '<title id="title">Fixed recommendation policies on 43 recorded test horizons</title>',
           '<desc id="desc">The hybrid has 490.1 kWh processed-load overlap and zero camera-label conflicts; the historical schedule 94.6 kWh and zero conflicts; LightGBM 493.9 kWh and 11 conflicts. These are saved-output observations, not measured savings.</desc>',
           '<rect width="1000" height="430" fill="#f1f6f3" rx="8"/>',
           '<g font-family="Arial,sans-serif" fill="#1c3035">',
           '<text x="35" y="49" font-size="23">Forecast quality is one part of the decision.</text>',
           '<text x="35" y="80" font-size="15" fill="#53676b">Fixed validation-selected policies · one-hour minimum windows · 43 saved test horizons</text>',
           '<text x="290" y="126" font-size="14">Processed-load overlap (kWh)</text><text x="816" y="117" font-size="13">Camera-label</text><text x="816" y="135" font-size="13">conflicts / intervals</text>']
    for i, (model, color) in enumerate(zip(models, colors)):
        metrics = model["reportedMetrics"]
        y = 162 + i * 65
        width = metrics["opportunityKwh"] / 500 * 430
        svg += [f'<text x="35" y="{y+21}" font-size="17">{model["label"]}</text>', f'<rect x="290" y="{y}" width="{width:.2f}" height="30" rx="3" fill="{color}"/>', f'<text x="{290+width+10:.2f}" y="{y+21}" font-size="16">{metrics["opportunityKwh"]:.1f}</text>', f'<text x="816" y="{y+21}" font-size="17">{metrics["conflictIntervals"]} / {metrics["recommendedIntervals"]}</text>']
    svg += ['<line x1="290" y1="356" x2="720" y2="356" stroke="#a6bab5"/>', '<text x="290" y="376" font-size="12">0</text><text x="720" y="376" font-size="12" text-anchor="end">500 kWh</text>', '<text x="35" y="407" font-size="13" fill="#53676b">Load overlap is not measured energy savings. Zero recorded conflicts does not guarantee future performance.</text>', '</g></svg>']
    (output / "reported-policies.svg").write_text("\n".join(svg) + "\n")
    (output / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#13685e"/><path d="M7 24V11l9-5 9 5v13H7zm8-12v5h3v-5h-3z" fill="#fff" fill-rule="evenodd"/></svg>\n')

    font_dir = Path("/System/Library/Fonts/Supplemental")
    fallback = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    def font(size, serif=False, bold=False):
        filename = "Georgia.ttf" if serif else ("Arial Bold.ttf" if bold else "Arial.ttf")
        path = font_dir / filename
        return ImageFont.truetype(str(path if path.exists() else fallback), size)
    image = Image.new("RGB", (1280, 640), "#fcfdfb")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 12, 640), fill="#13685e")
    draw.text((58, 37), "OCCUPANCY FORECASTING  /  REPRODUCIBLE RESEARCH", font=font(17, bold=True), fill="#13685e")
    draw.text((55, 88), "When should a forecast", font=font(59, serif=True), fill="#1c3035")
    draw.text((55, 159), "become a recommendation?", font=font(59, serif=True), fill="#1c3035")
    draw.text((58, 247), "Try the browser demo. Inspect the code. Reproduce the analysis.", font=font(23), fill="#53676b")
    draw.line((58, 301, 1222, 301), fill="#d6e2df", width=2)
    draw.text((58, 321), "Fixed policies · 43 saved test horizons", font=font(19, bold=True), fill="#1c3035")
    draw.text((650, 321), "Load proxy (kWh)", font=font(16), fill="#53676b")
    draw.text((1000, 321), "Label conflicts", font=font(16), fill="#53676b")
    for i, (model, color) in enumerate(zip(models, colors)):
        y = 365 + 51 * i
        metrics = model["reportedMetrics"]
        draw.text((58, y), model["label"], font=font(21), fill="#1c3035")
        draw.rounded_rectangle((336, y+3, 336+metrics["opportunityKwh"] / 500*280, y+26), radius=3, fill=color)
        draw.text((680, y), f'{metrics["opportunityKwh"]:.1f}', font=font(21), fill="#1c3035")
        draw.text((1040, y), str(metrics["conflictIntervals"]), font=font(21), fill="#1c3035")
    draw.text((58, 530), "Recorded load overlap is not measured energy savings.", font=font(17), fill="#53676b")
    draw.text((58, 589), "Junyu Chen · Chong Li", font=font(20, bold=True), fill="#1c3035")
    draw.text((620, 591), "stevenchenjy.github.io/decision-aware-occupancy-forecasting", font=font(16), fill="#53676b")
    image.save(output / "social-preview.png", optimize=True)
    print("Generated overview SVG, favicon, and 1280 x 640 social preview PNG.")


if __name__ == "__main__":
    main()
