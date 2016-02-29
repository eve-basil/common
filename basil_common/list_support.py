

def is_list_like(value):
    return value.startswith('[') and value.endswith(']')


def list_from_str(string):
    return string[1:-1].split(',')
