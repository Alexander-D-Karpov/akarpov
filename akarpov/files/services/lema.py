from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from pymorphy3 import MorphAnalyzer

# Set up stop words
english_stopwords = set(stopwords.words("english"))
russian_stopwords = set(stopwords.words("russian"))

# Set up lemmatizers
english_lemmatizer = None
russian_lemmatizer = None


def lemmatize_and_remove_stopwords(text, language="english"):
    # Tokenize the text
    global english_lemmatizer, russian_lemmatizer
    tokens = word_tokenize(text)

    # Lemmatize each token based on the specified language
    lemmatized_tokens = []
    for token in tokens:
        if language == "russian":
            if not russian_lemmatizer:
                russian_lemmatizer = MorphAnalyzer()
            lemmatized_token = russian_lemmatizer.parse(token)[0].normal_form
        else:  # Default to English
            if not english_lemmatizer:
                english_lemmatizer = WordNetLemmatizer()
            lemmatized_token = english_lemmatizer.lemmatize(token)
        lemmatized_tokens.append(lemmatized_token)

    # Remove stop words
    filtered_tokens = [
        token
        for token in lemmatized_tokens
        if token not in english_stopwords and token not in russian_stopwords
    ]

    # Reconstruct the text
    filtered_text = " ".join(filtered_tokens)
    return filtered_text
