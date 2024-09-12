import string
from base64 import b64encode
from io import BytesIO
import easyocr
from PIL import Image
from twocaptcha import TwoCaptcha
from ..config import API_KEY_2CAPTCHA


class CaptchaSolver:
    def __init__(self):
        eng_alb_lowercase = list(string.ascii_lowercase)
        eng_alb_uppercase = list(string.ascii_lowercase.upper())
        numbers = [f"{i}" for i in range(0, 10)]

        self.reader = easyocr.Reader(['en'], model_storage_directory="./ocr_models/maybank/model")
        self.allowlist = eng_alb_lowercase + eng_alb_uppercase + numbers
        self.server_captcha = TwoCaptcha(apiKey=API_KEY_2CAPTCHA, pollingInterval=3)

    async def get_from_ocr(self, image: Image):
        pixels = image.load()

        for i in range(image.size[0]):  # Меняем пиксели на черные ниже диапазона 185
            for j in range(image.size[1]):
                if pixels[i, j][0] < 185 and pixels[i, j][1] < 185 and pixels[i, j][2] < 185:
                    image.putpixel((i, j), (0, 0, 0))

        io = BytesIO()
        image.save(io, format='PNG')

        # Распознаем текст
        ocr_results = self.reader.readtext(image=io.getvalue(), detail=0, allowlist=self.allowlist)
        captcha = "".join(ocr_results)

        return captcha

    async def get_from_2captcha(self, image: Image):
        b64_file = b64encode(image.to_bytes()).decode('utf-8')
        response_2c = self.server_captcha.normal(file=b64_file,
                                          minLen=6,
                                          maxLen=6,
                                          caseSensitive=1,
                                          hintText="На фото есть линии, они мешают распознать текст правильно, "
                                                   "учтите это пожалуйста")
        return response_2c["code"]