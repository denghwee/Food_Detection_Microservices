import io
import cloudinary.uploader
from PIL import Image

def upload_image_to_cloudinary(image: Image.Image, folder="food-detection"):
    """
    Upload PIL Image to Cloudinary and return secure URL
    """
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    result = cloudinary.uploader.upload(
        buffer,
        folder=folder,
        resource_type="image"
    )

    return result.get("secure_url")
