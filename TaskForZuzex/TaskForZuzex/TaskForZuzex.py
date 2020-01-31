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

def filter_rect(rect):
    if rect[1][0] != 0 and rect[1][1] != 0:
        if rect[1][0]/rect[1][1]>5 or rect[1][1]/rect[1][0]>5:
            if rect[1][1]>rect[1][0]:
                revers_rect = [0,1,2]
                revers_rect[0] = rect[0]
                revers_rect[1] = list(rect[1])
                revers_rect[1][0], revers_rect[1][1] = revers_rect[1][1], revers_rect[1][0]
                revers_rect[1] = tuple(revers_rect[1])
                revers_rect[2] = rect[2] + 90
                return tuple(revers_rect)
            else:   
                return rect

def create_rotated_rect(image):
    height = np.size(image,0) 
    width = np.size(image,1) 
    area = width * height
    _delta = 5
    _min_area = int(area * 0.0002)
    _max_area = int(area * 0.03)
    mser = cv.MSER_create(_delta,_min_area,_max_area)
    regions, _ = mser.detectRegions(image_gray)
    hulls = [cv.convexHull(p.reshape(-1, 1, 2)) for p in regions]

    if len(hulls)<10:
        print_error("Image have not consist any barcode.")

    rotated_rect = []
    for i, contour in enumerate(hulls):
        rect = filter_rect(cv.minAreaRect(contour))
        if rect != None: 
            rotated_rect.append(rect)

    return tuple(rotated_rect)

def print_error(description):
    print(description)
    raise SystemExit

def view_image(image):
    cv.namedWindow('Display', cv.WINDOW_NORMAL)
    cv.resizeWindow('Display',np.size(image,1) ,np.size(image,0))
    cv.imshow('Display', image)
    cv.waitKey(0)
    cv.destroyAllWindows()


def improve_image(image_gray):
    kernel = np.array([[-0.6,-0.6,-0.6],[-0.6,5.3,-0.6],[-0.6,-0.6,-0.6]])
    image_gray = cv.filter2D(image_gray,-1,kernel)
    hist,bins = np.histogram(image_gray,256)
    cdf = hist.cumsum()
    cdf = (cdf-cdf[0])*255/(cdf[-1]-1)
    cdf = cdf.astype(np.uint8)
    image_gray = cdf[image_gray]
    return image_gray

def create_cluster(rotated_rect):
    sorted_areas = sorted(rotated_rect, key = lambda tup:tup[2])
    count_cluster = -17
    i = 0
    amount_in_cluster = [0 for clasters in range(36)]

    while count_cluster < 18 and i < len(sorted_areas):
        if count_cluster * 5 - 5 <= sorted_areas[i][2] < count_cluster * 5 :
            amount_in_cluster[count_cluster+17] += 1
            i += 1
        else:
            count_cluster += 1
   
    clusters_area = []
    summ_in_out = -amount_in_cluster[-1]
    for i in range(36):
        if amount_in_cluster[i-1] + amount_in_cluster[i] > 10:
            cluster = []
            for j in range(amount_in_cluster[i-1] + amount_in_cluster[i]):
                cluster.append(sorted_areas[summ_in_out + j])
            clusters_area.append(cluster)
        summ_in_out += amount_in_cluster[i-1]

    if clusters_area == None:
        print_error("Image have not consist any barcode.")

    # ПРОВЕРКА КЛАСТЕРОВ НА СОВПАДЕНИЕ

    return clusters_area
            


path = 'C:/Photo/2.bmp'


image = get_image(path)
image_gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
image_gray = improve_image(image_gray)
rotated_rect = create_rotated_rect(image_gray)
clusters_area = create_cluster(rotated_rect)

print(len(clusters_area[0]))
print(len(clusters_area[1]))



box = []
for i, contour in enumerate(clusters_area[0]):
    box.append(cv.boxPoints(clusters_area[0][i]))
    box[i] = np.int0(box[i])
    print(clusters_area[0][i][2])

for i, contour in enumerate(box):    
    cv.drawContours(image,[contour],0,(255,0,255),1)
view_image(image)

print('------------------------------')

box2 = []
for i, contour in enumerate(clusters_area[1]):
    box2.append(cv.boxPoints(clusters_area[1][i]))
    box2[i] = np.int0(box2[i])
    print(clusters_area[1][i][2])

for i, contour in enumerate(box2):    
    cv.drawContours(image,[contour],0,(0,0,255),1)

view_image(image)
