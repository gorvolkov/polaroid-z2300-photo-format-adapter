"""
Script to fix images for Polaroid Z2300 printer
Converts images to 3648x2736 (landscape) or 2736x3648 (portrait)
and fixes EXIF data.
"""

import os
import sys

from PIL import Image
import piexif

TARGET_LANDSCAPE = 3648, 2736
TARGET_PORTRAIT = 2736, 3648
TARGET_RATIO_LANDSCAPE = TARGET_LANDSCAPE[0] / TARGET_LANDSCAPE[1]
TARGET_RATIO_PORTRAIT = TARGET_PORTRAIT[0] / TARGET_PORTRAIT[1]

def calc_new_sizes(image_sizes: tuple, target_sizes: tuple):
    """
    Расчитывает новое соотношение сторон для того,
    чтобы вписать изображение в прямоугольник заданных размеров
    """
    width, height = image_sizes
    ratio = width / height
    target_width, target_height = target_sizes
    target_ratio = TARGET_RATIO_LANDSCAPE if target_width > target_height else TARGET_RATIO_PORTRAIT

    # картинка более вытянутая, чем целевая => ограничение по длине
    if ratio > target_ratio:
        resize_coef = target_width / width
        new_width = target_width
        new_height = height * resize_coef
    # картинка менее вытянутая, чем целевая => ограничичение по высоте
    else:
        resize_coef = target_height / height
        new_width = width * resize_coef
        new_height = target_height

    # для расчетов в пикселях округляем и преобразуем в integer
    return int(round(new_width)), int(round(new_height))


def fit_image(img: Image, target_sizes) -> Image:
    """
    Вписывает изображение в прямоугольник заданных размеров.
    Оставшееся пространство заполняется белым цветом
    """

    # Вычисляем новые размеры
    new_width, new_height = calc_new_sizes(img.size, target_sizes)

    # Масштабируем изображение
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Создаем белый холст нужного размера
    new_img = Image.new('RGB', target_sizes, 'white')

    # Вычисляем позицию для центрирования
    x_offset = (target_sizes[0] - new_width) // 2
    y_offset = (target_sizes[1] - new_height) // 2

    # Вставляем изображение на холст
    new_img.paste(img_resized, (x_offset, y_offset))

    return new_img


def update_metadata(image_path, target_sizes):
    """Обновляет метаданные изображения"""
    try:
        # Загружаем существующие EXIF данные
        exif_dict = piexif.load(image_path)

        target_width, target_height = target_sizes[0], target_sizes[1]

        # Обновляем теги размера в Exif IFD
        exif_dict['Exif'][piexif.ExifIFD.PixelXDimension] = target_width
        exif_dict['Exif'][piexif.ExifIFD.PixelYDimension] = target_height

        # Обновляем основные теги размера в Image IFD (0th)
        exif_dict['0th'][piexif.ImageIFD.ImageWidth] = target_width
        exif_dict['0th'][piexif.ImageIFD.ImageLength] = target_height

        # Конвертируем обратно в байты
        piexif.dump(exif_dict)
        print(f"  ✓ EXIF updated")

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

    # путь для обработанного изображения
    processed_img_path = filepath if output_dir is None else os.path.join(output_dir, os.path.basename(filepath))

    try:
        with Image.open(filepath) as img:
            original_size = img.size
            print(f"Processing {filepath} ({original_size[0]}x{original_size[1]})")

            # выбираем, горизонтальное или вертикальное изображение обрабатываем
            if original_size[0] > original_size[1]:
                target = TARGET_LANDSCAPE
            else:
                target = TARGET_PORTRAIT

            if original_size == target:
                print(f"  Size is already correct: {target}")
                img.save(processed_img_path)

            else:
                print(f"  Fit image to a target size")
                fitted_img = fit_image(img, target)
                fitted_img.save(processed_img_path)
                fitted_img.close()
            print(f"  Image saved: {processed_img_path}")

            # Update EXIF
            update_metadata(processed_img_path, target)
            return True

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def process_folder(directory: str=".", output_dir: str=None):
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
        sys.exit(0)

    # Create output directory if needed
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    processed,failed = 0, 0

    for f in files:
        filepath = os.path.join(directory, f)
        if process_image(filepath, output_dir):
            processed += 1
        else:
            failed += 1

    print(f"\nDone! Processed: {processed}, Failed: {failed}")
    sys.exit(0)



if __name__ == "__main__":
    process_folder()