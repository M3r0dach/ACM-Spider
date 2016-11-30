
def merge_dict(dict1, dict2, *more_dict):
    new_dict = dict(dict1, **dict2)
    for d in more_dict:
        new_dict.update(d)
    return new_dict
