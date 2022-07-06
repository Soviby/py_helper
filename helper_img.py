import io
import os
from PIL import Image


def get_img_bytes(img: Image, format: str = 'PNG'):
    img_bytes = io.BytesIO()
    img.save(img_bytes, format)
    return img_bytes.getvalue()


def get_md5_by_img(img: Image, format: str = 'PNG'):
    return get_md5(get_img_bytes(img))


def is_want_img_format(path: str, check_file_format_List: list = ['png', 'jpg']):
    format = os.path.splitext(path)[1][1:]
    for f in check_file_format_List:
        if f.lower() == format:
            return True
    return False

def get_md5(data: bytes):
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()
