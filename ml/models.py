"""Local CNN + patch-transformer branches fused by concatenation and projection."""
import torch
from torch import nn
NAMES=('cnn','vit','hybrid','lightweight','optimized','transfer_hybrid')
class CropModel(nn.Module):
    def __init__(self,architecture,classes):
        super().__init__()
        self.architecture=architecture
        width=48 if architecture in ('lightweight','optimized') else 96
        self.local=nn.Sequential(nn.Conv2d(3,24,3,2,1),nn.BatchNorm2d(24),nn.GELU(),
            nn.Conv2d(24,width,3,2,1),nn.BatchNorm2d(width),nn.GELU(),
            nn.Conv2d(width,width,3,2,1,groups=width),nn.Conv2d(width,width,1),nn.GELU(),
            nn.AdaptiveAvgPool2d(1),nn.Flatten()) if architecture!='vit' else None
        if architecture!='cnn':
            self.patch=nn.Conv2d(3,width,kernel_size=16,stride=16)
            self.position=nn.Parameter(torch.zeros(1,64,width))
            nn.init.trunc_normal_(self.position,std=.02)
            layer=nn.TransformerEncoderLayer(width,4,width*3,dropout=.1,batch_first=True,norm_first=True)
            self.global_encoder=nn.TransformerEncoder(layer,2 if width==48 else 4,enable_nested_tensor=False)
            self.norm=nn.LayerNorm(width)
        features=width*(2 if architecture not in ('cnn','vit') else 1)
        self.head=nn.Sequential(nn.Linear(features,width),nn.GELU(),nn.Dropout(.2),nn.Linear(width,classes))
    def forward(self,x):
        branches=[]
        if self.local is not None:branches.append(self.local(x))
        if self.architecture!='cnn':
            tokens=self.patch(x).flatten(2).transpose(1,2)+self.position
            branches.append(self.norm(self.global_encoder(tokens).mean(1)))
        return self.head(torch.cat(branches,dim=1))
class TransferHybrid(CropModel):
    """ImageNet MobileNet local features fused with a trainable patch Transformer."""
    def __init__(self,classes,pretrained=False):
        super().__init__('lightweight',classes)
        from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
        encoder=mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT if pretrained else None).features
        self.local=nn.Sequential(encoder,nn.AdaptiveAvgPool2d(1),nn.Flatten(),nn.Linear(576,48))
        if pretrained:
            for parameter in encoder.parameters():parameter.requires_grad=False

def build_model(architecture,classes,pretrained=False):
    if architecture=='transfer_hybrid':return TransferHybrid(classes,pretrained)
    if architecture not in NAMES:raise ValueError(f'Unknown architecture: {architecture}')
    return CropModel(architecture,classes)
