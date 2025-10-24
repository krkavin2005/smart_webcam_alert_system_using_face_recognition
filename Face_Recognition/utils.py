import cv2,numpy as np, os

BASE_DIR=os.path.dirname(os.path.abspath(__file__))

def enhance_low_light(img):
    lab=cv2.cvtColor(img,cv2.COLOR_BGR2LAB)
    l, a, b=cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l=clahe.apply(l)
    lab=cv2.merge((l,a,b))
    out = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    out = cv2.fastNlMeansDenoisingColored(out, None, 10,10,7,21)
    return out

def snapshots_dir():
    path=os.path.abspath(os.path.join(BASE_DIR,"..","alerts","snapshots"))
    os.makedirs(path,exist_ok=True)
    return path