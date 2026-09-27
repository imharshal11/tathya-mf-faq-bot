import resvg._resvg as r

def svg_to_png(svg_path, png_path, width, height):
    with open(svg_path, 'r') as f:
        svg_data = f.read()
    tree = r.usvg.Tree.from_str(svg_data, r.usvg.Options.default())
    png_data = r.render(tree, (1,0,0,1,0,0), None, None, (width, height), None)
    with open(png_path, 'wb') as f:
        f.write(png_data)
    print(f'Generated {png_path} ({width}x{height}, {len(png_data)} bytes)')

svg_to_png('web/brand/icon.svg', 'web/brand/icon-512.png', 512, 512)
svg_to_png('web/brand/favicon.svg', 'web/brand/favicon-32.png', 32, 32)
svg_to_png('web/brand/favicon.svg', 'web/brand/favicon-16.png', 16, 16)
svg_to_png('web/brand/icon.svg', 'web/brand/apple-touch-icon.png', 180, 180)

print('All PNGs generated')