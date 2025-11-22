from compare import are_images_different
from typing import Dict, Tuple
from pathlib import Path

def compare_components(suojas: list[str]):
    found_components: Dict[Tuple[str, str], int] = {}
    dir_path = Path("extracted_cells")
    
    for idx, file_path in enumerate(sorted(dir_path.iterdir())):
        if not file_path.is_file():
            continue
        filename = file_path.name
        label = suojas[idx]
        print(idx, filename, suojas[idx]) 

        if len(found_components) == 0:
            found_components[(filename, label)] = 1
        else:
            isnew = True
            for component in found_components.keys():
                unique_filename = component[0]
                unique_label = component[1] 
                
                image_not_unique = are_images_different(str(dir_path / filename), str(dir_path / unique_filename))

                label_not_unique = label == unique_label

                if image_not_unique and label_not_unique:
                    isnew = False
                    found_components[component] += 1
                    break

            if isnew:
                found_components[(filename, label)] = 1                
            
    print(found_components)
    return found_components

#test_suoja = ['C25', 'C16', 'C16', 'C16', 'C16', 'C16', 'C16', 'C16', 'C16', 'C16']
#compare_components(test_suoja)