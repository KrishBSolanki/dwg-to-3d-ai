# # src/perception/cubicasa/infer.py

# import torch
# import cv2
# import numpy as np
# from pathlib import Path

# from .model import load_cubicasa_model


# # ---------------------------------------------------------
# # IMAGE PREPROCESSING
# # ---------------------------------------------------------

# def preprocess_image(image_path: Path, device: str = "cpu"):
#     """
#     Load PNG floorplan and convert to model-ready tensor.

#     Returns:
#         tensor (1, 3, H, W) normalized to [0,1]
#         original_image (H, W, 3)
#     """

#     if not image_path.exists():
#         raise FileNotFoundError(f"Image not found: {image_path}")

#     image = cv2.imread(str(image_path))
#     image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

#     original = image.copy()

#     image = image.astype(np.float32) / 255.0
#     image = np.transpose(image, (2, 0, 1))  # HWC → CHW
#     image = np.expand_dims(image, axis=0)   # Add batch dim

#     tensor = torch.from_numpy(image).to(device)

#     return tensor, original


# # ---------------------------------------------------------
# # POST LOGIT → MASK
# # ---------------------------------------------------------

# def logits_to_mask(logits):
#     """
#     Convert raw logits into class index mask.

#     Args:
#         logits: Tensor (B, C, H, W)

#     Returns:
#         mask: numpy array (H, W)
#     """
#     probs = torch.softmax(logits, dim=1)
#     mask = torch.argmax(probs, dim=1)
#     return mask.squeeze(0).cpu().numpy()


# # ---------------------------------------------------------
# # MAIN INFERENCE FUNCTION
# # ---------------------------------------------------------

# def run_cubicasa_inference(image_path: str, device: str = "cpu"):
#     """
#     Full CubiCasa pipeline:
#         PNG → model → semantic masks

#     Returns:
#         {
#             "rooms": mask,
#             "walls": mask,
#             "doors": mask,
#             "windows": mask
#         }
#     """

#     device = "cuda" if torch.cuda.is_available() else device

#     model = load_cubicasa_model(device=device)

#     image_tensor, original_image = preprocess_image(
#         Path(image_path),
#         device
#     )

#     outputs = model(image_tensor)

#     # -------------------------------------------------
#     # EXPECTED OUTPUT KEYS FROM CUBICASA DECODER
#     # -------------------------------------------------
#     # Typical CubiCasa outputs:
#     #   outputs["room"]
#     #   outputs["wall"]
#     #   outputs["door"]
#     #   outputs["window"]

#     semantic_maps = {}

#     for key in outputs:
#         semantic_maps[key] = logits_to_mask(outputs[key])

#     print("✅ CubiCasa inference complete")

#     return semantic_maps
import torch
import torch.nn.functional as F
import numpy as np
import cv2

from .model import CubiCasaModel


class CubiCasaInference:
    def __init__(self, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Load wrapper
        self.wrapper = CubiCasaModel()

        # Move INTERNAL torch model
        self.model = self.wrapper.model.to(self.device)
        self.model.eval()

    def preprocess(self, image_path):
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (512, 512))
        image = image.astype(np.float32) / 255.0

        image = np.transpose(image, (2, 0, 1))
        image = torch.from_numpy(image).unsqueeze(0)

        return image.to(self.device)

    @torch.no_grad()
    def predict(self, image_path):
        x = self.preprocess(image_path)

        output = self.model(x)

        probs = F.softmax(output, dim=1)
        pred = torch.argmax(probs, dim=1)

        return pred.squeeze(0).cpu().numpy()
