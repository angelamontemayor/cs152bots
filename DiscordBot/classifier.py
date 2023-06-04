import torch
import torch.nn as nn
from torchvision import datasets, models, transforms
from PIL import Image
from tqdm import tqdm
import requests
from io import BytesIO

def image_loader(url):
    """load image, returns tensor"""
    transform = transforms.Compose([
    transforms.Resize(256),  # or whatever size you trained on
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    image = transform(image).float()
    image = image.unsqueeze(0)
    return image

def classify(url):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = models.resnet50(pretrained=True)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, 3)
    model = model.to(device)
    params = torch.load('tensor.pt', map_location=torch.device('cpu'))
    model.load_state_dict(params)
    model.eval()
    image = image_loader(url)
    
    with torch.no_grad():
        prediction = model(image)
        prediction = prediction.argmax(dim=1)
        if prediction == 1:
            return "kitten"
	elif prediction == 0:
	    return "adult cat"
        else:
            return "not a cat"
