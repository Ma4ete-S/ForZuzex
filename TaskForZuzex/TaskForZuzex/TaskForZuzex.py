import numpy as np
import math
import os

import cv2 as cv



class SearchBarcode:
    """Class will find barcode in the image"""


    def __init__(self, image, delta_MSER=5):
        self.image = image
        self._delta_MSER = delta_MSER
        self.barcode_area = None
        self._flag_drew_barcode = False
        self.get_barcode_area()

    
    def get_barcode_area(self):
        if self.barcode_area is None:
            self._calc_barcode_area()
        if self.barcode_area is not None:
            self_flag_drew_barcode = True
        return self.barcode_area

    def save_image_with_barcode_area(self, path):
        if not self._flag_drew_barcode:
            self._calc_barcode_area(self)
        cv.imwrite(path, self.image)
        
    def _calc_barcode_area(self):
        try:
            prepared_image = self._convert_and_improve_image()
            rotated_rect = self._create_rotated_rect(prepared_image)
            clusters_area = self._create_clusters(rotated_rect)
            self.barcode_area = self._select_barcode(clusters_area)
        except:
            return None



        
    def _convert_and_improve_image(self):
        prepared_image = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)
        kernel = np.array([[-0.6,-0.6,-0.6],[-0.6,5.4,-0.6],[-0.6,-0.6,-0.6]])
        prepared_image = cv.filter2D(prepared_image,-1,kernel)
        hist,bins = np.histogram(prepared_image,256)
        cdf = hist.cumsum()
        cdf = (cdf-cdf[0])*255/(cdf[-1]-1)
        cdf = cdf.astype(np.uint8)
        prepared_image = cdf[prepared_image]
        return prepared_image



    def _create_rotated_rect(self, prepared_image):
        conturs = self._find_conturs_with_MSER_(prepared_image)
        if len(conturs) > 10:
            rotated_rect = self._get_rotated_rect_from_conturs_(conturs)
        return rotated_rect

    def _find_conturs_with_MSER_(self, image):
        height = np.size(image,0) 
        width = np.size(image,1) 
        area = width * height
        _min_area = int(area * 0.0002)
        _max_area = int(area * 0.03)
        mser = cv.MSER_create(self._delta_MSER,_min_area,_max_area)
        regions, _ = mser.detectRegions(image)
        conturs = [cv.convexHull(p.reshape(-1, 1, 2)) for p in regions]
        return conturs

    def _get_rotated_rect_from_conturs_(self, contours):
        rotated_rect = []
        for i, contour in enumerate(contours):
            rect = self._filter_rect__(cv.minAreaRect(contour))
            if rect is not None:
                if len(rotated_rect)==0: 
                    rotated_rect.append(rect)
                elif rotated_rect[-1] != rect : 
                    rotated_rect.append(rect)

        return tuple(rotated_rect)

    def _filter_rect__(self, rect):
        if (rect[1][0] > 0 and rect[1][1] > 0 
          and (rect[1][0]/rect[1][1]>3 or rect[1][1]/rect[1][0]>3)):
            prepared_rect = self._get_prepared_rect___(rect)
            return prepared_rect
        else:
            return None

    def _get_prepared_rect___(self, rect):
        prepared_rect = [0,1,2]
        prepared_rect[0] = round(rect[0][0]) , round(rect[0][1])
        prepared_rect[1] = round(rect[1][0]) , round(rect[1][1])
        prepared_rect[2] = round(rect[2])
        if rect[1][1]>rect[1][0]:
            prepared_rect[1] = list(prepared_rect[1])
            prepared_rect[1][0] ,prepared_rect[1][1] = prepared_rect[1][1], prepared_rect[1][0]
            prepared_rect[1] = tuple(prepared_rect[1])
            prepared_rect[2] = prepared_rect[2] + 90
        return tuple(prepared_rect)



    def _create_clusters(self, rotated_rect):
        """


        """
        sorted_areas = sorted(rotated_rect, key = lambda tup:tup[2])
        amount_in_ranged_areas = self._get_ranged_area_by_five_degrees__(sorted_areas)
        clustered_by_defrees_area = self._filter_ranged_areas_(amount_in_ranged_areas, sorted_areas)

        return clustered_by_defrees_area

    def _filter_ranged_areas_(self, amount_in_ranged_areas, sorted_areas):
        clusters_area = []
        summ_in_out = -amount_in_ranged_areas[-2]
        for i in range(35):
            summ = amount_in_ranged_areas[i-2] + amount_in_ranged_areas[i-1] + amount_in_ranged_areas[i]
            if amount_in_ranged_areas[i-2] < amount_in_ranged_areas[i-1] > amount_in_ranged_areas[i] and summ > 10:
                cluster = []
                for j in range(summ):
                    cluster.append(sorted_areas[summ_in_out + j])
                clusters_area.append(cluster)
            summ_in_out += amount_in_ranged_areas[i-2]
        return clusters_area

    def _get_ranged_area_by_five_degrees__(self, sorted_areas):
        count_cluster = -17             
        amount_in_cluster = [0 for clasters in range(36)]
        i = 0
        while count_cluster < 19 and i < len(sorted_areas):
            if count_cluster * 5 - 5 <= sorted_areas[i][2] < count_cluster * 5:
                amount_in_cluster[count_cluster+17] += 1
                i += 1
            else:
                count_cluster += 1
        return amount_in_cluster



    def _select_barcode(self, clusters_area):
        barcode_area = []
        for i, cluster in enumerate(clusters_area):
            base_angle = self._calculate_average_angle_(cluster)
            distance = self._get_distance_between_centr_points_of_areas_(cluster, base_angle)
            cluster_sorted_by_distance = [y for x,y in sorted(zip(distance, cluster))]
            distance = sorted(distance)
            candidate_in_barcode = self._get_candidate_in_barcode_(cluster_sorted_by_distance, distance)

            if len(candidate_in_barcode) > 5:
                contour = self._find_min_area_rect_from_rect_(candidate_in_barcode)
                barcode_area.append(contour)

            candidate_in_barcode = []

        return barcode_area

    def _calculate_average_angle_(self, cluster): 
        base_angle = 0
        for i in range(len(cluster)):
            base_angle += cluster[i][2]
        base_angle = math.radians(base_angle / len(cluster))
        return base_angle

    def _get_distance_between_centr_points_of_areas_(self, cluster, base_angle):
        ### NEED FIND ERRORS
        k1 = 1/math.tan(base_angle)
        k2 = 1/math.tan(base_angle+math.radians(90))
        distance = []
        for i in range(len(cluster)):
            dx = (cluster[i][0][1] - k2 * cluster[i][0][0])/(k1-k2)
            dy = k1 * dx
            distance.append(((dx-cluster[i][0][0])**2 + (dy-cluster[i][0][1])**2)**0.5)
        return distance

    def _get_candidate_in_barcode_(self, sorted_cluster, distance):
        candidate = []
        i = 0
        while i < len(sorted_cluster)-1:
            distance_between_centr_of_areas = distance[i+1] - distance[i]
            dx = sorted_cluster[i+1][0][0] - sorted_cluster[i][0][0]
            dy = sorted_cluster[i+1][0][1] - sorted_cluster[i][0][1]
            vector_length_between_centr = (dx**2 + dy**2) **0.5
            max_distance = (sorted_cluster[i+1][1][0]/2 + sorted_cluster[i][1][0]/2)  * 0.3
            min_distance = (sorted_cluster[i+1][1][1] + sorted_cluster[i][1][1])/4

            if distance_between_centr_of_areas < max_distance and vector_length_between_centr < max_distance:
                if vector_length_between_centr < min_distance:
                    min_area_rect, i = self._connect_crossed_areas__(sorted_cluster, start = i)
                    candidate.append(min_area_rect)
                elif len(candidate)==0: 
                    candidate.append(sorted_cluster[i])
                else: 
                    candidate.append(sorted_cluster[i+1])
            i += 1
        return candidate

    def _connect_crossed_areas__(self, rect_areas,start):
        """
        Return min area of crossed areas and point stop

        """
        rect = []
        rect.append(rect_areas[start])
        distance_between_centr = 0
        min_distance = 1
        stop = start
        while distance_between_centr < min_distance and start < len(rect_areas)-2:
            start += 1
            stop = start
            dx = rect_areas[start+1][0][0] - rect_areas[start][0][0]
            dy = rect_areas[start+1][0][1] - rect_areas[start][0][1]
            distance_between_centr = (dx**2 + dy**2) **0.5
            min_distance = (rect_areas[start+1][1][1] + rect_areas[start][1][1])/4
            rect.append(rect_areas[stop])
        new_min_area_rect = self._find_min_area_rect_from_rect_(rect)

        return new_min_area_rect, stop


    def _find_min_area_rect_from_rect_(self, rect):
        points = []
        for i,element in enumerate(rect):

            dx = element[1][0] / 2
            dy = element[1][1] / 2
            lenght = (dx**2 + dy**2)**0.5

            base_x = element[0][0]
            base_y = element[0][1]
            base_angle = math.radians(element[2])
            d_angle = math.tan(dy/dx)

            d_shift1 = round(math.cos(base_angle + d_angle)*lenght)
            d_shift2 = round(math.sin(base_angle + d_angle)*lenght)
            d_shift3 = round(math.cos(base_angle - d_angle)*lenght)
            d_shift4 = round(math.sin(base_angle - d_angle)*lenght)

            point = base_x + d_shift1, base_y + d_shift2
            points.append(point)
            point = base_x - d_shift1, base_y - d_shift2
            points.append(point)
            point = base_x + d_shift3, base_y + d_shift4
            points.append(point)
            point = base_x - d_shift3, base_y - d_shift4 
            points.append(point)

        points = np.float32(points)
        return cv.minAreaRect(points)






def print_error(description):
    print(description)
    raise SystemExit



def get_image(path):
    if not os.path.exists(path):
        print_error('File does not exists.')
    if not cv.haveImageReader(path):
        print_error('File has no image or is corrupted.')
    else: 
        return cv.imread(path)


def view_image(image):
    cv.namedWindow('Display', cv.WINDOW_NORMAL)
    cv.resizeWindow('Display',np.size(image,1) ,np.size(image,0))
    cv.imshow('Display', image)
    cv.waitKey(0)
    cv.destroyAllWindows()





            

path = 'C:/Photo/1.png'

image = get_image(path)

barcode = SearchBarcode(image,10)

barcode_area = barcode.barcode_area

box = []
for i, contour in enumerate(barcode_area):
    box.append(cv.boxPoints(barcode_area[i]))
    box[i] = np.int0(box[i])

for i, contour in enumerate(box):    
    cv.drawContours(image,[contour],0,(0,0,255),1)


view_image(image)




