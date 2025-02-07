# Code is basically copied from OG Comfy Load Image node
# Added some extra handling of tif file, e.g. proper preview and metadata output

import fractions
from decimal import Decimal
import torch
import os
import sys
import hashlib
import base64
from io import BytesIO
from PIL import Image, ImageOps, ImageSequence
import numpy as np
from tifffile import imread, TiffFile
from aiohttp import web
from server import PromptServer


sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))

import folder_paths
import node_helpers


@PromptServer.instance.routes.get("/tiff")
async def preview_tiff(request):
    if "filename" in request.rel_url.query:
        filename = request.rel_url.query["filename"]
        filename, output_dir = folder_paths.annotated_filepath(filename)

        if not filename:
            return web.Response(status=400)

        # validation for security: prevent accessing arbitrary path
        if filename[0] == '/' or '..' in filename:
            return web.Response(status=400)

        if output_dir is None:
            type = request.rel_url.query.get("type", "output")
            output_dir = folder_paths.get_directory_by_type(type)

        if output_dir is None:
            return web.Response(status=400)

        if "subfolder" in request.rel_url.query:
            full_output_dir = os.path.join(output_dir, request.rel_url.query["subfolder"])
            if os.path.commonpath((os.path.abspath(full_output_dir), output_dir)) != output_dir:
                return web.Response(status=403)
            output_dir = full_output_dir

        filename = os.path.basename(filename)
        file = os.path.join(output_dir, filename)

        if os.path.isfile(file):
            with Image.open(file) as img:
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)

                return web.Response(body=buffer.read(), content_type="image/png")

    return web.Response(status=404)


class LoadImageTif:

    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        # Filter for .tif and .tiff files
        files = [f for f in os.listdir(input_dir)
                 if os.path.isfile(os.path.join(input_dir, f))
                 and f.lower().endswith(('.tif', '.tiff'))]
        return {"required":
                    {
                        "Upload": ("CUSTOM", {
                            "image_upload": True,
                            "file_types": ["tif", "tiff"],
                            "mime_types": ["image/tiff"],
                            "update_preview": True
                        }),
                        #"image": (sorted(files), {
                        #    "image_upload": True,
                        #    "file_types": ["tif", "tiff"],
                        #    "mime_types": ["image/tiff"],
                        #    "update_preview": True
                        #})
                    },
                }

    RETURN_TYPES = ("IMAGE", "MASK", "FLOAT", "FLOAT", "RAW")
    RETURN_NAMES = ("image", "mask", "x_dpi", "y_dpi", "icc_profile")
    CATEGORY = "image"
    FUNCTION = "load_image"

    def load_image(self, image):
        image_path = folder_paths.get_annotated_filepath(image)
        print("Loading image:", image_path)

        magic_numbers = {
            bytes([0x49, 0x49, 0x2A, 0x00]): "little endian TIFF",
            bytes([0x4D, 0x4D, 0x00, 0x2A]): "big endian TIFF",
            bytes([0x49, 0x49, 0x2B, 0x00]): "little endian BigTIFF",
            bytes([0x4D, 0x4D, 0x00, 0x2B]): "big endian BigTIFF"
        }

        # Verify if it's actually a TIFF file
        max_read_size = max(len(m) for m in magic_numbers.keys())
        with open(image_path, 'rb') as fd:
            file_head = fd.read()[:max_read_size]

        if file_head not in magic_numbers:
            raise ValueError("Selected file is not a valid TIFF image")

        with TiffFile(image_path) as tif:
            tags = tif.pages[0].tags

            # Extract DPI information
            x_dpi = float(fractions.Fraction(*tags['XResolution'].value)) if 'XResolution' in tags else 72.0
            y_dpi = float(fractions.Fraction(*tags['YResolution'].value)) if 'YResolution' in tags else 72.0

            # Get ICC profile as raw bytes
            icc_profile = tags["InterColorProfile"].value if "InterColorProfile" in tags else bytes()

            image = tif.asarray().astype(np.float32) / 255.0

        tensor = torch.from_numpy(image)[None,]

        # Create appropriate mask
        if len(image.shape) > 2 and image.shape[2] == 4:  # RGBA image
            mask = torch.from_numpy(image[:, :, 3]).float()
        else:
            mask = torch.zeros((image.shape[0], image.shape[1]), dtype=torch.float32, device="cpu")

        return (tensor, mask, x_dpi, y_dpi, icc_profile)


    @classmethod
    def PREVIEW_OUTPUTS(s):
        return ["image"]

    def get_image_preview(self):
        try:
            return {"image": self._preview} # if hasattr(self, '_preview') else None
        except Exception as e:
            print(f"Error getting preview: {e}")
            return None


    @classmethod
    def IS_CHANGED(s, image):
        print("Is CHANGED")
        image_path = folder_paths.get_annotated_filepath(image)
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()


    @classmethod
    def VALIDATE_INPUTS(s, image):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)

        # Validate file extension
        if not image.lower().endswith(('.tif', '.tiff')):
            return "File must be a TIFF image (*.tif, *.tiff)"

        # Validate TIFF format using magic numbers
        image_path = folder_paths.get_annotated_filepath(image)
        magic_numbers = {
            bytes([0x49, 0x49, 0x2A, 0x00]): "little endian TIFF",
            bytes([0x4D, 0x4D, 0x00, 0x2A]): "big endian TIFF",
            bytes([0x49, 0x49, 0x2B, 0x00]): "little endian BigTIFF",
            bytes([0x4D, 0x4D, 0x00, 0x2B]): "big endian BigTIFF"
        }

        with open(image_path, 'rb') as fd:
            file_head = fd.read()[:4]
            if file_head not in magic_numbers:
                return "File is not a valid TIFF image"

        return True