import numpy as np
import time

def mandelbrot(c, max_iter):
    z = 0
    for n in range(max_iter):
        if abs(z) > 2:
            return n / max_iter
        z = z * z + c
    return 1


def generate_mandelbrot(center_x, center_y, zoom, size=70, max_iter=256):
    zoom = 1.05 ** (zoom - 1)
    pixels = np.zeros((size, size))
    for x in range(size):
        for y in range(size):
            re = (x - size / 2) / (0.5 * zoom * size) + center_x
            im = (y - size / 2) / (0.5 * zoom * size) + center_y
            c = complex(re, im)
            pixels[y, x] = mandelbrot(c, max_iter)
    return pixels


def run(n):
    # Use this to record an entire sequence. Run a screen recorder while this runs and then
    # export the frames of that move at 0.1fps, giving you one iteration per frame. You can then
    # combine these frames into a video using ffmpeg. Maybe there's a better way to do this!
    for i in range(n):
        start = time.time()
        S1 = i + 1
        _ = A3
        to_sleep = 10 - time.time() + start
        print(to_sleep)
        time.sleep(to_sleep)
