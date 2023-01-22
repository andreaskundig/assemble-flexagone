import math
from pathlib import Path
from PIL import Image

page_length = 1712

u = 'up'
d = 'down'
f = 'front'
b = 'back'

# page_parts
pa = 'pa'
pb = 'pb'
pc = 'pc'
pd = 'pd'
pall = 'pall'
page_parts = [pa, pb, pc, pd, pall]
coordinates = [[0, 0], [1, 0],
               [0, 1], [1, 1],
               [0, 0]]

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

cover = 'cover'
cover2 = 'cover2'

def is_full_page(page_name):
    page_number = int(page_name[-1])
    return page_number % 2 != 0


def is_vertical(page_name):
    if is_full_page(page_name):
        raise Exception(f'Page {page_name} is not a half page')
    return page_name[0] in ['h', 'r']


def page_part_coordinates(p_name, part):
    if part == pb:
        if not is_full_page(p_name) and is_vertical(p_name):
            part = pc
    return coordinates[page_parts.index(part)]


def width_height_multiplicator(page_name):
    if page_name in [cover, cover2]:
        return (1, 1)
    if is_full_page(page_name):
        return (0.5, 0.5)
    elif is_vertical(page_name):
        return (1, 0.5)
    else:
        return (0.5, 1)


# (page, quarter, up/down
square_pages_front = {1:  [(t3, pd, d), (v3, pc, d)],
                      2:  [(h2, pa, d), (v2, pa, u)],
                      3:  [(h3, pb, d), (r3, pb, d)],
                      4:  [(h3, pa, d), (r3, pc, d)],
                      5:  [(h4, pa, u), (v2, pb, u)],
                      6:  [(t3, pc, d), (v3, pd, d)],
                      7:  [(t3, pa, d), (v3, pb, d)],
                      8:  [(h4, pa, d), (v2, pb, u)],
                      9:  [(h3, pc, d), (r3, pa, d)],
                      10: [(h3, pd, d), (r3, pb, d)],
                      11: [(h2, pb, u), (v4, pa, u)],
                      12: [(t3, pb, d), (v3, pa, d)],
                      # 13: [(cover, pall, u)]
                      }

square_pages_back = {1:  [(r4, pb, d)],
                     2:  [(t1, pa, d), (hv1, pb, d), (r1, pd, d)],
                     3:  [(t2, pa, u)],
                     4:  [(t2, pb, u)],
                     5:  [(t1, pb, u), (hv1, pa, u), (r1, pc, u)],
                     6:  [(r2, pb, d)],
                     7:  [(r2, pa, d)],
                     8:  [(t1, pd, d), (hv1, pc, d), (r1, pa, d)],
                     9:  [(t4, pb, u)],
                     10: [(t4, pa, u)],
                     11: [(t1, pc, u), (hv1, pd, u), (r1, pb, u)],
                     12: [(r4, pa, d)],
                     # 13: [(cover2, pall, u)]
                     }

# unfolded squares
#  1  2  3  4
# 12 13     5
# 11        6
# 10  9  8  7
square_locs = {1:  [0, 0], 2:  [1, 0], 3: [2, 0], 4: [3, 0],
               12: [0, 1], 13: [1, 1],            5: [3, 1],
               11: [0, 2],                        6: [3, 2],
               10: [0, 3], 9:  [1, 3], 8: [2, 3], 7: [3, 3]}


# (square_nb, front/back, up/down)
page_squares = {hv1: [[(5, b, u), (2, b, d)],
                      [(1, b, d), (11, b, u)]]}

dest_dimension = (page_length * 4, page_length * 4)


def paste0(im, loc, dest):
    square_number, side, up = loc
    square_loc = square_locs[square_number]
    if up == 'd':
        im = im.rotate(180)
    left = square_loc[0] * page_length
    top = square_loc[1] * page_length
    dest.paste(im, (left, top))


def copy(page_name, page_part, upside_down=False):
    im = Image.open(Path(f'../{page_name}.tif'))
    width, height = im.size
    wm, hm = width_height_multiplicator(page_name)
    crop_width = width * wm
    crop_height = height * hm
    crop_x, crop_y = page_part_coordinates(page_name, page_part)
    print(page_name, page_part, wm, hm, crop_x, crop_y, upside_down)
    left = crop_x * crop_width
    right = left + crop_width
    upper = crop_y * crop_height
    lower = upper + crop_height
    im = im.crop((left, upper, right, lower))
    if upside_down:
        im = im.rotate(180)
    return im


def paste(im, dest, square_number):
    square_loc = square_locs[square_number]
    im_width, im_height = im.size
    left_offset = math.floor((page_length - im_width) / 2)
    top_offset = math.floor((page_length - im_height) / 2)
    left = left_offset + square_loc[0] * page_length
    top = top_offset + square_loc[1] * page_length
    dest.paste(im, (left, top))


def assemble():
    assembled = []
    for square_pages in [square_pages_front, square_pages_back]:
        dest_img = Image.new('L', dest_dimension, color=255)
        assembled.append(dest_img)
        for square_number, (source, *s) in square_pages.items():
            # for square_number, (source, *s) in list(square_pages.items())[:8]:
            page_name, page_part, up = source
            copied = copy(page_name, page_part, up == d)
            paste(copied, dest_img, square_number)
    return assembled


def assemble0():
    front = Image.new('L', dest_dimension, color=255)
    back = Image.new('L', dest_dimension, color=255)
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
                side = loc[1]
                dest = front if side == 'f' else back
                paste0(cropped, loc, dest)
    back.show()


def main():
    # cropped = crop(r4, pa)
    # cropped = crop(h2, pb)
    # cropped = crop(t3, pd)
    # cropped.show()
    assembled = assemble()
    assembled[0].show()
    assembled[1].show()


main()
