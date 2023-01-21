import math
from pathlib import Path
from PIL import Image

page_length = 1712

u = 'up'
d = 'down'
f = 'front'
b = 'back'

# quadrants
a = [0, 0]
b = [1, 0]
c = [0, 1]
d = [1, 1]

# pages

hv1 = 'hv1'
h2 = 'h2'
h3 = 'h3'
h4 = 'h4'
r1 = 'r1'
r2 = 'r2'
r3 = 'r3'
r4 = 'r4'
t1 = 't1'
t2 = 't2'
t3 = 't3'
t4 = 't4'
v2 = 'v2'
v3 = 'v3'
v4 = 'v4'

# unfolded squares
#  1  2  3  4
# 12        5
# 11        6
# 10  9  8  7
square_locs = {1:  [0, 0], 2: [0, 1], 3: [0, 2], 4: [0, 3],
               12: [1, 0],                       5: [1, 3],
               11: [2, 0],                       6: [2, 3],
               10: [3, 0], 9: [3, 1], 8: [3, 2], 7: [3, 3]}


# (sheet_nb, up/down)
page_sheet: {hv1: [[(1, u)]]}

# (square_nb, front/back, up/down)
page_squares = {hv1: [[(5, b, u), (2, b, d)],
                      [(1, b, d), (11, b, u)]]}

dest_dimension = (page_length * 4, page_length * 4)
front = Image.new('L', dest_dimension, color=255)
back = Image.new('L', dest_dimension, color=255)


def paste(im, loc):
    square_number, side, up = loc
    square_loc = square_locs[square_number]
    dest = front if side == 'f' else back
    if up == 'd':
        im = im.rotate(180)
    left = square_loc[0] * page_length
    top = square_loc[1] * page_length
    dest.paste(im, (left, top))


def main():
    for page_name, locs in page_squares.items():
        print(page_name)
        im = Image.open(Path(f'../{page_name}.tif'))
        width, height = im.size
        row_count = len(locs)
        col_count = len(locs[0])
        crop_width = math.floor(width / col_count)
        crop_height = math.floor(height / row_count)
        for x, row in enumerate(locs):
            left = x * crop_width
            right = left + crop_width
            for y, loc in enumerate(row):
                print(x, y)
                upper = y * crop_height
                lower = upper + crop_height
                cropped = im.crop((left, upper, right, lower))
                # cropped.show()
                paste(cropped, loc)


main()
back.show()
