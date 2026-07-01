"""
Script to fix images for Polaroid Z2300 printer
Converts images to 3648x2736 (landscape) or 2736x3648 (portrait)
and fixes EXIF data.
"""

import os
from PIL import Image
import piexif

TARGET_LANDSCAPE = (3648, 2736)
TARGET_PORTRAIT = (2736, 3648)


def fix_image_size(img, target_size, background_color=(255, 255, 255)):
    """
    Resize image maintaining aspect ratio and add padding to reach target size.

    Args:
        img: PIL Image object
        target_size: tuple (width, height)
        background_color: RGB tuple for padding

    Returns:
        PIL Image object with target size
    """

    # Create new image with target size
    new_img = Image.new('RGB', target_size, background_color)

    # Resize maintaining aspect ratio
    img_copy = img.copy()
    img_copy.thumbnail(target_size, Image.Resampling.LANCZOS)

    # Center the image
    x = (target_size[0] - img_copy.size[0]) // 2
    y = (target_size[1] - img_copy.size[1]) // 2
    new_img.paste(img_copy, (x, y))

    return new_img



def update_exif(image_path, width, height):
    """
    Update EXIF PixelXDimension and PixelYDimension using piexif.

    Args:
        image_path: Path to image file
        width: New width
        height: New height

    Returns:
        bytes: Updated EXIF data or None if failed
    """
    try:
        # Загружаем существующие EXIF данные
        exif_dict = piexif.load(image_path)

        # Обновляем теги размера в Exif IFD
        exif_dict['Exif'][piexif.ExifIFD.PixelXDimension] = width
        exif_dict['Exif'][piexif.ExifIFD.PixelYDimension] = height

        # Обновляем основные теги размера в Image IFD (0th)
        exif_dict['0th'][piexif.ImageIFD.ImageWidth] = width
        exif_dict['0th'][piexif.ImageIFD.ImageLength] = height

        # Конвертируем обратно в байты
        exif_bytes = piexif.dump(exif_dict)

        print(f"  ✓ EXIF updated: {width}x{height}")
        return exif_bytes

    except Exception as e:
        print(f"Warning: Could not update EXIF for {image_path}: {e}")
        return None

def process_image(filepath, output_dir=None):
    """
    Process a single image: resize if needed and fix EXIF.

    Args:
        filepath: Path to image file
        output_dir: Directory to save processed image (None = overwrite)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with Image.open(filepath) as img:
            original_size = img.size
            print(f"Processing {filepath} ({original_size[0]}x{original_size[1]})")

            # Determine target size
            if original_size[0] > original_size[1]:
                target = TARGET_LANDSCAPE
            else:
                target = TARGET_PORTRAIT

            # Check if resizing is needed
            if original_size == target:
                print(f"  Size is already correct: {target}")
                processed_img = None
                final_size = original_size
            else:
                print(f"  Resizing to {target[0]}x{target[1]}")
                processed_img = fix_image_size(img, target)
                final_size = target

                # Save the processed image
                save_path = filepath if output_dir is None else os.path.join(output_dir, os.path.basename(filepath))
                processed_img.save(save_path, quality=95)
                print(f"  Image saved: {processed_img.size[0]}x{processed_img.size[1]}")

                # Update filepath to saved path for EXIF update
                filepath = save_path

            # Update EXIF
            update_exif(filepath, final_size[0], final_size[1])

            return True

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def process_directory(directory, output_dir=None):
    """
    Process all JPG/JPEG images in a directory.

    Args:
        directory: Directory containing images
        output_dir: Directory to save processed images (None = overwrite)

    Returns:
        tuple: (processed_count, failed_count)
    """
    # Get all image files
    extensions = ('.jpg', '.jpeg')
    files = [f for f in os.listdir(directory)
             if f.lower().endswith(extensions)]

    if not files:
        print(f"No JPG files found in {directory}")
        return (0, 0)

    # Create output directory if needed
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    processed = 0
    failed = 0

    for f in files:
        filepath = os.path.join(directory, f)
        if process_image(filepath, output_dir):
            processed += 1
        else:
            failed += 1

    return (processed, failed)


def main():
    """Main function when script is run directly."""
    processed, failed = process_directory('.')
    print(f"\nDone! Processed: {processed}, Failed: {failed}")


if __name__ == "__main__":
    main()