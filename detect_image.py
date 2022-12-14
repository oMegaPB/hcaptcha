import typing as t
from io import BytesIO
import pathlib, random

import requests
from PIL import Image

xJsonT = t.Dict[str, t.Any]

class KindaComputerVision:
    def ensure_func(self, question: str) -> t.Callable:
        print(question)
        data = {"appleonat": self.detect_apple_on_a_tree, "daisy": self.detect_daisy}
        for x, y in data.items():
            if x in question.replace(" ", ""):
                print(y)
                return y
        return self.random_answers
    
    def random_answers(self, tasklist: t.List[xJsonT]) -> xJsonT:
        return {x["task_key"]: str(bool(random.randint(0, 1))).lower() for x in tasklist}
    
    def detect_daisy(self, tasklist: t.List[xJsonT]) -> xJsonT:
        answers = {}
        for x in tasklist:
            im = Image.open(BytesIO(requests.get(f'{x["datapoint_uri"]}').content))
            
            white_check: t.Callable[[int, int, int], bool] = lambda r, g, b: r > 170 and g > 170 and b > 170
            orange_check: t.Callable[[int, int, int], bool] = lambda r, g, b: r > 220 and g < 160 and g > 70 and b < 70
            
            pixels = sum([list(im.getdata())[i * im.size[0]:(i + 1) * im.size[0]] for i in range(im.size[1])], [])

            white_pixels = [x for x in pixels if white_check(*x)]
            orange_pixels = [x for x in pixels if orange_check(*x)]
            
            coeff = (len(white_pixels) / len(pixels)) * 100
            if len(orange_pixels) > 350:
                coeff -= 30
            if coeff > 5:
                answers[x["task_key"]] = "true"
            else:
                answers[x["task_key"]] = "false"

        return answers

    def detect_apple_on_a_tree(self, tasklist: t.List[xJsonT]) -> xJsonT:
        answers = {}
        for y, x in enumerate(tasklist): # type: ignore
            im = Image.open(BytesIO(requests.get(f'{x["datapoint_uri"]}').content))
            
            red_check: t.Callable[[int, int, int], bool] = lambda r, g, b: r > 130 and g < 70 and b < 120
            green_check: t.Callable[[int, int, int], bool] = lambda r, g, b: r < 130 and g > 100 and b < 100
            
            pixels = sum([list(im.getdata())[i * im.size[0]:(i + 1) * im.size[0]] for i in range(im.size[1])], [])
            
            green = (len([x for x in pixels if green_check(*x)]) / len(pixels)) * 100
            red = (len([x for x in pixels if red_check(*x)]) / len(pixels)) * 100
            
            # if red > 45 and green > 10 and green < 25:
            #     green += random.randint(0, 10)
            
            # if red > 17 and red < 25:
            #     red += random.randint(0, 12)

            predict = red > 1.5
            print(y+1, "image",  x["datapoint_uri"], predict, red)
            answers[x["task_key"]] = str(predict).lower()
        
        return answers
    
    def test_case(self, path: str) -> t.Any:
        images = [x for x in pathlib.Path(__file__).parent.joinpath(*path.split("/")).rglob("*.png")]
        for x in images:
            im = Image.open(x)
            pixels = sum([list(im.getdata())[i * im.size[0]:(i + 1) * im.size[0]] for i in range(im.size[1])], [])
            
            red_check: t.Callable[[int, int, int], bool] = lambda r, g, b: r > 130 and g < 70 and b < 120
            red = (len([x for x in pixels if red_check(*x)]) / len(pixels)) * 100

            green_check: t.Callable[[int, int, int], bool] = lambda r, g, b: r < 130 and g > 100 and b < 100
            green = (len([x for x in pixels if green_check(*x)]) / len(pixels)) * 100

            predict = green > 3 and red > 1.5
            print(predict, green, red, x.name)

# a = KindaComputerVision()
# a.test_case("data/apple/tree/1670955978")
