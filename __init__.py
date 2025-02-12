import os
from .LoadImageTif import LoadImageTif, preview_tiff
from .SaveImageTif import SaveImageTif

NODE_CLASS_MAPPINGS = {
    "Load TIFF" : LoadImageTif,
    "Save TIFF" : SaveImageTif
}

WEB_DIRECTORY = "js"

__all__ = ['NODE_CLASS_MAPPINGS', "WEB_DIRECTORY"]