from PIL import Image

def calculate_dhash(image_path_or_pil_img) -> str:
    """
    Computes a 64-bit difference hash (dHash) for an image.
    Returns a 16-character hexadecimal string representation.
    """
    if isinstance(image_path_or_pil_img, str):
        img = Image.open(image_path_or_pil_img)
    else:
        img = image_path_or_pil_img
        
    # Convert to grayscale and resize to 9x8
    img = img.convert("L").resize((9, 8), Image.Resampling.BILINEAR)
    pixels = list(img.getdata())
    
    # Compute difference between adjacent pixels in a row
    difference = []
    for row in range(8):
        for col in range(8):
            pixel_left = pixels[row * 9 + col]
            pixel_right = pixels[row * 9 + col + 1]
            difference.append(pixel_left > pixel_right)
            
    # Convert binary list to hex string
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2**(index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].zfill(2))
            decimal_value = 0
            
    return "".join(hex_string)

def hamming_distance(h1: str, h2: str) -> int:
    """
    Computes the Hamming distance between two 16-character hex dHashes.
    """
    if not h1 or not h2:
        return 999
    try:
        return (int(h1, 16) ^ int(h2, 16)).bit_count()
    except ValueError:
        return 999
