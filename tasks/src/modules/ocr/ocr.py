import string
from base64 import b64encode
from io import BytesIO
from warnings import filterwarnings
import easyocr
from PIL import Image
from twocaptcha import TwoCaptcha
from tasks.src.config import API_KEY_2CAPTCHA, ROOT_DIR

filterwarnings("ignore", category=FutureWarning, message=r".*You are using `torch.load` with `weights_only=False`.*")


class CaptchaSolver:
    def __init__(self, model_name: str):
        eng_alb_lowercase = list(string.ascii_lowercase)
        eng_alb_uppercase = list(string.ascii_lowercase.upper())
        numbers = [f"{i}" for i in range(0, 10)]
        model_dir = ROOT_DIR + f"/modules/ocr/ocr_models/{model_name}/model"

        self.reader = easyocr.Reader(['en'], model_storage_directory=model_dir, gpu=False)
        self.allowlist = eng_alb_lowercase + eng_alb_uppercase + numbers
        self.server_captcha = TwoCaptcha(apiKey=API_KEY_2CAPTCHA, pollingInterval=5)

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
        io = BytesIO()
        image.save(io, format='PNG')
        bytes_image = io.getvalue()
        b64_file = b64encode(bytes_image).decode('utf-8')
        response_2c = self.server_captcha.normal(b64_file,
                                                 minLen=6,
                                                 maxLen=6,
                                                 caseSensitive=1,
                                                 lang="en",
                                                 hintText="На фото есть линии, они мешают распознать текст правильно, "
                                                          "также учтите регистр пожалуйста!")
        return response_2c["code"]
