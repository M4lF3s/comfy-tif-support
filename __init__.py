import os
from .LoadImageTif import LoadImageTif, get_hello

NODE_CLASS_MAPPINGS = {
    "Load Image (with tif support)" : LoadImageTif,
}

WEB_DIRECTORY = "js"

__all__ = ['NODE_CLASS_MAPPINGS', "WEB_DIRECTORY"]