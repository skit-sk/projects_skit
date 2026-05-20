from PIL import Image


def make_collage(input_paths, output_path):
    imgs = [Image.open(p) for p in input_paths]
    heights = [im.height for im in imgs]
    max_w = max(im.width for im in imgs)
    total_h = sum(heights)

    collage = Image.new("RGB", (max_w, total_h), (0, 0, 0))
    y = 0
    for im in imgs:
        x = (max_w - im.width) // 2
        collage.paste(im, (x, y))
        y += im.height

    collage.save(output_path, "PNG")
    return output_path
