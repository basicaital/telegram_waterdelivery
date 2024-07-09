from functools import lru_cache


@lru_cache(maxsize=128)
def get_bottle_word(quantity):
    if 11 <= quantity % 100 <= 19:
        return "бутылей"
    elif quantity % 10 == 1:
        return "бутыль"
    elif 2 <= quantity % 10 <= 4:
        return "бутыли"
    else:
        return "бутылей"
