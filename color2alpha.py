import sys
import os
import time
import PIL.Image
import numpy as np

ENABLE_CROPPING = True

def find_crops(sum_alpha):
    START_DENSITY = 5.
    ADDED_MARGIN = 59 # 0.5cm @300dpi
    n = sum_alpha.shape[0]
    first = np.argmax(sum_alpha > START_DENSITY)
    inverse = sum_alpha[::-1]
    last = n - np.argmax(inverse > START_DENSITY)
    first = max(first - ADDED_MARGIN, 0)
    last = min(last + ADDED_MARGIN, n)
    return (first, last)

def color_to_alpha(input_filename, output_filename, bg_color_rgb):
    MAX_CHANNEL = 255
    MAX_ALPHA = 255
    input_image = PIL.Image.open(input_filename)
    input = np.asarray(input_image)

    bg_color = np.array(bg_color_rgb, dtype=np.uint8)

    # Inversing the formula Img = alpha * Fg + (1-alpha) * Bg
    alpha_per_channel = (0
                        + np.greater(input, bg_color)
                        * np.divide(input - bg_color, MAX_CHANNEL - bg_color,
                                    where=np.greater(MAX_CHANNEL - bg_color, 0))
                        + np.less(input, bg_color)
                        * np.divide(bg_color - input, bg_color,
                                    where=np.greater(bg_color,0)))
    alpha = np.amax(alpha_per_channel, axis=2, keepdims=True)
    foreground = np.divide(input - (1-alpha) * bg_color, alpha,
                           where=np.greater(alpha, 1e-4))

    # Output has 4 channels (RGBA)
    output = np.zeros([input.shape[0],input.shape[1],4], dtype=np.uint8)
    # Set RGB channels
    output[:, :, 0:3] = foreground
    # Set alpha channel
    output[:, :, 3:4] = alpha * MAX_ALPHA

    if ENABLE_CROPPING:
        crop_0 = find_crops(np.sum(alpha,axis=(1,2)))
        crop_1 = find_crops(np.sum(alpha,axis=(0,2)))
        output = output[crop_0[0]:crop_0[1],crop_1[0]:crop_1[1]]

    output_image = PIL.Image.fromarray(output)
    output_image.save(output_filename, dpi=input_image.info.get('dpi'),
                      exif=input_image.info.get('exif'))

def convert_directory(dir_path, bg_color_rgb):
    print(f'Processing all files in {dir_path}')
    for filename in os.scandir(dir_path):
        if not filename.is_file():
            continue
        if not filename.path.lower().endswith('.jpg'):
            continue
        output_fname = filename.path[:len(filename.path) - 4] + '-white-to-alpha.png'
        color_to_alpha(filename.path, output_fname, bg_color_rgb)
        print(f'Created {output_fname}')


# Color to make transparent.
BG_COLOR_RGB = [255, 255, 255] # white

if len(sys.argv) == 3:
    color_to_alpha(sys.argv[1], sys.argv[2], BG_COLOR_RGB)
elif len(sys.argv) == 2:
    convert_directory(sys.argv[1], BG_COLOR_RGB)
elif len(sys.argv) == 1:
    convert_directory(os.path.dirname(sys.argv[0]), BG_COLOR_RGB)
else:
    print("Incorrect usage usage, should be color2alpha input.jpg output.png")

print("Operation complete, closing in 3 seconds.")
time.sleep(3)
