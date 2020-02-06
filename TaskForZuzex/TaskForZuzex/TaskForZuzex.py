import numpy as np
import os
import sys

import cv2 as cv

from ClassSearcherBarcode import SearcherBarcode




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


def draw_contour(image, contours):
    box = []
    for i in range(len(contours)):
        box.append(cv.boxPoints(contours[i]))
    box = np.int0(box)
    for i, contour in enumerate(box):    
        cv.drawContours(image,[contour],0,(0,0,255),2)



def view_image(image):
    if path_save_image is not None:
        name_window = os.path.basename(os.path.splitext(path_save_image)[0])
    else:
        name_window = os.path.basename(os.path.splitext(path_load_image)[0])

    cv.namedWindow(name_window, cv.WINDOW_NORMAL)
    cv.resizeWindow(name_window,np.size(image,1) ,np.size(image,0))
    cv.imshow(name_window, image)
    cv.waitKey(0)
    cv.destroyAllWindows()


def load_command_line_arguments():
    path_save_image = None
    flag_print_runtime = 0

    if len(sys.argv)==1:
        print_error(
            '''\n There are no arguments:
            I < picture file path > required;
            O < picture file path > optional parameter for saving processing results;
            T < 1 > optional parameter, measure execution time for each command block and command as a whole, display the measurement result.
            ''')

    if len(sys.argv)>1:
        path_load_image = sys.argv[1]
        
    if len(sys.argv)>2:
        if (sys.argv[2] == str(0) or sys.argv[2] == str(1)) and len(sys.argv) == 3: 
            flag_print_runtime = int(sys.argv[2])
        else:
            path = os.path.split(sys.argv[2])[0]
            file_name = os.path.split(sys.argv[2])[1]
            if not os.path.exists(path):
                print_error('\nError second argument: Path for save file does not exists.\n')
            elif len(file_name)<1:
                print_error('\nError second argument: Missing file name to save.\n')
            path_save_image = sys.argv[2]

    if len(sys.argv)>3:
        if sys.argv[3] != str(0) and sys.argv[3] != str(1): 
            print_error("\nError third argument: argument is not correct.\n")
        else:
            flag_print_runtime = int(sys.argv[3])

    if len(sys.argv)>4:
        print("\nThree arguments loaded, the rest will be ignored.\n")
    
    return path_load_image, flag_print_runtime, path_save_image
    



path_load_image, flag_print_runtime, path_save_image = load_command_line_arguments()
image = get_image(path_load_image)
barcode = SearcherBarcode(image, flag_print_runtime)
barcode_area = barcode.get_barcode_area()

if barcode_area is None:
    print("\nImage have not consist any barcode\n")
else:
    n = len(barcode_area)
    print("\n{} barcode{} found. \n".format(n, 's' if n>1 else ''))
    draw_contour(image, barcode_area)


if path_save_image is not  None:
    path = os.path.splitext(path_save_image)[0] + os.path.splitext(path_load_image)[1]
    cv.imwrite(path, image)
    
    

view_image(image)



    

