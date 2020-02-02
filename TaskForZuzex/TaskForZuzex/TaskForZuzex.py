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
        if rect[1][0]/rect[1][1]>3 or rect[1][1]/rect[1][0]>3:
            round_rect = [0,1,2]
            round_rect[0] = round(rect[0][0]) , round(rect[0][1])
            round_rect[1] = round(rect[1][0]) , round(rect[1][1])
            round_rect[2] = round(rect[2])

            if rect[1][1]>rect[1][0]:
                round_rect[1] = list(round_rect[1])
                round_rect[1][0] ,round_rect[1][1] = round_rect[1][1], round_rect[1][0]
                round_rect[1] = tuple(round_rect[1])
                round_rect[2] = round_rect[2] + 90


            return tuple(round_rect)
    return None

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

        if rect != None and (len(rotated_rect) == 0 or rotated_rect[-1] != rect) : 
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
    kernel = np.array([[-0.6,-0.6,-0.6],[-0.6,5.4,-0.6],[-0.6,-0.6,-0.6]])
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

    while count_cluster < 19 and i < len(sorted_areas):
        if count_cluster * 5 - 5 <= sorted_areas[i][2] < count_cluster * 5 :
            amount_in_cluster[count_cluster+17] += 1
            i += 1
        else:
            count_cluster += 1
   
    clusters_area = []
    summ_in_out = -amount_in_cluster[-1]
    for i in range(35):
        summ = amount_in_cluster[i-1] + amount_in_cluster[i] + amount_in_cluster[i+1]
        if amount_in_cluster[i-1] < amount_in_cluster[i] > amount_in_cluster[i+1] and summ > 10:
            cluster = []
            for j in range(summ):
                cluster.append(sorted_areas[summ_in_out + j])
            clusters_area.append(cluster)
        summ_in_out += amount_in_cluster[i-1]
    
    summ = amount_in_cluster[-2] + amount_in_cluster[-1] + amount_in_cluster[0]
    
    if amount_in_cluster[-2] < amount_in_cluster[-1] > amount_in_cluster[0] and summ > 10:
        cluster = []
        for j in range(summ):
            cluster.append(sorted_areas[summ_in_out + j])
        clusters_area.append(cluster)

    

    if clusters_area == None:
        print_error("Image have not consist any barcode.")



    return clusters_area
            
def select_barcode(clusters_area):
    barcode_area = []
    for i, cluster in enumerate(clusters_area):
        base_x = 0
        base_y = 0
        base_angle = 0 
        for j in range(len(cluster)):
            base_angle += cluster[j][2]
        base_angle = math.radians(base_angle / len(cluster))
        k1 = 1/math.tan(base_angle)
        k2 = 1/math.tan(base_angle+math.radians(90))
        distance = []

        for j in range(len(cluster)):
            dx = (cluster[j][0][1] - k2 *cluster[i][0][0])/(k1-k2)
            dy = k1 * dx
            distance.append(((dx-cluster[j][0][0])**2 + (dy-cluster[j][0][1])**2)**0.5)

        cluster_sorted_by_distance = [y for x,y in sorted(zip(distance, cluster))]
        distance = sorted(distance)

        candidate_in_barcode = []
        for j in range(len(cluster_sorted_by_distance)-1):
            distance_between_element_in_plane = distance[j+1] - distance[j]
            dx = cluster_sorted_by_distance[j+1][0][0] - cluster_sorted_by_distance[j][0][0]
            dy = cluster_sorted_by_distance[j+1][0][1] - cluster_sorted_by_distance[j][0][1]
            distance_between_centr = (dx**2 + dy**2) **0.5
            max_distance = cluster_sorted_by_distance[j][1][0] * 0.5
            min_distance = (cluster_sorted_by_distance[j+1][1][1] + cluster_sorted_by_distance[j][1][1])/4

            if distance_between_element_in_plane < max_distance and distance_between_centr < max_distance:
                if distance_between_centr < min_distance:
                    min_area_rect, j = connect_crossed_areas(cluster_sorted_by_distance, start = j)
                    candidate_in_barcode.append(min_area_rect)
                elif candidate_in_barcode==None: 
                    candidate_in_barcode.append(cluster_sorted_by_distance[j])
                else: 
                    candidate_in_barcode.append(cluster_sorted_by_distance[j+1])
 
        if len(candidate_in_barcode) > 5:
            for j in range(len(candidate_in_barcode)):
                contour = find_minAreaRect_from_rect(candidate_in_barcode)

                box = []
                box.append(cv.boxPoints(contour))
                box = np.int0(box)
                cv.drawContours(image,[box],0,(255,0,0),1)
            barcode_area.append(contour)




        point_split_1 = (base_x,base_y)

    
    return barcode_area

def connect_crossed_areas(rect_areas,start):
    rect = []
    rect.append(rect_areas[start])
    distance_between_centr = 0
    min_distance = 1
    while distance_between_centr < min_distance and start < len(rect_areas)-1:
        start += 1
        stop = start
        dx = rect_areas[start+1][0][0] - rect_areas[start][0][0]
        dy = rect_areas[start+1][0][1] - rect_areas[start][0][1]
        distance_between_centr = (dx**2 + dy**2) **0.5
        min_distance = (rect_areas[start+1][1][1] + rect_areas[start][1][1])/4
        rect.append(rect_areas[stop])
    new_area_rect = find_minAreaRect_from_rect(rect)

    return new_area_rect, stop


def find_minAreaRect_from_rect(rect):
    points = []
    for i,element in enumerate(rect):
        base_x = element[0][0]
        base_y = element[0][1]
        base_angle = math.radians(element[2])
        lenght = ((base_x - element[1][0])**2 + (base_y - element[1][1])**2) **0.5
        d_shift1 = round(math.sin(math.radians(base_angle))*lenght)
        d_shift2 = round(math.cos(math.radians(base_angle))*lenght)

        point = base_x + d_shift1, base_y + d_shift2
        points.append(point)
        point = base_x - d_shift1, base_y - d_shift2
        points.append(point)
        point = base_x + d_shift1, base_y - d_shift2
        points.append(point)
        point = base_x - d_shift1, base_y + d_shift2 
        points.append(point)

    return cv.minAreaRect(np.float32(points))






path = 'C:/Photo/9.png'


image = get_image(path)
image_gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
image_gray = improve_image(image_gray)
rotated_rect = create_rotated_rect(image_gray)
clusters_area = create_cluster(rotated_rect)
select_barcode(clusters_area)

view_image(image)

#print(len(clusters_area))

#for i in range(len(clusters_area)):
 #   print(i,"__",len(clusters_area[i]))





#box = []
#for i, contour in enumerate(clusters_area[0]):
#    box.append(cv.boxPoints(clusters_area[0][i]))
#    box[i] = np.int0(box[i])

#for i, contour in enumerate(box):    
#    cv.drawContours(image,[contour],0,(0,0,255),1)


#box2 = []
#for i, contour in enumerate(clusters_area[1]):
#    box2.append(cv.boxPoints(clusters_area[1][i]))
#    box2[i] = np.int0(box2[i])

#for i, contour in enumerate(box2):    
#    cv.drawContours(image,[contour],0,(255,0,0),1)





