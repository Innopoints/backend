def transform(color):
    color /= 255;
    if color <= 0.03928:
        return color / 12.92
    else:
        return ((color + 0.055) / 1.055) ** 2.4


def luminance(r, g, b):
    return (transform(r) * 0.2126
          + transform(g) * 0.7152
          + transform(b) * 0.0722)


def get_contrast(background, content):
    '''Return the contrast between the background and content colors,
       specified as (r, g, b) tuples in range [0; 255].'''
    return ((luminance(*background) + 0.05)
          / (luminance(*content) + 0.05))


def rgb_to_hsl(r, g, b):
    '''Convert the RGB color (r, g, b in range(0, 256))
       to the HSL color (h, s, l in range(0, 1)).'''
    r /= 255
    g /= 255
    b /= 255

    max_comp = max(r, g, b)
    min_comp = min(r, g, b)

    l = (min_comp + max_comp) / 2

    if (max_comp == min_comp):
        h = s = 0
    else:
        delta = max_comp - min_comp
        s = 2 - max_comp - min_comp if l > 0.5 else delta / (max_comp + min_comp)

        if max_comp == r:
            h = (g - b) / delta + (6 if g < b else 0)
        elif max_comp == g:
            h = (b - r) / delta + 2
        else:
            h = (r - g) / delta + 4

        h /= 6

    return h, s, l


def get_background(color):
    '''Return the optimal background color for the color given as
       a hex string without the hash.'''
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)

    h, s, l = rgb_to_hsl(r, g, b)
    contrast = get_contrast((255, 255, 255), (r, g, b))

    if contrast > 1.08:
        bg_h, bg_s, bg_l = h, s, 0.97
    else:
        bg_h, bg_s, bg_l = h, s, 0.9

    return f'hsl({int(bg_h * 360)}, {bg_s * 100}%, {bg_l * 100}%)'

if __name__ == '__main__':
    print(get_background('ff00ff'))
