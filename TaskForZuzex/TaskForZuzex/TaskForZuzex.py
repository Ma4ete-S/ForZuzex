import cv2 as cv
import numpy as np
import math
import os


def get_image(path):
    if not os.path.exists(path):
        print_error('File does not exists.')
    image = cv.imread(path)
    if image==None:
        print_error('File has no image or is corrupted.')
    else: 
        return image

    

def create_rotated_rect(image):
    width = np.size(image,0) 
    height = np.size(image,1)
    area = width * height
    _delta = 3
    _min_area = int(area * 0.0002)
    _max_area = int(area * 0.05)
    mser = cv.MSER_create(_delta,_min_area,_max_area)
    image_gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    image_gray = cv.medianBlur(image_gray,5)
    grayscale_levels(image_gray)
    regions, _ = mser.detectRegions(image_gray)
    hulls = [cv.convexHull(p.reshape(-1, 1, 2)) for p in regions]

    if len(hulls)<5:
        print_error("Image have not consist any barcode.")

    rotated_rect = []
    for i, contour in enumerate(hulls):
        rotated_rect.append(cv.minAreaRect(contour))

    return rotated_rect

def print_error(description):
    print(description)
    raise SystemExit

def view_image(image):
    cv.namedWindow('Display', cv.WINDOW_NORMAL)
    cv.imshow('Display', image)
    cv.waitKey(0)
    cv.destroyAllWindows()

def grayscale_levels(image):
    high = 255
    while(1):
        low = high - 5
        col_to_be_changed_low = np.array([low])
        col_to_be_changed_high = np.array([high]) 
        lvl_mask = cv.inRange(image,col_to_be_changed_low,col_to_be_changed_high)
        image[lvl_mask>0] = (high)
        high -= 5
        if (low <= 0):
            break
    return image

def rect_filter(rotated_rect):
    filtered_rect = []
    for i, element in enumerate(rotated_rect):
        if element[1][0]/element[1][1]>5 or element[1][1]/element[1][0]>5:
            filtered_rect.append(element)
    return filtered_rect

def create_split_line(rect):
    split_lines = []
    for i, element in enumerate(rect):
        centr_point = (int(element[0][0]),int(element[0][1]))
        width = element[1][0] 
        height = element[1][1]
        a = element[2]
        dx = math.sin(a+90)
        dy = math.cos(a+90)
       
        if height>width:
            l = 0.3 * height
            point_bis_1 = (int(element[0][0]+dx*l),int(element[0][1]+dy*l))
            point_bis_2 = (int(element[0][0]-dx*l),int(element[0][1]-dy*l))
            cv.line(image,centr_point,point_bis_1,(0,255,0),1)
            cv.line(image,centr_point,point_bis_2,(0,255,0),1)
        else: 
            l = 0.3 * width
            point_bis_1 = (int(element[0][0]+dx*l),int(element[0][1]-dy*l))
            point_bis_2 = (int(element[0][0]-dx*l),int(element[0][1]+dy*l))
            cv.line(image, centr_point, point_bis_1, (0,255,0))
            cv.line(image, centr_point, point_bis_2, (0,255,0))
        
            


        #bisectors.append(cv.minAreaRect(element))

path = 'C:/Photo/NVIDIA_SLA_cuDNN_Support.txt'
image = get_image(path)


rotated_rect = create_rotated_rect(image)
filtred_rect = rect_filter(rotated_rect)
split_lines = create_split_line(filtred_rect)



box = np.array(len(filtred_rect)) 
box = np.int0(filtred_rect)

for i, contour in enumerate(filtred_rect):
    box.append(cv.boxPoints(filtred_rect[i]))
    box[i] = np.int0(box[i])


for i, contour in enumerate(box):    
    cv.drawContours(image,[contour],0,(0,0,255),1)

print(rotated_rect[0])
view_image(image)
