import sys
import math
from pathlib import Path
from itertools import product
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageOps

BUILD = Path('build')

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
                      3:  [(h3, pb, d), (r3, pd, d)],
                      4:  [(h3, pa, d), (r3, pc, d)],
                      5:  [(h4, pa, u), (v2, pb, u)],
                      6:  [(t3, pc, d), (v3, pd, d)],
                      7:  [(t3, pa, d), (v3, pb, d)],
                      8:  [(h4, pb, d), (v4, pb, u)],
                      9:  [(h3, pc, d), (r3, pa, d)],
                      10: [(h3, pd, d), (r3, pb, d)],
                      11: [(h2, pb, u), (v4, pa, u)],
                      12: [(t3, pb, d), (v3, pa, d)],
                      13: [(cover, pall, u)]
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
                     13: [(cover2, pall, d)]
                     }

@dataclass
class PagePart:
    page: str
    part: str
    orientation: str | None = None
    image: Image.Image | None = None
    def filename(self):
        return f'{self.page}.tif'
    def __str__(self):
        return f' {self.page} {self.part}'

page_parts_front = {k:[PagePart(*val) for val in vals]
                    for k,vals in square_pages_front.items()}
page_parts_back = {k:[PagePart(*val) for val in vals]
                    for k,vals in square_pages_back.items()}

# unfolded squares
#  1  2  3  4
# 12 13     5
# 11        6
# 10  9  8  7
square_locs = {1:  [0, 0], 2:  [1, 0], 3: [2, 0], 4: [3, 0],
               12: [0, 1], 13: [1, 1],            5: [3, 1],
               11: [0, 2],                        6: [3, 2],
               10: [0, 3], 9:  [1, 3], 8: [2, 3], 7: [3, 3]}


def square_size(square_number):
    return 2 if square_number == 13 else 1


def crop(im, page_name, page_part, rotate180=False, path=Path('..')):
    width, height = im.size
    wm, hm = width_height_multiplicator(page_name)
    crop_width = width * wm
    crop_height = height * hm
    crop_x, crop_y = page_part_coordinates(page_name, page_part)
    # print(page_name, page_part, wm, hm, crop_x, crop_y, rotate180)
    left = crop_x * crop_width
    right = left + crop_width
    upper = crop_y * crop_height
    lower = upper + crop_height
    # print(left, right, upper, lower)
    im = im.crop((left, upper, right, lower))
    if rotate180:
        im = im.rotate(180)
    return im


def copy(page_name, page_part, rotate180=False, path=Path('..')):
    im = Image.open(path / f'{page_name}.tif')
    return crop(im, page_name, page_part, rotate180, path)


def paste(im, dest, square_number):
    square_loc = square_locs[square_number]
    im_width, im_height = im.size
    square_length = square_size(square_number)
    page_length = math.floor(im_width / square_length)
    correct_page_length = page_length * square_size(square_number)
    left_offset = math.floor((correct_page_length - im_width) / 2)
    top_offset = math.floor((correct_page_length - im_height) / 2)
    left = left_offset + square_loc[0] * page_length
    top = top_offset + square_loc[1] * page_length
    dest.paste(im, (left, top))


def assemble_for_print(source_path):
    print('copying from', source_path)
    assembled = []
    for square_pages in [square_pages_front, square_pages_back]:
        dest_img = None
        for square_number, (source, *s) in square_pages.items():
            # for square_number, (source, *s) in list(square_pages.items())[:8]:
            page_name, page_part, up = source
            copied = copy(page_name, page_part, up == d, source_path)
            if not dest_img:
                w, h = copied.size
                dest_img = Image.new('L', (w*4, h*4), color=255)
                assembled.append(dest_img)
            print('copied', page_name, copied.size)
            paste(copied, dest_img, square_number)
        if dest_img:
            draw = ImageDraw.Draw(dest_img)
            width, height = dest_img.size
            # draw.rectangle([0, 0, width - 1, height - 1],
            #                width=3, outline='black')
            points = [math.floor(i) for i in [width * 0.25, height * 0.25,
                                            width * 0.75, height * 0.75]]
            draw.rectangle(points, width=3)
    return assembled


def save_image(image, name, build_path=BUILD):
    '''Saves images to build dir'''
    path = build_path / name
    if not build_path.exists():
        build_path.mkdir(parents=True, exist_ok=True)
    image = image.convert('1')
    image.save(path)
    print(f'saved {path}')
    return image

def draw_corner_squares(image, margin_px):
    draw = ImageDraw.Draw(image)
    oth = image.size[0] - margin_px
    for point in product([0, oth], [0, oth]):
        points = point + tuple([c + margin_px for c in point])
        draw.rectangle(points, width=5)

def expand_into_margins(image, margin_px):
    width, height = image.size
    box = (margin_px, margin_px, margin_px+1, height - margin_px)
    destination = (margin_px-5, margin_px)
    cropped = image.crop(box)
    image.paste(cropped, destination)

def save_as_a3_pdf(images, build_path=BUILD):
    dpi = 1200
    a3_width = 297
    # a3_height = 420
    im_length_px = images[0].size[0]  # a square
    mm_per_inch = 25.4
    im_length_mm = (im_length_px / dpi) * mm_per_inch
    margin_mm = (a3_width - im_length_mm) / 2
    margin_px = math.floor((margin_mm / mm_per_inch) * dpi)
    margin_images = []
    for im in images:
        expanded = ImageOps.expand(im, border=margin_px, fill='white')
        draw_corner_squares(expanded, margin_px)
        # expand_into_margins(expanded, margin_px)
        margin_images.append(expanded)
    [front, *rest] = margin_images
    path = build_path / 'fleur.pdf'
    front.save(path, save_all=True, resolution=dpi,
               append_images=rest)
    print(f'saved {path}')


def assemble_for_print_and_save(path=Path('..')):
    # cropped = crop(r4, pa)
    # cropped = crop(h2, pb)
    # cropped = crop(t3, pd)
    # cropped.show()
    assembled = assemble_for_print(path)
    front = save_image(assembled[0], 'front.tif', path)
    back = save_image(assembled[1], 'back.tif', path)
    save_as_a3_pdf([front, back], path)
    # front.show()
    # back.show()


def page_size(page_name, square_length):
    width = square_length
    height = square_length
    if is_full_page(page_name) or is_vertical(page_name):
        height *= 2
    if is_full_page(page_name) or not is_vertical(page_name):
        width *= 2
    return (width, height)


def perpendicular(page_name1, page_name2):
    if is_full_page(page_name1) or is_full_page(page_name2):
        return False
    return is_vertical(page_name1) != is_vertical(page_name2)

def copy_image_part(original: PagePart, target: PagePart, images):
    if not original.image:
        raise Exception(f'Missing image for {original}')
    copied = original.image
    length = copied.size[0]
    print(f'{original} length: {length}')
    t_p_size = page_size(target.page, length)
    if target.page not in images:
        images[target.page] = Image.new('L', t_p_size,
                                        color=255)
    t_image = images[target.page]
    x, y = page_part_coordinates(target.page, target.part)
    t_left_top = (x * length, y * length)
    rotate = perpendicular(original.page, target.page)
    # h2 pa -> v2 pa rotate 180
    # h2 pb -> v4 pa rotate 180
    # h4 pa -> v3 pb rotate 180
    # h4 pb -> v3 pb rotate 180
    if rotate:
        copied = copied.rotate(180)
    print(f'copy {original} to {target}', t_left_top, t_p_size, rotate)
    t_image.paste(copied, t_left_top)

def assemble_pages(path=Path('..')):
    """Takes original page images from path
       and creates the missing page images
       by copying the parts of the the originals
       to the other pages where they appear
       so they can be read sequentially in a presentation
       without having a physical flexagon.
       The original is considered to be the first page
       in the lists of square_pages_front and _back.
       Images are saved to the build dir.
    """
    # page_sizes = build_page_sizes()
    images = {}
    for page_parts in [page_parts_front, page_parts_back]:
        for pps in page_parts.values():
            original = next(p for p in pps if (path/p.filename()).exists())
            original.image = copy(original.page, original.part, False, path)
            targets = pps.copy()
            targets.remove(original)
            # (original, *targets) = pps
            o_im = Image.open(path/original.filename())
            # print(path / original.filename())
            save_image(o_im, original.filename())
            if targets:
                for target in targets:
                    copy_image_part(original, target, images)
    for page_name, image in images.items():
        save_image(image, f'{page_name}.tif')

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'p':
        print('make pages')
        # assemble_pages(Path('../../fleur-oeil/dessins'))
        assemble_pages(Path('../dessins'))
    else:
        # assemble_for_print_and_save(Path('build-fleur-oeil'))
        assemble_for_print_and_save(Path('build-fleur'))
