import io

import qrcode
import qrcode.image.svg


def generate_qr_code(data):
    qr_image = qrcode.make(data, image_factory=qrcode.image.svg.SvgImage)
    byte_arr = io.BytesIO()
    qr_image.save(byte_arr)

    qr_svg = byte_arr.getvalue().decode().replace("\n", "")

    return qr_svg
