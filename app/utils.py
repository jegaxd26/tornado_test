def bxor(packet):
    checksum = 0
    for byte in packet:
        checksum ^= byte
    return checksum.to_bytes(1,'little')
