from enum import Enum


class Category(str, Enum):
    RECSYS = "recsys"
    ML = "ml"
    NLP = "nlp"
    CV = "cv"
    RL = "rl"
    OTHER = "other"
