def _get_candidate_in_barcode_(self, sorted_cluster, distance):
        candidates = []
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
            #else:
             #   if len(candidate)<5: 
             #       candidate =[]
             #   else:
             #       candidates.append([candidate])



            view_image(image, candidate)
            i += 1
        
        return candidates
