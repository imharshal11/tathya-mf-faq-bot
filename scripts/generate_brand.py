from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
import os

font_path = "scripts/fonts/Poppins-Bold.ttf"
font = TTFont(font_path)
glyph_set = font.getGlyphSet()
cmap = font.getBestCmap()

def get_glyph_path(char):
    glyph_name = cmap.get(ord(char))
    if not glyph_name:
        return None
    glyph = glyph_set[glyph_name]
    pen = SVGPathPen(glyph_set)
    glyph.draw(pen)
    return pen.getCommands()

# Get paths for needed characters
t_path = get_glyph_path('t')
a_path = get_glyph_path('a')
h_path = get_glyph_path('h')
y_path = get_glyph_path('y')

# Print paths for verification
print("t:", t_path)
print("a:", a_path)
print("h:", h_path)
print("y:", y_path)

# Save paths to a file for use in SVG generation
with open("scripts/fonts/glyph_paths.py", "w") as f:
    f.write(f't_path = """{t_path}"""\n')
    f.write(f'a_path = """{a_path}"""\n')
    f.write(f'h_path = """{h_path}"""\n')
    f.write(f'y_path = """{y_path}"""\n')

print("Glyph paths saved to scripts/fonts/glyph_paths.py")