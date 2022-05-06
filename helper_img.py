from PIL import Image
from soviby import helper
import io


def get_img_bytes(img: Image, format: str = 'PNG'):
    img_bytes = io.BytesIO()
    img.save(img_bytes, format)
    return img_bytes.getvalue()


def get_md5_by_img(img: Image, format: str = 'PNG'):
    return helper.get_md5(get_img_bytes(img))
