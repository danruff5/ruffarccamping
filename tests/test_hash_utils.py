from backend.hash_utils import calculate_dhash, hamming_distance
from PIL import Image, ImageDraw

def test_hamming_distance():
    assert hamming_distance("0000000000000000", "0000000000000000") == 0
    assert hamming_distance("ffffffffffffffff", "0000000000000000") == 64
    assert hamming_distance("0f0f0f0f0f0f0f0f", "f0f0f0f0f0f0f0f0") == 64
    assert hamming_distance("1111111111111111", "0111111111111111") == 1

def test_dhash_calculation():
    # Create two identical patterned images and one different
    img1 = Image.new("RGB", (100, 100), color="white")
    draw1 = ImageDraw.Draw(img1)
    draw1.rectangle([20, 20, 80, 80], fill="black")
    
    img2 = Image.new("RGB", (100, 100), color="white")
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle([20, 20, 80, 80], fill="black")
    
    img3 = Image.new("RGB", (100, 100), color="white")
    draw3 = ImageDraw.Draw(img3)
    draw3.line([0, 0, 100, 100], fill="black", width=5)
    
    h1 = calculate_dhash(img1)
    h2 = calculate_dhash(img2)
    h3 = calculate_dhash(img3)
    
    assert len(h1) == 16
    assert h1 == h2
    assert hamming_distance(h1, h3) > 0

