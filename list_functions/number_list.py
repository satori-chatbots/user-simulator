import numpy as np
import yaml
import random

# these are only examples of functions to create lists.

def number_list(min, max, step):
    numberlist = np.arange(min, max, step)
    return numberlist.tolist()


def random_list():
    randomlist = np.random.randint(0, 10, 3)
    return randomlist.tolist()


def shuffle_list(file):
    with open(file, 'r', encoding="UTF-8") as f:
        yaml_file = yaml.safe_load(f)
    dic = list(yaml_file.keys())
    yaml_list = yaml_file[dic[0]]
    copy_list = yaml_list.copy()
    random.shuffle(copy_list)
    return copy_list