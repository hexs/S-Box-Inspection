import hexss
from hexss.box import Box

hexss.check_packages('qrcode', auto_install=True)

from hexss.image import Image
import qrcode

data = [
    "QD1-1985",
    "QD1-1998",
    "QD1-2001",
    "QD1-2073",
    "QC5-9973",
    "QC7-7957",
    "QC4-9336",
    "FE3-8546",
    "QC8-0997",

]
for d in data:
    im = Image(qrcode.make(d).get_image())
    im = im.crop(xyxy=(30, 30, im.size[0] - 30, im.size[1] - 30))
    # im.show()
    im.save(f"qrcode {d}.png")
