
def read_bits(data, start, end):
    bits = []
    plus_data = []
    minus_data = []
    pd = None
    for i, d in enumerate(data[start:end]):
        if d < 0:
            # minus
            if pd is not None and pd >= 0:
                # plus -> minus
                if len(plus_data) > 0 and len(minus_data) > 0:
                    if len(plus_data) <= 15:
                        b1 = 0
                    else:
                        b1 = 1
                    bits.append(b1)

                plus_data.clear()
                minus_data.clear()
            minus_data.append(d)
        else:
            # plus
            plus_data.append(d)
        pd = d
    return bits

def bits_to_bytes(bits):
    byte = 0
    byte_count = 0
    bytes_ = []
    for b in bits:
        byte = (byte << 1) + b
        byte_count += 1
        if byte_count == 9:
            byte -= 0x100
            bytes_.append(byte)
            byte = 0
            byte_count = 0
    return bytes_

def read_info_data(bits):
    count = 0
    pb = None
    area = False
    total_len = 0
    checksum = 0
    bits2 = []
    info_block = None
    lines= []
    for i, b in enumerate(bits):
        if pb is not None:
            if b == pb:
                count += 1
            else:
                count = 1

        if area == 0:
            # インフォーメーションブロック前
            if b > 0:
                checksum += 1
            if b == 1 and count == 40:
                area = 1

        elif area == 1:
            # インフォーメーションブロック-テープマーク１後
            if b > 0:
                checksum += 1
            if b == 0 and count == 40:
                area = 2

        elif area == 2:
            # インフォーメーションブロック-テープマーク２後
            area = 3

        elif area == 3:
            # インフォーメーションブロック-正味
            checksum += b

            bits2.append(b)
            if len(bits2) == 9 * 128:
                info_bytes = bits_to_bytes(bits2)
                info_block = {'attribute' : info_bytes[0],
                                     'filename' : ['%c' % c for c in info_bytes[1:17]],
                                     'length' : info_bytes[18] + info_bytes[19] * 0x100}
                bits2.clear()
                area = 4

        elif area == 4:
            # インフォーメーションブロック-チェックサム
            bits2.append(b)
            if len(bits2) == 9 * 2:
                ckecksum_bytes = bits_to_bytes(bits2)
                print('checksum=%x %x %x' % (ckecksum_bytes[0], ckecksum_bytes[1], checksum))
                bits2.clear()
                area = 10
                chechsum = 0

        elif area == 10:
            # データブロック-テープマーク１後
            if b > 0:
                checksum += 1
            if pb == 1 and count == 20:
                area = 11

        elif area == 11:
            # データブロック-テープマーク２後
            if b > 0:
                checksum += 1
            if pb == 0 and count == 20:
                area = 12

        elif area == 12:
            # データブロック-テープマーク２後
                area = 13

        elif area == 13:
            # データブロック-バイト数
            if b > 0:
                checksum += 1
            bits2.append(b)
            if len(bits2) == 9 * 1:
                length_bytes = bits_to_bytes(bits2)
                line_len = length_bytes[0]
                bits2.clear()
                area = 14

        elif area == 14:
            # データブロック-行番号・テキスト
            if b > 0:
                checksum += 1

            bits2.append(b)
            if len(bits2) == 9 * (line_len - 1):

                line_bytes = bits_to_bytes(bits2)
                total_len += line_len + 2

                line = '%d ' % line_bytes[0]
                for byte in line_bytes[2:-1]:
                    if 0x20 <= byte <= 0x7f:
                        line += '%c' % byte
                    else:
                        line += '%x' % byte

                lines.append(line)
                if total_len + 1 >= info_block['length']:
                    area = 15
                else:
                    area = 13
                bits2.clear()

        elif area == 15:
            # データブロック-チェックサム
            bits2.append(b)
            if len(bits2) == 9 * 2:
                ckecksum_bytes = bits_to_bytes(bits2)
                print('checksum=%x %x' % (ckecksum_bytes[0], ckecksum_bytes[1]))
                bits2.clear()
                area = 16

        pb = b
    
    return info_block, lines
