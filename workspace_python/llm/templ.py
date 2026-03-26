import torch
import sys

print(torch.__version__)
print(torch.cuda.is_available())
print(sys.executable)
print(torch.__file__)


if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))