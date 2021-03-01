import subprocess
import cv2
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.path import Path

cmd = "raspistill -vf -o ./image2.jpg -t -1"
subprocess.call(cmd, shell=True)
print("Success!")

filename = 'image2.jpg'
img = cv2.imread(filename)
height, width, channels = img.shape
img = img[int(0.14 * height):int(0.94 * height), int(0.195 * width):int(0.81 * width)]
height, width, channels = img.shape
new_width = int(width / 3)
new_height = int(height / 3)
img = cv2.resize(img, (new_width, new_height))
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
point_xs = np.linspace(0, new_width - 1, 9).astype(int)
point_ys = np.linspace(0, new_height - 1, 9).astype(int)
for x in point_xs:
    for y in point_ys:
        gray[y, x] = 255
cv2.imshow('img',gray)
cv2.waitKey(0)