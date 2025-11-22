from compare import are_images_different
from typing import Dict, Tuple, List
from pathlib import Path


def compare_components(component_with_suoja: Dict[str, str]) -> Dict[Tuple[str, str], int]:
    found_components: Dict[Tuple[str, str], int] = {}
    # dir_path = Path(cells_dir)

    # sorted_files = sorted(dir_path.iterdir())

    # for idx, file_path in enumerate(sorted_files):
    #     if not file_path.is_file():
    #         continue

    #     if idx >= len(suojas):
    #         break

    #     filename = file_path.name
    #     suoja = suojas[idx]

    #     # First component is always unique
    #     if len(found_components) == 0:
    #         found_components[(filename, suoja)] = 1
    #         continue

    #     # Check if this component matches any existing unique component
    #     is_new = True
    #     for component_key in list(found_components.keys()):
    #         unique_filename, unique_suoja = component_key

    #         if suoja != unique_suoja:
    #             continue

    #         images_different = are_images_different(
    #             str(file_path), str(dir_path / unique_filename)
    #         )
    #         images_similar = not images_different

    #         # If both suoja and image match, it's a duplicate
    #         if images_similar:
    #             is_new = False
    #             found_components[component_key] += 1
    #             break

    #     # Add as new unique component if no match found
    #     if is_new:
    #         found_components[(filename, suoja)] = 1

    return found_components
