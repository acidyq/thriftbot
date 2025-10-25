"""
ThriftBot Image Processing

Photo processing utilities for eBay listings including background removal,
resizing, and optimization for e-commerce.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageEnhance, ImageOps
import rembg
from dotenv import load_dotenv

from thriftbot.db import get_item_by_sku, InventoryItem

# Load environment variables
load_dotenv()

# Configuration
MAX_PHOTO_SIZE = int(os.getenv("MAX_PHOTO_SIZE", "2048"))
PHOTO_QUALITY = int(os.getenv("PHOTO_QUALITY", "85"))
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}


def process_item_photos(
    sku: str,
    input_dir: str = "photos",
    output_dir: str = "processed",
    remove_background: bool = True,
    enhance: bool = True,
    create_variants: bool = True
) -> Dict[str, Any]:
    """Process all photos for an inventory item."""
    
    item = get_item_by_sku(sku)
    if not item:
        raise ValueError(f"Item with SKU {sku} not found")
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create item-specific directory
    item_output_dir = output_path / sku
    item_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find photos for this item
    photo_files = find_item_photos(sku, input_path)
    
    if not photo_files:
        raise ValueError(f"No photos found for SKU {sku} in {input_path}")
    
    processed_photos = []
    processing_log = []
    
    for i, photo_path in enumerate(photo_files):
        try:
            # Process each photo
            result = process_single_photo(
                photo_path,
                item_output_dir,
                f"{sku}_{i+1:02d}",
                remove_background=remove_background,
                enhance=enhance,
                create_variants=create_variants
            )
            
            processed_photos.extend(result["files"])
            processing_log.append(result["log"])
            
        except Exception as e:
            processing_log.append({
                "file": str(photo_path),
                "status": "error",
                "message": str(e)
            })
    
    # Update database with processed photo paths
    _update_item_photos(item, photo_files, processed_photos)
    
    return {
        "sku": sku,
        "original_count": len(photo_files),
        "processed_count": len(processed_photos),
        "output_directory": str(item_output_dir),
        "processed_files": processed_photos,
        "processing_log": processing_log
    }


def process_single_photo(
    input_path: Path,
    output_dir: Path,
    base_name: str,
    remove_background: bool = True,
    enhance: bool = True,
    create_variants: bool = True
) -> Dict[str, Any]:
    """Process a single photo with various optimizations."""
    
    try:
        # Load image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            processed_files = []
            
            # Original optimized version
            optimized_path = output_dir / f"{base_name}_optimized.jpg"
            optimized_img = _optimize_image(img, enhance=enhance)
            optimized_img.save(optimized_path, "JPEG", quality=PHOTO_QUALITY, optimize=True)
            processed_files.append(str(optimized_path))
            
            # Background removed version
            if remove_background:
                try:
                    bg_removed_path = output_dir / f"{base_name}_no_bg.png"
                    bg_removed_img = remove_image_background(img)
                    bg_removed_img.save(bg_removed_path, "PNG", optimize=True)
                    processed_files.append(str(bg_removed_path))
                except Exception as e:
                    print(f"⚠️  Background removal failed: {e}")
            
            # Create variants if requested
            if create_variants:
                # Square crop for main listing photo
                square_path = output_dir / f"{base_name}_square.jpg"
                square_img = create_square_crop(optimized_img)
                square_img.save(square_path, "JPEG", quality=PHOTO_QUALITY, optimize=True)
                processed_files.append(str(square_path))
                
                # Thumbnail
                thumb_path = output_dir / f"{base_name}_thumb.jpg"
                thumbnail = optimized_img.copy()
                thumbnail.thumbnail((300, 300), Image.Resampling.LANCZOS)
                thumbnail.save(thumb_path, "JPEG", quality=80, optimize=True)
                processed_files.append(str(thumb_path))
            
            return {
                "files": processed_files,
                "log": {
                    "file": str(input_path),
                    "status": "success",
                    "variants_created": len(processed_files),
                    "original_size": f"{img.width}x{img.height}",
                    "message": f"Processed successfully with {len(processed_files)} variants"
                }
            }
            
    except Exception as e:
        raise Exception(f"Failed to process {input_path}: {str(e)}")


def _optimize_image(img: Image.Image, enhance: bool = True) -> Image.Image:
    """Optimize image for eBay listings."""
    
    # Resize if too large
    if img.width > MAX_PHOTO_SIZE or img.height > MAX_PHOTO_SIZE:
        img.thumbnail((MAX_PHOTO_SIZE, MAX_PHOTO_SIZE), Image.Resampling.LANCZOS)
    
    if enhance:
        # Enhance image quality
        # Slight contrast boost
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        # Slight sharpness boost
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        # Slight color saturation boost
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.05)
    
    return img


def remove_image_background(img: Image.Image) -> Image.Image:
    """Remove background from image using rembg."""
    
    # Convert PIL Image to bytes
    import io
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Remove background
    output = rembg.remove(img_byte_arr)
    
    # Convert back to PIL Image
    result_img = Image.open(io.BytesIO(output))
    return result_img


def create_square_crop(img: Image.Image) -> Image.Image:
    """Create a square crop of the image (useful for main listing photo)."""
    
    width, height = img.size
    
    # Determine the size of the square (minimum of width and height)
    size = min(width, height)
    
    # Calculate coordinates for center crop
    left = (width - size) // 2
    top = (height - size) // 2
    right = left + size
    bottom = top + size
    
    # Crop to square
    square_img = img.crop((left, top, right, bottom))
    
    # Resize to standard size if needed
    if size > 1200:
        square_img = square_img.resize((1200, 1200), Image.Resampling.LANCZOS)
    
    return square_img


def find_item_photos(sku: str, search_dir: Path) -> List[Path]:
    """Find photos for a specific item SKU."""
    
    photo_files = []
    
    # Look for files that start with the SKU or contain it
    for file_path in search_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
            # Check if filename contains SKU
            if sku.lower() in file_path.name.lower():
                photo_files.append(file_path)
    
    # Sort by filename to ensure consistent ordering
    photo_files.sort()
    
    return photo_files


def create_photo_grid(photo_paths: List[str], output_path: str, grid_size: Tuple[int, int] = (2, 2)) -> str:
    """Create a grid layout of photos for listings."""
    
    if not photo_paths:
        raise ValueError("No photos provided for grid creation")
    
    cols, rows = grid_size
    max_photos = cols * rows
    
    # Use first max_photos images
    photos_to_use = photo_paths[:max_photos]
    
    # Open and resize images
    images = []
    cell_size = 500  # Size of each cell in the grid
    
    for photo_path in photos_to_use:
        with Image.open(photo_path) as img:
            # Resize to fit cell
            img.thumbnail((cell_size, cell_size), Image.Resampling.LANCZOS)
            
            # Create square with white background
            square_img = Image.new('RGB', (cell_size, cell_size), (255, 255, 255))
            
            # Center the image
            x = (cell_size - img.width) // 2
            y = (cell_size - img.height) // 2
            square_img.paste(img, (x, y))
            
            images.append(square_img)
    
    # Fill remaining cells with white if needed
    while len(images) < max_photos:
        white_cell = Image.new('RGB', (cell_size, cell_size), (255, 255, 255))
        images.append(white_cell)
    
    # Create grid
    grid_width = cols * cell_size
    grid_height = rows * cell_size
    grid_img = Image.new('RGB', (grid_width, grid_height), (255, 255, 255))
    
    # Paste images into grid
    for i, img in enumerate(images):
        row = i // cols
        col = i % cols
        x = col * cell_size
        y = row * cell_size
        grid_img.paste(img, (x, y))
    
    # Save grid
    grid_img.save(output_path, "JPEG", quality=PHOTO_QUALITY, optimize=True)
    
    return output_path


def analyze_image_quality(image_path: str) -> Dict[str, Any]:
    """Analyze image quality and provide recommendations."""
    
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            
            analysis = {
                "file_path": image_path,
                "dimensions": f"{width}x{height}",
                "aspect_ratio": round(width / height, 2),
                "total_pixels": width * height,
                "format": img.format,
                "mode": img.mode,
                "recommendations": []
            }
            
            # Size recommendations
            if width < 500 or height < 500:
                analysis["recommendations"].append("Image is too small for quality eBay listings (min 500px)")
            
            if width > 2048 or height > 2048:
                analysis["recommendations"].append("Image is very large and should be resized to improve loading")
            
            # Aspect ratio recommendations
            if analysis["aspect_ratio"] < 0.8 or analysis["aspect_ratio"] > 1.2:
                analysis["recommendations"].append("Consider cropping to square or closer to 1:1 ratio for main photo")
            
            # Format recommendations
            if img.format not in ['JPEG', 'PNG']:
                analysis["recommendations"].append("Convert to JPEG or PNG for better compatibility")
            
            if not analysis["recommendations"]:
                analysis["recommendations"].append("Image quality looks good for eBay listing")
            
            return analysis
            
    except Exception as e:
        return {
            "file_path": image_path,
            "error": str(e),
            "recommendations": ["Failed to analyze image - check file path and format"]
        }


def _update_item_photos(item: InventoryItem, original_paths: List[Path], processed_paths: List[str]):
    """Update database with photo information."""
    
    # Store as JSON strings in database
    original_paths_json = json.dumps([str(p) for p in original_paths])
    processed_paths_json = json.dumps(processed_paths)
    
    # Update item in database
    from thriftbot.db import engine, Session
    
    with Session(engine) as session:
        # Get fresh item from database
        item_db = session.get(InventoryItem, item.id)
        if item_db:
            item_db.photo_paths = original_paths_json
            item_db.processed_photos = processed_paths_json
            session.commit()


def get_photo_upload_suggestions(category: str) -> Dict[str, List[str]]:
    """Get photo upload suggestions based on item category."""
    
    suggestions = {
        "clothing": [
            "Front view on flat surface or hanger",
            "Back view showing any patterns or details",
            "Close-up of brand label/tag",
            "Close-up of any flaws or wear",
            "Detail shots of unique features (buttons, zippers, etc.)"
        ],
        "electronics": [
            "Overall product view",
            "Screen/display (if applicable)",
            "All included accessories",
            "Brand label/model number",
            "Any ports, buttons, or controls",
            "Signs of wear or damage"
        ],
        "home": [
            "Overall product view",
            "Close-up of brand/maker marks",
            "Detail of materials/textures", 
            "Any flaws or damage",
            "Size reference (with ruler/coin)"
        ],
        "books": [
            "Front cover",
            "Back cover",
            "Spine showing title",
            "Copyright page",
            "Any damage to pages or binding"
        ],
        "toys": [
            "Overall toy view",
            "All included pieces",
            "Brand markings/labels",
            "Moving parts or features",
            "Any wear or missing pieces"
        ]
    }
    
    return {
        "category": category,
        "suggested_photos": suggestions.get(category.lower(), suggestions["home"]),
        "general_tips": [
            "Use natural lighting when possible",
            "Clean item before photographing",
            "Use plain background (white/neutral preferred)",
            "Take multiple angles",
            "Show scale with common objects if size unclear",
            "Photograph all flaws honestly"
        ]
    }


def batch_process_directory(
    input_dir: str = "photos",
    output_dir: str = "processed",
    remove_background: bool = False,  # More conservative default for batch
    enhance: bool = True
) -> Dict[str, Any]:
    """Process all photos in a directory, organizing by detected SKUs."""
    
    input_path = Path(input_dir)
    
    if not input_path.exists():
        raise ValueError(f"Input directory {input_dir} does not exist")
    
    # Find all image files
    all_photos = []
    for file_path in input_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
            all_photos.append(file_path)
    
    if not all_photos:
        return {"message": "No photos found to process", "processed_skus": []}
    
    # Group photos by detected SKU patterns
    sku_photos = {}
    unmatched_photos = []
    
    for photo in all_photos:
        # Try to extract SKU from filename
        sku = _extract_sku_from_filename(photo.name)
        if sku:
            if sku not in sku_photos:
                sku_photos[sku] = []
            sku_photos[sku].append(photo)
        else:
            unmatched_photos.append(photo)
    
    results = {
        "total_photos_found": len(all_photos),
        "matched_skus": list(sku_photos.keys()),
        "unmatched_photos": len(unmatched_photos),
        "processing_results": {},
        "errors": []
    }
    
    # Process each SKU's photos
    for sku, photos in sku_photos.items():
        try:
            # Check if item exists in database
            if get_item_by_sku(sku):
                result = process_item_photos(
                    sku=sku,
                    input_dir=input_dir,
                    output_dir=output_dir,
                    remove_background=remove_background,
                    enhance=enhance,
                    create_variants=True
                )
                results["processing_results"][sku] = result
            else:
                results["errors"].append(f"SKU {sku} not found in database")
        except Exception as e:
            results["errors"].append(f"Failed to process SKU {sku}: {str(e)}")
    
    return results


def _extract_sku_from_filename(filename: str) -> Optional[str]:
    """Extract SKU from filename using common patterns."""
    
    import re
    
    # Common SKU patterns
    patterns = [
        r'(\d{2}-\d{4})',  # Format: 25-0001
        r'([A-Z]{2,3}-\d{3,5})',  # Format: ABC-123
        r'(SKU[_-]?(\w+))',  # Format: SKU_123 or SKU-ABC
        r'^([A-Z0-9]{6,})_',  # Format: ABC123_photo.jpg
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename.upper())
        if match:
            return match.group(1)
    
    return None