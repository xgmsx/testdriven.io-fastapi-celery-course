import random
from string import ascii_lowercase


def random_username():
    username = "".join([random.choice(ascii_lowercase) for i in range(5)])
    return username
