import torch
from transformers import RobertaForSequenceClassification, AutoTokenizer

def loadModel():
    model = RobertaForSequenceClassification.from_pretrained("wonrax/phobert-base-vietnamese-sentiment")
    tokenizer = AutoTokenizer.from_pretrained("wonrax/phobert-base-vietnamese-sentiment", use_fast=False)
    return model, tokenizer

def sentimentAnalysisOneComment(model, tokenizer, comment):
    input_tensor = tokenizer.encode(comment, padding=True, truncation=True, max_length=256, return_tensors="pt")

    with torch.no_grad():
        outputs = model(input_tensor)
        prediction = outputs.logits
        prediction = torch.argmax(prediction)

    if prediction == 0:
        sentiment = 'Negative'
    elif prediction == 1:
        sentiment = 'Positive'
    else:
        sentiment = 'Neutral'

    return sentiment
