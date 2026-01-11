from PIL import Image
import os

png_path = "ui/resources/icon.png"
ico_path = "ui/resources/icon.ico"

if os.path.exists(png_path):
    img = Image.open(png_path)
    img.save(ico_path, format='ICO', sizes=[(256, 256)])
    print(f"converted {png_path} to {ico_path}")
else:
    print("PNG not found")
