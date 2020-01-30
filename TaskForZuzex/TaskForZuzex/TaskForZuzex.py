import cv2 as cv
import numpy as np
import math
import os


def get_image(path):
    if not os.path.exists(path):
        print_error('File does not exists.')
    if not cv.haveImageReader(path):
        print_error('File has no image or is corrupted.')
    else: 
        return cv.imread(path)

def create_rotated_rect(image):
    height = np.size(image,0) 
    width = np.size(image,1) 
    area = width * height
    _delta = 10
    _min_area = int(area * 0.0002)
    _max_area = int(area * 0.03)
    mser = cv.MSER_create(_delta,_min_area,_max_area)
    image_gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    #ДОБАВИТЬ УЛУЧШЕНИЕ + КОНТРАСТНОСТЬ
    regions, _ = mser.detectRegions(image_gray)
    hulls = [cv.convexHull(p.reshape(-1, 1, 2)) for p in regions]

    if len(hulls)<10:
        print_error("Image have not consist any barcode.")

    rotated_rect = []
    for i, contour in enumerate(hulls):
        rect = cv.minAreaRect(contour)

        if rect[1][0] != 0 and rect[1][1] != 0:
            if rect[1][0]/rect[1][1]>5 or rect[1][1]/rect[1][0]>5:
                if rect[1][1]>rect[1][0]:
                    revers_rect = [0,1,2]
                    revers_rect[0] = rect[0]
                    revers_rect[1] = list(rect[1])
                    revers_rect[1][0], revers_rect[1][1] = revers_rect[1][1], revers_rect[1][0]
                    revers_rect[1] = tuple(revers_rect[1])
                    revers_rect[2] += rect[2] + 90
                    rotated_rect.append(tuple(revers_rect))
                else:   
                    rotated_rect.append(rect)
            
    sorted_areas = sorted(rotated_rect, key = lambda left_center_point:rotated_rect[0][0])
    return tuple(sorted_areas)

def print_error(description):
    print(description)
    raise SystemExit

def view_image(image):
    cv.namedWindow('Display', cv.WINDOW_NORMAL)
    cv.resizeWindow('Display',np.size(image,1) ,np.size(image,0))
    cv.imshow('Display', image)
    cv.waitKey(0)
    cv.destroyAllWindows()

def create_split_line(rect):
    split_lines = []
    for i, element in enumerate(rect):
        centr_point = (int(element[0][0]),int(element[0][1]))
        width = element[1][0] 
        height = element[1][1]
        a = math.radians(abs(element[2]))
        l = 0.3 * height
        dx = math.cos(a)*l
        dy = math.sin(a)*l

               
        point_split_1 = (int(centr_point[0] + dx), int(centr_point[1] - dy))
        point_split_2 = (int(centr_point[0] - dx), int(centr_point[1] + dy))
            
        cv.line(image, point_split_1, point_split_2, (0,255,0))

        a = element[2]; 
        add = (point_split_1,point_split_2,a)  
        split_lines.append(add)
    return tuple(split_lines)     


path = 'C:/Photo/5.png'


image = get_image(path)
rotated_rect = create_rotated_rect(image)
split_lines = create_split_line(rotated_rect)



box = []
for i, contour in enumerate(rotated_rect):
    print(rotated_rect[i])
    box.append(cv.boxPoints(rotated_rect[i]))
    box[i] = np.int0(box[i])

for i, contour in enumerate(box):    
    cv.drawContours(image,[contour],0,(0,0,255),1)


view_image(image)
