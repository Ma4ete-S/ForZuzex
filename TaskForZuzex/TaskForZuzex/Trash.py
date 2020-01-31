
    #image_gray = cv.medianBlur(image_gray,5)
    #ДОБАВИТЬ УЛУЧШЕНИЕ + КОНТРАСТНОСТЬ
    # grayscale_levels(image_gray)


 #   def grayscale_levels(image):
 #   high = 255
 #   while(1):
  #      low = high - 10
  #      col_to_be_changed_low = np.array([low])
   #     col_to_be_changed_high = np.array([high]) 
   #     lvl_mask = cv.inRange(image,col_to_be_changed_low,col_to_be_changed_high)
   #     image[lvl_mask>0] = (high)
   #     high -= 10
   #     if (low <= 0):
   #         break
   # return image


#def rect_filter(rotated_rect):
#   filtered_rect = []
#    for i, element in enumerate(rotated_rect):
#        if element[1][0]/element[1][1]>5 or element[1][1]/element[1][0]>5:
#            filtered_rect.append(element)
#    return tuple(filtered_rect)



        
        #else: 
        #    l = 0.3 * width
        #    point_split_1 = (int(centr_point[0] + math.sin(a)*l), int(centr_point[1] + math.cos(a)*l))
        #    point_split_2 = (int(centr_point[0] - math.sin(a)*l), int(centr_point[1] - math.cos(a)*l))
        #    a = abs(element[2])
            
        #    cv.line(image, point_split_1, point_split_2, (0,255,0))


        #def union_of_intersecting_areas(area,center_line):
   # for i, line in enumerate(center_line):    
     #   if center_line[i][2]>=line[2]-2 and center_line[i][2]<=line[2]+2:
     #       if area[i][0][0]+


    #for i, element in enumerate(sorted_areas):
    #    if element[0][1]<sorted_areas[i][0][1]-sorted_areas[i][1][1]

#filtred_rect = rect_filter(rotated_rect)
split_lines = create_split_line(rotated_rect)

def create_split_line(rect):
    split_lines = []
    for i, element in enumerate(rect):
        centr_point = (int(element[0][0]),int(element[0][1]))
        height = element[1][0]
        a = math.radians(element[2]+90) 
        l = 0.3 * height
        dx = math.cos(a)*l
        dy = math.sin(a)*l

        point_split_1 = (int(centr_point[0] + dx), int(centr_point[1] + dy))
        point_split_2 = (int(centr_point[0] - dx), int(centr_point[1] - dy))
        #CREATE LIST !!!    
        cv.line(image, point_split_1, point_split_2, (0,255,0))

         
        add = [point_split_1,point_split_2,a]  
        split_lines.append(add)
    return tuple(split_lines)     
