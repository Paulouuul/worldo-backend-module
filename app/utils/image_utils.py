# app/utils/image_utils.py
from PIL import Image, ImageSequence
import io
from typing import Optional, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)

class ConvertOptions:
    def __init__(self, format: str = 'webp', quality: int = 80, width: Optional[int] = None, height: Optional[int] = None, preserve_transparency: bool = True, fit: str = 'inside'):
        self.format = format
        self.quality = quality
        self.width = width
        self.height = height
        self.preserve_transparency = preserve_transparency
        self.fit = fit

class ConvertResult:
    def __init__(self, buffer: bytes, format: str, original_size: int, optimized_size: int, is_animated: bool, metadata: Optional[Dict[str, Any]] = None):
        self.buffer = buffer
        self.format = format
        self.original_size = original_size
        self.optimized_size = optimized_size
        self.is_animated = is_animated
        self.metadata = metadata or {}

def add_animated_suffix(filename: str, is_gif: bool) -> str:
    if not is_gif: return filename
    last_dot = filename.rfind('.')
    if last_dot == -1: return f"{filename}-animated"
    return f"{filename[:last_dot]}-animated{filename[last_dot:]}"

def normalize_mime_type(mime_type: str) -> str:
    return 'image/jpeg' if mime_type == 'image/jfif' else mime_type

def _ensure_bytes(data: Union[bytes, io.BytesIO, bytearray]) -> bytes:
    """Garante de forma simples que o buffer está em bytes"""
    if isinstance(data, bytes):
        return data
    elif isinstance(data, bytearray):
        return bytes(data)
    elif hasattr(data, 'getvalue'):
        return data.getvalue()
    elif hasattr(data, 'read'):
        return data.read()
    raise TypeError(f"Formato binário não suportado: {type(data)}")

def _resize_image(img: Image.Image, width: Optional[int], height: Optional[int], fit: str = 'inside') -> Image.Image:
    if not width and not height: return img
    original_width, original_height = img.size
    
    if fit == 'inside' or fit == 'contain':
        img.thumbnail((width or 99999, height or 99999), Image.Resampling.LANCZOS)
    elif fit == 'cover':
        target_ratio = width / height if width and height else 1
        img_ratio = original_width / original_height
        if img_ratio > target_ratio:
            new_width = int(original_height * target_ratio)
            x_offset = (original_width - new_width) // 2
            img = img.crop((x_offset, 0, x_offset + new_width, original_height))
        else:
            new_height = int(original_width / target_ratio)
            y_offset = (original_height - new_height) // 2
            img = img.crop((0, y_offset, original_width, y_offset + new_height))
        if width and height:
            img = img.resize((width, height), Image.Resampling.LANCZOS)
    elif fit == 'fill' and width and height:
        img = img.resize((width, height), Image.Resampling.LANCZOS)
    elif fit == 'outside' and width and height:
        ratio = max(width / original_width, height / original_height)
        img = img.resize((int(original_width * ratio), int(original_height * ratio)), Image.Resampling.LANCZOS)
    return img

def _convert_animated_gif(img: Image.Image, quality: int, width: Optional[int], height: Optional[int], fit: str) -> bytes:
    frames, durations = [], []
    for frame in ImageSequence.Iterator(img):
        if width or height: frame = _resize_image(frame, width, height, fit)
        if frame.mode not in ('RGBA', 'RGB'): frame = frame.convert('RGBA')
        durations.append(frame.info.get('duration', 100))
        frames.append(frame)
    
    output = io.BytesIO()
    if frames:
        frames[0].save(output, format='WEBP', quality=quality, save_all=True, append_images=frames[1:], duration=durations, loop=0, method=6)
    return output.getvalue()

def _convert_static_image(img: Image.Image, quality: int, width: Optional[int], height: Optional[int], fit: str, preserve_transparency: bool = True) -> bytes:
    if width or height: img = _resize_image(img, width, height, fit)
    
    if preserve_transparency and img.mode in ('RGBA', 'LA', 'P'):
        if img.mode == 'P': img = img.convert('RGBA')
    else:
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
    output = io.BytesIO()
    img.save(output, format='WEBP', quality=quality, method=6, lossless=quality >= 90)
    return output.getvalue()

def convert_to_webp(input_buffer: Union[bytes, io.BytesIO, bytearray], original_type: str, options: ConvertOptions) -> ConvertResult:
    image_bytes = _ensure_bytes(input_buffer)
    original_size = len(image_bytes)
    normalized_type = normalize_mime_type(original_type)
    is_gif = normalized_type == 'image/gif'
    is_animated = options.format == 'webp-animated' or is_gif
    quality = max(1, min(100, options.quality))
    
    try:
        img = Image.open(io.BytesIO(image_bytes))
        metadata = {'width': img.width, 'height': img.height, 'frames': getattr(img, 'n_frames', 1)}
    except Exception as e:
        logger.warning(f"⚠️ Erro ler metadados: {e}")
        metadata, img = {}, None
        
    if is_gif and is_animated:
        if img is None: img = Image.open(io.BytesIO(image_bytes))
        optimized_buffer = _convert_animated_gif(img, quality, options.width, options.height, options.fit)
        is_animated_result = True
    else:
        if img is None: img = Image.open(io.BytesIO(image_bytes))
        optimized_buffer = _convert_static_image(img, quality, options.width, options.height, options.fit, options.preserve_transparency)
        is_animated_result = False
        
    optimized_size = len(optimized_buffer)
    return ConvertResult(buffer=optimized_buffer, format='webp', original_size=original_size, optimized_size=optimized_size, is_animated=is_animated_result, metadata=metadata)