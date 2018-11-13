# The Base58 digits
base58_digits = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
#length = len(base58_digits)


def encode58(baseint):
    basedigits = []
    if baseint == 0:
        return '0'
    while baseint > 0:
        baseint, rem = divmod(baseint, 58)
        basedigits.insert(0, base58_digits[rem])
    return ''.join(basedigits)

def decode58(basestring):
    baseint = 0
    for char in basestring:
        baseint *= 58
        digit = base58_digits.index(char)
        baseint += digit
    return baseint