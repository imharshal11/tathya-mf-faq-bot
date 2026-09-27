import resvg._resvg as r

# Try with bg_size parameter
svg_data = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="red"/></svg>'
tree = r.usvg.Tree.from_str(svg_data, r.usvg.Options.default())

# Try bg_size
try:
    png_data = r.render(tree, (1,0,0,1,0,0), None, None, (512, 512), None)
    with open('test_bg_size.png', 'wb') as f:
        f.write(png_data)
    from PIL import Image
    img = Image.open('test_bg_size.png')
    print(f'bg_size test: {img.size}')
except Exception as e:
    print(f'bg_size failed: {e}')

# Try without transform
try:
    png_data = r.render(tree, (1,0,0,1,0,0), None, None, None, None)
    with open('test_default.png', 'wb') as f:
        f.write(png_data)
    from PIL import Image
    img = Image.open('test_default.png')
    print(f'default test: {img.size}')
except Exception as e:
    print(f'default failed: {e}')