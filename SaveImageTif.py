import numpy as np
from tifffile import TiffWriter, RESUNIT, COMPRESSION
import os
import folder_paths

class SaveImageTif:

    def __init__(self):
        self.prefix_append = ""
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "The images to save."}),
                "icc_profile": ("RAW", {"tooltip": "The images to save."}),
                "x_dpi": ("FLOAT", {"forceInput": True}),
                "y_dpi": ("FLOAT", {"forceInput": True}),
                "filename_prefix": ("STRING", {"default": "ComfyUI",
                                               "tooltip": "The prefix for the file to save. This may include formatting information such as %date:yyyy-MM-dd% or %Empty Latent Image.width% to include values from nodes."}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "image"
    DESCRIPTION = "Saves the input images to your ComfyUI output directory."

    def save_images(self, images, filename_prefix="ComfyUI", prompt=None, icc_profile=None, x_dpi=None, y_dpi=None):
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()
        for (batch_number, image) in enumerate(images):
            i = 255. * image.cpu().numpy()
            i = np.clip(i, 0, 255).astype(np.uint8)
            # i = image.cpu().numpy().astype(np.float32)
            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.tif"

            with TiffWriter(os.path.join(full_output_folder, file)) as tif:
                tif.write(
                    i,
                    resolution=(x_dpi, y_dpi),
                    resolutionunit=RESUNIT.INCH,
                    compression=COMPRESSION.NONE,
                    iccprofile=icc_profile,
                )

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": "output"
            })
            counter += 1


        return { "ui": { "images": results } }


    @classmethod
    def VALIDATE_INPUTS(s, input_types):
        return True