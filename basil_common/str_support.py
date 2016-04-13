

def as_int(value):
    try:
        return int(value)
    except ValueError:
        return None


def urljoin(*parts):
    url = parts[0]
    for p in parts[1:]:
        if url[-1] != '/':
            url += '/'
        url += p
    return url
