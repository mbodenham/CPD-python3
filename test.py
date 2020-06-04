import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
import torchvision.utils as utils
import torchvision.transforms as transforms

import time
import numpy as np
import pdb, os, argparse

from model.dataset import ImageGroundTruthFolder
from model.models import CPD, CPD_A

parser = argparse.ArgumentParser()
parser.add_argument('--datasets_path', type=str, default='./datasets/test', help='path to datasets, default = ./datasets/test')
parser.add_argument('--save_path', type=str, default='./results', help='path to save results, default = ./results')
parser.add_argument('--pth', type=str, default='CPD.pth', help='model filename, default = CPD.pth')
parser.add_argument('--attention', action='store_true', default=False, help='use attention branch model')
parser.add_argument('--imgres', type=int, default=352, help='image input and output resolution, default = 352')
args = parser.parse_args()

if torch.cuda.is_available():
    device = torch.device('cuda')
else:
    device = torch.device('cpu')

if args.attention:
    model = CPD_A()
else:
    model = CPD()

model.load_state_dict(torch.load(args.pth, map_location=torch.device(device)))
model.eval()
print('Loaded:', model.name)

transform = transforms.Compose([
            transforms.Resize((args.imgres, args.imgres)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
gt_transform = transforms.Compose([
            transforms.Resize((args.imgres, args.imgres)),
            transforms.ToTensor()])

dataset = ImageGroundTruthFolder(args.datasets_path, transform=transform, target_transform=gt_transform)
test_loader = DataLoader(dataset, batch_size=1, shuffle=False)

for pack in test_loader:
    image, gt, dataset, img_name, img_res = pack
    print('{} - {}'.format(dataset[0], img_name[0]))
    gt = np.asarray(gt, np.float32)
    gt /= (gt.max() + 1e-8)
    if device == 'cuda':
        image = image.cuda()

    if args.attention:
        res = model(image)
    else:
        _, res = model(image)

    res = F.interpolate(res, size=img_res[::-1], mode='bilinear', align_corners=False)
    res = res.sigmoid().data.cpu()

    save_path = './results/{}/{}/'.format(model.name, dataset[0])
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    filename = '{}{}.png'.format(save_path, img_name[0])
    utils.save_image(res,  filename)