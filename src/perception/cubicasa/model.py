# # src/perception/cubicasa/model.py

# import torch
# import torch.nn as nn
# from pathlib import Path

# # -------------------------------------------------
# # IMPORT ORIGINAL CUBICASA ARCHITECTURE
# # -------------------------------------------------
# # These files must come from the CubiCasa repo
# # You can COPY them into src/perception/cubicasa/
# # (encoder.py, decoder.py, etc.)

# from .networks.encoder import Encoder
# from .networks.decoder import Decoder


# # -------------------------------------------------
# # CUBICASA MODEL WRAPPER (INFERENCE ONLY)
# # -------------------------------------------------

# class CubiCasaNet(nn.Module):
#     """
#     Thin production wrapper around CubiCasa5K CNN.
#     This class:
#     - builds encoder + decoder
#     - loads pretrained weights
#     - runs forward inference only
#     """

#     def __init__(self, weights_path: Path, device: str = "cpu"):
#         super().__init__()

#         self.device = torch.device(device)

#         # Encoder / Decoder (as per CubiCasa architecture)
#         self.encoder = Encoder()
#         self.decoder = Decoder()

#         self.to(self.device)
#         self.eval()

#         self._load_weights(weights_path)

#     # -------------------------------------------------
#     # LOAD CHECKPOINT
#     # -------------------------------------------------

#     def _load_weights(self, weights_path: Path):
#         if not weights_path.exists():
#             raise FileNotFoundError(f"CubiCasa weights not found: {weights_path}")

#         checkpoint = torch.load(weights_path, map_location=self.device)

#         if "model_state" not in checkpoint:
#             raise RuntimeError("Invalid CubiCasa checkpoint: missing model_state")

#         self.load_state_dict(checkpoint["model_state"], strict=True)

#         print(f"✅ CubiCasa weights loaded from {weights_path}")

#     # -------------------------------------------------
#     # FORWARD PASS
#     # -------------------------------------------------

#     @torch.no_grad()
#     def forward(self, x: torch.Tensor):
#         """
#         Input:
#             x : torch.Tensor
#                 Shape (B, 3, H, W)
#                 Range [0, 1]

#         Output:
#             dict of semantic logits:
#                 {
#                     'rooms': Tensor,
#                     'walls': Tensor,
#                     'doors': Tensor,
#                     'windows': Tensor
#                 }
#         """

#         features = self.encoder(x)
#         outputs = self.decoder(features)

#         return outputs


# # -------------------------------------------------
# # FACTORY FUNCTION (USED BY infer.py)
# # -------------------------------------------------

# def load_cubicasa_model(device: str = "cpu") -> CubiCasaNet:
#     """
#     Safe loader used by perception_router / infer.py
#     """

#     base_dir = Path(__file__).resolve().parent
#     weights_path = base_dir / "weights" / "cubicasa.pkl"

#     model = CubiCasaNet(
#         weights_path=weights_path,
#         device=device
#     )

#     return model
import torch
from pathlib import Path

# IMPORTANT: use relative import
from .floortrans.models.hg_furukawa_original import hg_furukawa_original


class CubiCasaModel:
    def __init__(self, weight_path=None, device="cpu"):
        self.device = torch.device(device)

        # -------------------------
        # Default weight path
        # -------------------------
        if weight_path is None:
            weight_path = (
                Path(__file__).parent
                / "weights"
                / "cubicasa.pkl"
            )

        print(f"📦 Loading CubiCasa weights from: {weight_path}")

        # -------------------------
        # Build EXACT architecture
        # -------------------------
        # Official CubiCasa multi-task model uses 44 classes
        n_classes = 44
        self.model = hg_furukawa_original(n_classes=n_classes)
        self.model.to(self.device)

        # -------------------------
        # Load checkpoint safely
        # -------------------------
        checkpoint = torch.load(weight_path, map_location=self.device)

        # Some checkpoints wrap state_dict inside "model_state"
        if isinstance(checkpoint, dict) and "model_state" in checkpoint:
            state_dict = checkpoint["model_state"]
        else:
            state_dict = checkpoint

        # Load strictly to ensure architecture match
        self.model.load_state_dict(state_dict, strict=True)

        self.model.eval()

        print("✅ CubiCasa model loaded successfully")

    # ------------------------------------
    # Forward helper
    # ------------------------------------
    def __call__(self, x):
        with torch.no_grad():
            return self.model(x)
