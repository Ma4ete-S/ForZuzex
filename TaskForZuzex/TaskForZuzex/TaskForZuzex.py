import numpy as np
import math
import os
import timeit
import sys

import cv2 as cv


class SearchBarcode:
    """
    Класс осуществляет поиск области ограничивающей штрихкод.

    Конструктор принимает:
        Изображение - обязательный параметр
        Значение параметра MSER - опциональный параметр, значение по умолчанию  delta_MSER = 5 
        Флаг печати времени выполнения - опциональный параметр, значение по умолчанию flag_print_runtime = False,
        при установке flag_print_runtime = True выводит на экран отчёт о времени выполнения модулей.

    Открытый метод:
        get_barcode_area() - Метод вычислеей область ограничивающую штрихкод и возвращает полученное значение.
                             Если переданно повреждённое изображение или отсутствует штрихкод, возвразает None.

    """
    _general_runtime = 0
    _start_run = 0

    def __init__(self, image, delta_MSER=5, flag_print_runtime=False):
        self.image = image
        self.delta_MSER = delta_MSER
        self.flag_print_runtime = flag_print_runtime
        self.barcode_area = None
        self._flag_drew_barcode = False
        

    
    def get_barcode_area(self):
        """  
        В случае удачного определения области штрихкода, метод возвращает tuple из 
        параметров ограничивающех областей в формате tuple((centrX,centrY),(length,width),angle)
        """
        if self.barcode_area is None:
            self._calc_barcode_area()
        if self.barcode_area is not None:
            self_flag_drew_barcode = True
        return self.barcode_area

        
    def _calc_barcode_area(self):
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
        #hist,bins = np.histogram(prepared_image,256)
        #cdf = hist.cumsum()
        #cdf = (cdf-cdf[0])*255/(cdf[-1]-1)
        #cdf = cdf.astype(np.uint8)
        #prepared_image = cdf[prepared_image]
        #view_image(prepared_image)




        #kernel = np.array([[-1,-1,-1],[-1,8.8,-1],[-1,-1,-1]])
        #prepared_image = cv.filter2D(prepared_image,-1,kernel)
        #view_image(prepared_image)

        #prepared_image = cv.medianBlur(prepared_image,5)
        #view_image(prepared_image)

        #prepared_image = cv.filter2D(prepared_image,-1,kernel)
        #view_image(prepared_image)

        #prepared_image = cv.medianBlur(prepared_image,5)
        #view_image(prepared_image)

        #prepared_image = cv.filter2D(prepared_image,-1,kernel)
        #view_image(prepared_image)

        return prepared_image



    def _create_rotated_rect(self, prepared_image):
        """ Функция осуществляет поиск контуров используя алгоритм MSER."""

        conturs = self._find_conturs_with_MSER_(prepared_image)
        if len(conturs) > 10:
            rotated_rect = self._get_rotated_rect_from_conturs_(conturs)
            rotated_rect = self._connect_crossed_areas__(rotated_rect)
            #view_image(image, rotated_rect)
        return rotated_rect

    def _find_conturs_with_MSER_(self, image):
        height = np.size(image,0) 
        width = np.size(image,1) 
        area = width * height
        _min_area = int(area * 0.0005)
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
        Метод принимает параметры детектированной области и
        фильтрует их по следующим критериям:
        - удаляются области с нулевым значением ширины или высоты 
        - удаляются с соотношением сторон менее 3.
        
        Если границы области выходят за гриницы изображения, 
        границы области обрезаются по границам изображения.

        В случае если ширина больше высоты, их значения меняются 
        местами и значение угла увеличивается на 90 градусов.
        """
        height = np.size(image,0) 
        width = np.size(image,1) 


        if (rect[1][0] > 0 and rect[1][1] > 0 
          and (rect[1][0]/rect[1][1]>2 or rect[1][1]/rect[1][0]>2)):
            # Добавить: изменять границы элемента если выходит за гриницы
            if rect[1][1]>rect[1][0]:
                prepared_rect = [0,1,2]
                prepared_rect[0] = rect[0]
                prepared_rect[1] = list(rect[1])
                prepared_rect[1][0] ,prepared_rect[1][1] = prepared_rect[1][1], prepared_rect[1][0]
                prepared_rect[1] = tuple(prepared_rect[1])
                prepared_rect[2] = rect[2] + 90
                return tuple(prepared_rect)
            else: 
                return rect
        else:
            return None

    def _connect_crossed_areas__(self, rect_areas):
        """
        Return min area of crossed areas and point stop

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

            # ДОПИСАТЬ
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
        return cv.minAreaRect(points)





    def _create_clusters(self, rotated_rect):
        """  Метод принимает список детектированных областей и формирует из них кластеры. """
        sorted_areas = sorted(rotated_rect, key = lambda tup:tup[2])
        amount_in_ranged_areas = self._get_ranged_area_by_five_degrees_(sorted_areas)
        clustered_by_angle_area = self._filter_ranged_areas_(amount_in_ranged_areas, sorted_areas)
        return clustered_by_angle_area


    def _get_ranged_area_by_five_degrees_(self, sorted_areas):
        """ 
        Метод принимает список детектированных областей отсортированных по углу ориентации,
        разбивает весь диапозон от -90 до +90 градусов на 36, по 5 градусов и 
        вычисляет сколько областей попало в каждый диапозон.
       
        Возвращает список из 36 элементов содержащий количество областей попавших в границы 5 градусов. 
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
        Метод выполняет сборку кластеров по следующему критерию:
        По данным о количестве элементов в границах 5 градусов, проводится проверка - 
        если количество элементов в границах 5 градусов, больше чем в соседних границах и
        количество элементов в этих трёх границах (15 градусов) больше 10, то из них
        формируется кластер.
        """
        clusters_area = []
        summ_in_out = -amount_in_ranged_areas[-2] - amount_in_ranged_areas[-1]
        i=0
        while i<36:
            summ = amount_in_ranged_areas[i-2] + amount_in_ranged_areas[i-1] + amount_in_ranged_areas[i]
            if amount_in_ranged_areas[i-2] < amount_in_ranged_areas[i-1] > amount_in_ranged_areas[i] and summ > 10:
                cluster = []
                for j in range(summ):
                    cluster.append(sorted_areas[summ_in_out + j])
                clusters_area.append(cluster)
            summ_in_out += amount_in_ranged_areas[i-2]
            i+=1
        return clusters_area


    def _select_barcode(self, clusters_area):
        barcode_area = []
        for i, cluster in enumerate(clusters_area):
            base_angle = self._calculate_average_angle_(cluster)
            distance = self._get_distance_between_centr_points_of_areas_(cluster, base_angle)
            cluster_sorted_by_distance = [y for x,y in sorted(zip(distance, cluster))]
            distance = sorted(distance)
            
            # claster_select_by_distance = self._get_claster_select_by_distance_(cluster_sorted_by_distance, distance)
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
        k1 = math.tan(base_angle+math.radians(90))
        k2 = math.tan(base_angle)
        distance = []
        for i in range(len(cluster)):
            dx = (cluster[i][0][1] - k2 * cluster[i][0][0])/(k1-k2)
            dy = k1 * dx
            distance.append(((dx-cluster[i][0][0])**2 + (dy-cluster[i][0][1])**2)**0.5)
        return distance

    #def _get_claster_select_by_distance_(self, sorted_clusters, distance):
    #   cluster = []
    #    list_candidat = [0 for clasters in range(len(sorted_clusters))]

        #for i in range(len(sorted_clusters)):
        #    for j in range(len(sorted_clusters)):
        #        if distance[j] - distance[i] < sorted_clusters[i][1][0]/4 + sorted_clusters[j][1][0]/4:
        #            list_candidat[i] += 1


        #for i in range(len(sorted_clusters)):
        #    p1 = sorted_clusters[i][0][0] + math.sin(math.radians(sorted_clusters[i][2]))*distance[i]
        #    p2 = sorted_clusters[i][0][1] + math.cos(math.radians(sorted_clusters[i][2]))*distance[i]
        #    cv.line(image,(sorted_clusters[i][0][0],sorted_clusters[i][0][1]), (p1, p2), (255,0,0), 1)

#        view_image(image)




        #return claster


    def _get_candidate_in_barcode_(self, sorted_cluster, distance):
        new_cluster = []
        average_distance = self._calculate_max_distance__(sorted_cluster)
        j = 0
        while len(sorted_cluster)!=0:
            list_flag = [0 for clasters in range(len(sorted_clusters))]
            candidate = []

            for i in range(len(sorted_cluster)-1):
                #distance_between_centr_of_areas = abs(distance[i-1] - distance[i])
                dx = sorted_cluster[i+1][0][0] - sorted_cluster[j][0][0]
                dy = sorted_cluster[i+1][0][1] - sorted_cluster[j][0][1]
                vector_distance_between_centr = (dx**2 + dy**2)**0.5
                max_distance = average_distance * 0.3

                if vector_distance_between_centr < max_distance: 
                    list_flag[i] = 1
            

            for count in len(list_flag)-j:
                if list_flag[count+j] == 0:
                    j += 1
                    break
            if count == len(list_flag):
                for
                    
            # Если дошёл до конца, то запустить переписывание


            #view_image(image, candidate)
            #j += 1
        
        return candidates

    def _calculate_max_distance__(self, sorted_cluster):
        distance = 0
        for i in range(len(sorted_cluster)):
            distance += sorted_cluster[i][1][0]
        distance = distance / len(sorted_cluster)
        return distance






def print_error(message):
    print(message)
    sys.exit(0)


def get_image(path):
    if not os.path.exists(path):
        print_error('\nError: File does not exists.\n')
    if not cv.haveImageReader(path):
        print_error('\nError: Has no image or is corrupted.\n')
    else: 
        return cv.imread(path)


def view_image(image, conturs):
    if conturs is not None:
        box = []
        for i, contour in enumerate(conturs):
            box.append(cv.boxPoints(conturs[i]))
            box[i] = np.int0(box[i])

        for i, contour in enumerate(box):    
            cv.drawContours(image,[contour],0,(0,0,255),1)

    cv.namedWindow('Image with detecting barcode', cv.WINDOW_NORMAL)
    cv.resizeWindow('Image with detecting barcode',np.size(image,1) ,np.size(image,0))
    cv.imshow('Image with detecting barcode', image)
    cv.waitKey(0)
    cv.destroyAllWindows()


def load_command_line_arguments():
    path_save_image = None
    flag_print_runtime = 0

    if len(sys.argv)==1:
        print_error("\nError first argument: Missing required argument.\n")

    if len(sys.argv)>1:
        path_load_image = sys.argv[1]
        
    if len(sys.argv)>2:
        path = os.path.split(sys.argv[2])[0]
        file_name = os.path.split(sys.argv[2])[1]
        if not os.path.exists(path):
            print_error('\nError second argument: Path for save file does not exists.\n')
        elif len(file_name)<1:
            print_error('\nError second argument: Missing file name to save.\n')

    if len(sys.argv)>3:
        if sys.argv[3] != str(0) and sys.argv[3] != str(1): 
            print_error("\nError third argument: argument is not correct.\n")
        else:
            flag_print_runtime = int(sys.argv[3])

    if len(sys.argv)>4:
        print("\nThree arguments loaded, the rest will be ignored.\n")
    
    return path_load_image, flag_print_runtime, path_save_image
    



path_load_image = 'C:/Photo/6.png'
flag_print_runtime = 0
path_save_image = None


#path_load_image, flag_print_runtime, path_save_image = load_command_line_arguments()
image = get_image(path_load_image)
barcode = SearchBarcode(image,5,flag_print_runtime)
barcode_area = barcode.get_barcode_area()

if barcode_area is None:
    print("Image have not consist any barcode")
else:
    n = len(barcode_area)
    print("\n{} barcode{} found. \n".format(n, 's' if n>1 else ''))
    if path_save_image is not  None:
        path = os.path.splitext(path_save_image)[0] + os.path.splitext(path_load_image)[1]
        cv.imwrite(path, image)
    

view_image(image, barcode_area)



    

