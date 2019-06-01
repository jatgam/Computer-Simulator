def extractBits(number, numBits, position):
    """
    Extract bits from a large number and return the number.

    Parameters:
        number          the number to extract from
        numBits         the amount of bits to extract
        position        the position to start from

    Returns:
        int             the int of the extracted bits
    """
    return ( (1 << numBits) - 1 & (number >> (position-1)) )
