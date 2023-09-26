import pycld2 as cld2
import spacy
import torch
from transformers import AutoModel, AutoTokenizer

# load ml classes and models on first request
# TODO: move to outer server/service
nlp = None
ru_nlp = None

ru_model = None
ru_tokenizer = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_text_embedding(text: str):
    global nlp, ru_nlp, ru_model, ru_tokenizer

    is_reliable, text_bytes_found, details = cld2.detect(text)
    if is_reliable:
        lang = details[0]
        if lang[1] in ["ru", "en"]:
            lang = lang[1]
        else:
            return None
    else:
        return None

    if lang == "ru":
        if not ru_nlp:
            ru_nlp = spacy.load("ru_core_news_md", disable=["parser", "ner"])
        lema = " ".join([token.lemma_ for token in ru_nlp(text)])
        if not ru_model:
            ru_model = AutoModel.from_pretrained("DeepPavlov/rubert-base-cased")
        if not ru_tokenizer:
            ru_tokenizer = AutoTokenizer.from_pretrained("DeepPavlov/rubert-base-cased")
        encodings = ru_tokenizer(
            lema,  # the texts to be tokenized
            padding=True,  # pad the texts to the maximum length (so that all outputs have the same length)
            return_tensors="pt",  # return the tensors (not lists)
        )
        with torch.no_grad():
            # get the model embeddings
            embeds = ru_model(**encodings)
        embeds = embeds[0]
    elif lang == "en":
        embeds = None
    else:
        embeds = None

    return embeds
