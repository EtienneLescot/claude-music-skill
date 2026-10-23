"""One-time conversion of NVIDIA's BigVGAN v2 (MIT) to ONNX, run by setup.py with PyTorch in a throwaway uv
environment, so that rendering needs only onnxruntime.

    uv run --python 3.12 --with torch --with onnx --with huggingface_hub --with librosa --with matplotlib --with tqdm \
        python -I bigvgan_onnx.py <folder with bigvgan.py, config.json and bigvgan_generator.pt>"""
import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
sys.path.insert(0, str(d))
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402

import alias_free_activation.torch.filter as lowpass  # noqa: E402
import alias_free_activation.torch.resample as resample  # noqa: E402
from bigvgan import BigVGAN  # noqa: E402
from env import AttrDict  # noqa: E402


def edge(x, p):
    """Edge padding as a concat: the exporter fails on ONNX's Pad in edge mode."""
    return torch.cat([x[..., :1].repeat(1, 1, p[0]), x, x[..., -1:].repeat(1, 1, p[1])], -1)


def up(self, x):                                       # BigVGAN's own, with the channel count frozen for the exporter
    c = int(x.shape[1])
    x = self.ratio * F.conv_transpose1d(edge(x, (self.pad, self.pad)), self.filter.repeat(c, 1, 1),
                                        stride=self.stride, groups=c)
    return x[..., self.pad_left:-self.pad_right]


def low(self, x):
    c = int(x.shape[1])
    if self.padding:
        x = edge(x, (self.pad_left, self.pad_right)) if self.padding_mode == 'replicate' else \
            F.pad(x, (self.pad_left, self.pad_right), mode=self.padding_mode)
    return F.conv1d(x, self.filter.repeat(c, 1, 1), stride=self.stride, groups=c)


resample.UpSample1d.forward, lowpass.LowPassFilter1d.forward = up, low
g = BigVGAN(AttrDict(json.loads((d / 'config.json').read_text())), use_cuda_kernel=False)
g.load_state_dict(torch.load(d / 'bigvgan_generator.pt', map_location='cpu', weights_only=True)['generator'])
g.eval()
g.remove_weight_norm()
torch.onnx.export(g, torch.randn(1, 128, 400), str(d / 'bigvgan.onnx'), input_names=['mel'], output_names=['waveform'],
                  dynamic_axes={'mel': {2: 'frames'}, 'waveform': {2: 'samples'}}, opset_version=17, dynamo=False)
print('bigvgan.onnx written')
