def page(items, index, size):
    start = index * size
    end = min(start + size, len(items) - 1)
    return items[start:end]
