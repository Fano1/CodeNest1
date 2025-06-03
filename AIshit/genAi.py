from PIL import Image
from google import genai

key = 'key_needed'
client = genai.Client(api_key=key)

models = ['gemini-2.0-flash-exp','gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-1.0-pro','gemini-1.5-pro']

class ProtocolGenerateContent:
    def __init__(self, cnt, path):
        self.content = cnt
        self.path = path
    
    def InputImage(self):
        try:
            image = Image.open(self.path)
            response = client.models.generate_content(
                # model= models[n],
                model = "gemini-1.5-flash",

                contents=[image, self.content]
            )
            return (response.text)
        except Exception as e:
            pass

content = "Tell me the nurtitional value of the food given in the picture and sugegst me thing that can help me improve it."
path = "Image\\ppr.jpg"
cam = ProtocolGenerateContent(cnt = content, path=path)

res = cam.InputImage()
print(res)