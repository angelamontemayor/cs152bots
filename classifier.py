import torch
import torch.nn as nn
from torchvision import datasets, models, transforms
from PIL import Image
from tqdm import tqdm


def image_loader(image_name):
    """load image, returns tensor"""
    transform = transforms.Compose([
    transforms.Resize(256),  # or whatever size you trained on
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
    
    image = Image.open(image_name)
    image = transform(image).float()
    image = image.unsqueeze(0)
    return image

def main():
    img_path = "adults/00001496_024.jpg" #Change this as necessary
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = models.resnet50(pretrained=True)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, 2)
    model = model.to(device)
    params = torch.load('tensor.pt', map_location=torch.device('cpu'))
    model.load_state_dict(params)
    model.eval()
    image = image_loader(img_path)
    
    with torch.no_grad():
    prediction = model(image)
    prediction = prediction.argmax(dim=1)
    if prediction == 1:
        print('Kitten')
    else:
        print('Adult Cat')