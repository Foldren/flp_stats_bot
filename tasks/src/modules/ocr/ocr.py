import string
from asyncio import sleep, run
from base64 import b64encode
from io import BytesIO
from warnings import filterwarnings
# import easyocr
from PIL import Image
from httpx import AsyncClient
from twocaptcha import TwoCaptcha
# from config import API_KEY_2CAPTCHA, ROOT_DIR
from anticaptchaofficial.imagecaptcha import *

filterwarnings("ignore", category=FutureWarning, message=r".*You are using `torch.load` with `weights_only=False`.*")


class CaptchaSolver:
    def __init__(self, model_name: str = None):
        pass
        # if model_name is not None:
        #     eng_alb_lowercase = list(string.ascii_lowercase)
        #     eng_alb_uppercase = list(string.ascii_lowercase.upper())
        #     numbers = [f"{i}" for i in range(0, 10)]
        #     model_dir = ROOT_DIR + f"/modules/ocr/ocr_models/{model_name}/model"
        #
        #     self.reader = easyocr.Reader(['en'], model_storage_directory=model_dir, gpu=False)
        #     self.allowlist = eng_alb_lowercase + eng_alb_uppercase + numbers
        #     self.server_captcha = TwoCaptcha(apiKey=API_KEY_2CAPTCHA, pollingInterval=5)

    async def __get_b64_from_image(self, image: Image) -> str:
        io = BytesIO()
        image.save(io, format='PNG')
        bytes_image = io.getvalue()
        b64_file = b64encode(bytes_image).decode('utf-8')

        return b64_file

    # async def get_from_ocr(self, image: Image):
    #     pixels = image.load()
    #
    #     for i in range(image.size[0]):  # Меняем пиксели на черные ниже диапазона 185
    #         for j in range(image.size[1]):
    #             if pixels[i, j][0] < 185 and pixels[i, j][1] < 185 and pixels[i, j][2] < 185:
    #                 image.putpixel((i, j), (0, 0, 0))
    #
    #     io = BytesIO()
    #     image.save(io, format='PNG')
    #
    #     # Распознаем текст
    #     ocr_results = self.reader.readtext(image=io.getvalue(), detail=0, allowlist=self.allowlist)
    #     captcha = "".join(ocr_results)
    #
    #     return captcha

    async def get_from_2captcha(self, image: Image):
        b64_file = self.__get_b64_from_image(image)
        response_2c = self.server_captcha.normal(b64_file,
                                                 minLen=6,
                                                 maxLen=6,
                                                 caseSensitive=1,
                                                 lang="en",
                                                 hintText="На фото есть линии, они мешают распознать текст правильно, "
                                                          "также учтите регистр пожалуйста!")
        return response_2c["code"]

    async def get_from_capsola_space(self, image: Image):
        b64_file = self.__get_b64_from_image(image)

        headers = {
            'Content-type': 'application/json',
            'X-API-Key': "fb60806f-3361-4269-810c-9dd5ee1883fd"
        }

        async with AsyncClient() as client:
            response = await client.post(url='https://api.capsola.cloud/create',
                                         json={'type': 'TextCaptcha', 'task': b64_file},
                                         headers=headers)
            create_r = response.json()

            if create_r['status'] == 1:
                task_id = create_r['response']
                while True:
                    await sleep(2)
                    response = await client.post(url='https://api.capsola.cloud/result',
                                                 json={'id': task_id},
                                                 headers=headers)
                    result_r = response.json()

                    if result_r['status'] == 1:
                        print(result_r)
                        break
                    if (result_r['status'] == 0) and (result_r['response'] != 'CAPCHA_NOT_READY'):
                        print(result_r)
                        break

    async def get_from_anticaptcha(self, image: Image) -> str | None:
        solver = imagecaptcha()
        solver.set_key("850f186c1cd75cb60e5fc84122fe4fda")

        io = BytesIO()
        image.save(io, format='PNG')
        bytes_image = io.getvalue()

        # Specify softId to earn 10% commission with your app.
        # Get your softId here: https://anti-captcha.com/clients/tools/devcenter
        solver.set_soft_id(0)
        solver.set_case(True)  # case sensitivity
        solver.set_minLength(6)  # minimum captcha text length
        solver.set_maxLength(6)  # maximum captcha text length

        captcha_text = solver.solve_and_return_solution(file_path=None, body=bytes_image)

        if captcha_text != 0:
            return captcha_text
        else:
            return None
