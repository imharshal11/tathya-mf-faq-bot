import resvg._resvg as r

svg_data = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="red"/></svg>'
tree = r.usvg.Tree.from_str(svg_data, r.usvg.Options.default())
print(type(tree))
try:
    png_data = r.render(tree, (1,0,0,1,0,0), None, None, None, None)
    print(f'got {len(png_data)} bytes')
    with open('test.png', 'wb') as f:
        f.write(png_data)
    print('saved test.png')
except Exception as e:
    print(f'failed: {e}')