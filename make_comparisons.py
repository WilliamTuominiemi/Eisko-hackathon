from compare import compute_image_hash
from typing import Dict, Tuple, List
from pathlib import Path
import imagehash


def compare_components(
    suojas: List[str],
    cells_dir: str = 'extracted_cells',
    use_fast_comparison: bool = True,
    max_hash_diff: int = 5,
    verbose: bool = False,
) -> Dict[Tuple[str, str], int]:
    """Compare components to find unique items and count duplicates.

    Args:
        suojas: List of component labels (e.g., Suoja values)
        cells_dir: Directory containing component cell images
        use_fast_comparison: Use perceptual hashing (10-100x faster)
        max_hash_diff: Maximum hash difference for similarity (lower = stricter)
        verbose: Print debug information

    Returns:
        Dictionary mapping (filename, label) to count of occurrences
    """
    found_components: Dict[Tuple[str, str], int] = {}
    component_hashes: Dict[Tuple[str, str], imagehash.ImageHash] = {}
    dir_path = Path(cells_dir)

    sorted_files = sorted(dir_path.iterdir())

    for idx, file_path in enumerate(sorted_files):
        if not file_path.is_file() or file_path.suffix.lower() not in {
            '.png',
            '.jpg',
            '.jpeg',
        }:
            continue

        if idx >= len(suojas):
            if verbose:
                print(
                    f'Warning: More image files than labels (skipping {file_path.name})'
                )
            break

        filename = file_path.name
        label = suojas[idx]

        if verbose:
            print(f'{idx}: {filename} -> {label}')

        # First component is always unique
        if len(found_components) == 0:
            found_components[(filename, label)] = 1
            if use_fast_comparison:
                component_hashes[(filename, label)] = compute_image_hash(file_path)
            continue

        # Check if this component matches any existing unique component
        is_new = True
        for component_key in list(found_components.keys()):
            unique_filename, unique_label = component_key

            # Labels must match
            if label != unique_label:
                continue

            # Check image similarity
            if use_fast_comparison:
                # Fast hash-based comparison
                current_hash = compute_image_hash(file_path)
                existing_hash = component_hashes[component_key]
                images_similar = (current_hash - existing_hash) <= max_hash_diff
            else:
                # Legacy pixel-by-pixel comparison (slow)
                from compare import are_images_different

                images_different = are_images_different(
                    str(file_path), str(dir_path / unique_filename), verbose=False
                )
                images_similar = not images_different

            # If both label AND image match, it's a duplicate
            if images_similar:
                is_new = False
                found_components[component_key] += 1
                break

        # Add as new unique component if no match found
        if is_new:
            found_components[(filename, label)] = 1
            if use_fast_comparison:
                component_hashes[(filename, label)] = compute_image_hash(file_path)

    if verbose:
        print(f'\nFound {len(found_components)} unique components:')
        for (fn, lbl), count in sorted(
            found_components.items(), key=lambda x: x[1], reverse=True
        ):
            print(f'  {lbl}: {count}x')

    return found_components
