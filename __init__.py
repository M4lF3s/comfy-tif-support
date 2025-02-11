import os
from .LoadImageTif import LoadImageTif, preview_tiff

NODE_CLASS_MAPPINGS = {
    "Load TIFF" : LoadImageTif,
}

WEB_DIRECTORY = "js"

__all__ = ['NODE_CLASS_MAPPINGS', "WEB_DIRECTORY"]