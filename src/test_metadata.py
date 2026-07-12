from pprint import pprint
import piexif

reference_img = r"E:\CODE\polaroid-z2300-photo-format-adapter\test\test_data\reference\PICT0016.JPG"

metadata = piexif.load(reference_img)
pprint(metadata['Exif'])