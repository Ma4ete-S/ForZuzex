import numpy as np
import math
import os
import timeit
import sys

import cv2 as cv

class SearcherBarcode:
    """
    The class searches the area of the bounding barcode.

    The designer accepts:
    Image - Required
    MSER parameter value - optional parameter, default value delta_MSER = 5
    Run-time print flag - optional parameter, default flag_print_runtime = False,
    When set to flag_print_runtime = True, the system displays a report on the runtime of the modules.

    Open method:
    get_barcode_area () - The method returns the oriented rectangle of the bounding barcode.

    If a damaged image is transmitted or there is no barcode, returns None.

    """

    _aspect_ratio_for_filtering = 3
    _delta_max_distance_to_unite = 0.5
    _mount_areas_for_became_barcode = 8
    _general_runtime = 0
    _start_run = 0

    def __init__(self, image, flag_print_runtime=False, delta_MSER=5):
        self.image = image
        self.delta_MSER = delta_MSER
        self.flag_print_runtime = flag_print_runtime
        self.barcode_area = None

    
    def get_barcode_area(self):
        """  

        If the barcode region is successfully defined, the method returns a list
        Oriented rectangle bounding found barcodes
        in the tuple format ((centrX, centrY), (length, width), angle)

        """

        if self.barcode_area is None:
            self._calc_barcode_area()
        return self.barcode_area

        
    def _calc_barcode_area(self):
        """ Automatically finds the area of the bounding barcode. """
        try:
            if self.flag_print_runtime: 
                self._start_run = timeit.default_timer()
                
            prepared_image = self._convert_and_improve_image()
            if self.flag_print_runtime: 
                print("\nPreprocessing runtime: {} c".format(self._get_runtime()))
            
            rotated_rect = self._create_rotated_rect(prepared_image)
            if self.flag_print_runtime: 
                print("Block detection runtime: {} c".format(self._get_runtime()))

            clusters_area = self._create_clusters(rotated_rect)
            if self.flag_print_runtime: 
                print("Clustering runtime: {} c".format(self._get_runtime()))

            self.barcode_area = self._select_barcode(clusters_area)
            if self.flag_print_runtime: 
                print("Selecting area barcode runtime: {} c".format(self._get_runtime()))
                print("Total runtime: {} c".format(round(self._general_runtime, 2)))

        except:
            return None

    def _get_runtime(self):
        modul_runtime = timeit.default_timer() - self._start_run - self._general_runtime
        self._general_runtime += modul_runtime
        return round(modul_runtime, 2)

        
    def _convert_and_improve_image(self):
        prepared_image = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)
        kernel = np.array([[-0.5,-0.5,-0.5],[-0.5,4.8,-0.5],[-0.5,-0.5,-0.5]])
        prepared_image = cv.filter2D(prepared_image,-1,kernel)

        #hist,bins = np.histogram(prepared_image,256)
        #cdf = hist.cumsum()
        #cdf = (cdf-cdf[0])*255/(cdf[-1]-1)
        #cdf = cdf.astype(np.uint8)
        #prepared_image = cdf[prepared_image]
        
        #prepared_image = cv.medianBlur(prepared_image,5)
        return prepared_image


    def _create_rotated_rect(self, prepared_image):
        """ 

        The function receives the image and returns a list of detected areas.
        As bounding boxes of minimum area using the MSER algorithm.

        """

        conturs = self._find_conturs_with_MSER_(prepared_image)
        if len(conturs) > 10:
            rotated_rect = self._get_rotated_rect_from_conturs_(conturs)
            rotated_rect = self._connect_crossed_areas__(rotated_rect)
        return rotated_rect

    def _find_conturs_with_MSER_(self, image):
        height = np.size(image,0) 
        width = np.size(image,1) 
        area = width * height
        _min_area = 50
        _max_area = int(area * 0.02)
        mser = cv.MSER_create(self.delta_MSER,_min_area,_max_area)
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
        """ 
        The function takes the oriented rectangle and returns the oriented rectangle
        A rectangle if it meets the following selection criteria:
        -The width or height value is greater than zero
        - Aspect ratio is more than self._aspect_ratio_for_filtering.

        If the region boundaries extend beyond the image grates,
        Area boundaries are trimmed to image boundaries.

        If the width is greater than the height, their values change
        Places and the angle increases by 90 degrees.

        """

        if (rect[1][0] > 0 and rect[1][1] > 0 
          and (rect[1][0]/rect[1][1]>self._aspect_ratio_for_filtering 
               or rect[1][1]/rect[1][0]>self._aspect_ratio_for_filtering)):
            if rect[1][1]>rect[1][0]:
                rect = self._swap_width_and_height__(rect)
            return rect
        else:
            return None

    def _swap_width_and_height__(self, rect):
        prepared_rect = [0,1,2]
        prepared_rect[0] = rect[0]
        prepared_rect[1] = list(rect[1])
        prepared_rect[1][0] ,prepared_rect[1][1] = prepared_rect[1][1], prepared_rect[1][0]
        prepared_rect[1] = tuple(prepared_rect[1])
        prepared_rect[2] = rect[2] + 90
        return tuple(prepared_rect)
    

    def _connect_crossed_areas__(self, rect_areas):
        """
        The function takes a list of oriented rectangle parameters and
        Combines intersecting regions.

        """
        rect = [rect_areas[0]]
        new_rect_areas = []

        i = 0
        flag_push_to_connect = False
        while i < len(rect_areas)-1:
            dx = rect_areas[i+1][0][0] - rect_areas[i][0][0]
            dy = rect_areas[i+1][0][1] - rect_areas[i][0][1]
            distance_between_centr = (dx**2 + dy**2) **0.5
            min_distance = (rect_areas[i+1][1][1] + rect_areas[i][1][1])/4

            if distance_between_centr < min_distance : 
                rect.append(rect_areas[i+1])
                flag_push_to_connect = True
            elif flag_push_to_connect:
                new_rect_areas.append(self._find_min_area_rect_from_rect_(rect))
                rect = []
                new_rect_areas.append(rect_areas[i+1])
                flag_push_to_connect = False
            i+=1
        return new_rect_areas


    def _find_min_area_rect_from_rect_(self, rect):
        """

        The method returns the parameters of the minimum area rectangle 
        of the bounding the list of the transferred areas.

        """

        points = []
        for i,element in enumerate(rect):

            height = np.size(self.image,0) 
            width = np.size(self.image,1) 

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

            points.append((base_x + d_shift1, base_y + d_shift2))
            points.append((base_x - d_shift1, base_y - d_shift2))
            points.append((base_x + d_shift3, base_y + d_shift4))
            points.append((base_x - d_shift3, base_y - d_shift4))

            for i in range(4):
                if points[i-4][0] > width:
                    points[i-4] = (width, points[i-4][1])
                if points[i-4][1] > height:
                    points[i-4] = (points[i-4][0], height)
                if points[i-4][1] < 0:
                    points[i-4] = (points[i-4][0], 0)                
                if points[i-4][1] < 0:
                    points[i-4] = (points[i-4][0], 0)

        points = np.float32(points)
        rect = cv.minAreaRect(points)

        if rect[1][1]>rect[1][0]:
            rect = self._swap_width_and_height__(rect)

        return rect



    def _create_clusters(self, rotated_rect):
        """  The function receives a list of oriented boxes and forms clusters from them. """
        sorted_areas = sorted(rotated_rect, key = lambda tup:tup[2])
        amount_in_ranged_areas = self._get_ranged_area_by_five_degrees_(sorted_areas)
        clustered_by_angle_area = self._filter_ranged_areas_(amount_in_ranged_areas, sorted_areas)
        return clustered_by_angle_area

    def _get_ranged_area_by_five_degrees_(self, sorted_areas):
        """ 

        The function takes a list of oriented boxes sorted by orientation angle,
        Splits all diaposone from -90 to 90 degrees by 36, by 5 degrees and
        Calculates how many regions have entered each diaposone.

        Returns a list of 36 items containing the number of boxes in the boundary
        each area.

        """

        count_cluster = -17             
        amount_in_cluster = [0 for clasters in range(36)]
        i = 0
        while count_cluster < 19 and i < len(sorted_areas):
            if count_cluster * 5 - 5 <= sorted_areas[i][2] <= count_cluster * 5:
                amount_in_cluster[count_cluster+17] += 1
                i += 1
            else:
                count_cluster += 1
        return amount_in_cluster

    def _filter_ranged_areas_(self, amount_in_ranged_areas, sorted_areas):
        """ 

        The function builds oriented boxes into clusters according to the following criteria:
        According to the data on the number of boxes within the boundaries of 5 degrees, the check is carried out -
        If the number of boxes within the boundaries of 5 degrees is greater than within the adjacent boundaries, and
        The number of elements within these three boundaries (15 degrees) is greater than self._mount_areas_for_became_barcode () = 8,
        Then a cluster is formed from them.

        """

        clusters_area = []
        summ_in_out = -amount_in_ranged_areas[-2] - amount_in_ranged_areas[-1]
        i=0
        while i<36:
            summ = amount_in_ranged_areas[i-2] + amount_in_ranged_areas[i-1] + amount_in_ranged_areas[i]
            if amount_in_ranged_areas[i-2] < amount_in_ranged_areas[i-1] > amount_in_ranged_areas[i] and summ > self._mount_areas_for_became_barcode:
                cluster = []
                for j in range(summ):
                    cluster.append(sorted_areas[summ_in_out + j])
                clusters_area.append(cluster)
            summ_in_out += amount_in_ranged_areas[i-2]
            i+=1
        return clusters_area


    def _select_barcode(self, clusters_area):
        """ 

        The function filters items within raw clusters and returns
        A list of oriented rectangle bounding areas of the barcode.       

        """

        barcode_area = []
        for i, cluster in enumerate(clusters_area):
            candidate_in_barcode = self._get_candidate_in_barcode_(cluster)
            
            for i, cluster in enumerate(candidate_in_barcode):
                if len(cluster) > self._mount_areas_for_became_barcode:
                    cluster_contour = self._find_min_area_rect_from_rect_(cluster)
                    barcode_area.append(cluster_contour)
                candidate_in_barcode = []

        if len(barcode_area) == 0: 
            return None

        return barcode_area


    def _get_candidate_in_barcode_(self, sorted_cluster):
        """" 

        The function takes a list of primogons collected into a raw cluster.

        The distance between the center points of all the elements is checked.
        If the distance between elements is less than the threshold level (mean
        Arithmetic value from the heights of all the boxes in the cluster),
        Then the elements are checked out to the processed cluster if the number of primogons
        In a processed cluster greater than self._mount_areas_for_became_barcode = 8, then
        The cluster is considered to be the area bounding the barcode.

        Returns the lists of oriented boxes bounding the barcode.

        """

        new_cluster = []
        average_distance = self._calculate_average_distance__(sorted_cluster)
        j = 0
        revers_number = 0
        control_to_check = [0 for i in range(len(sorted_cluster))]
        list_flag = [0 for i in range(len(sorted_cluster))]
        flag_to_revers = False
        candidate = []
        while len(sorted_cluster)!=0:
            for i in range(len(sorted_cluster)):
                dx = sorted_cluster[i][0][0] - sorted_cluster[j][0][0]
                dy = sorted_cluster[i][0][1] - sorted_cluster[j][0][1]
                vector_distance_between_centr = (dx**2 + dy**2)**0.5
                max_distance = average_distance * self._delta_max_distance_to_unite

                if vector_distance_between_centr < max_distance and list_flag[i] == 0: 
                    list_flag[i] = 1
                    if i < j and not flag_to_revers: 
                        flag_to_revers = True
                        revers_number = i

            if flag_to_revers:
                j = revers_number
                flag_to_revers = False
                continue            

            for i in range(len(sorted_cluster)):
                if list_flag[i] == 1 and control_to_check[i] == 0:
                    control_to_check[i] = 1
                    j = i
                    break
            else:
                if sum(list_flag) < self._mount_areas_for_became_barcode:
                    for i in reversed(range(len(sorted_cluster))):
                        if list_flag[i] == 1:
                            sorted_cluster.pop(i)
                            list_flag.pop(i)
                            control_to_check.pop(i)
                else:
                    for i in reversed(range(len(sorted_cluster))):
                        if list_flag[i] == 1:
                            candidate.append(sorted_cluster.pop(i))
                            list_flag.pop(i)
                            control_to_check.pop(i)
                    new_cluster.append(candidate)
                    candidate = []
                j=0
                stop_to_connect=0
        
        return new_cluster

    def _calculate_average_distance__(self, sorted_cluster):
        distance = 0
        for i in range(len(sorted_cluster)):
            distance += sorted_cluster[i][1][0]
        distance = distance / len(sorted_cluster)
        return distance