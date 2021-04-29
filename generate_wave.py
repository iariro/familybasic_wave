# [python]　sin波の音をWAV形式で出力する
# https://qiita.com/kinaonao/items/c3f2ef224878fbd232f5

# Pythonでサウンドを扱う
# https://qiita.com/hisshi00/items/62c555095b8ff15f9dd2
# pip install simpleaudio

'''
import simpleaudio
import familybasic_wave.generate_wave

lines = [[10, "' 2021/04/27 test"]]

binwave =  familybasic_wave.generate_wave.make_binwave('1234567890abcde', lines)

playback = simpleaudio.play_buffer(binwave, 1, 2, familybasic_wave.generate_wave.fs)
playback.wait_done()
familybasic_wave.generate_wave.save_wave(binwave, 'basic.wav')
'''

import numpy as np
import wave
import struct
import math

fs = 44100

class FBByteArray():
    def __init__(self):
        self.bits = []

    def add_word_little_endian(self, word):
        self.add_bytes([word % 0x100, word // 0x100])

    def add_word_big_endian(self, word):
        self.add_bytes([word // 0x100, word % 0x100])

    def add_bytes(self, bytes_):
        for byte in bytes_:
            for i in range(8):
                self.bits.append(True if byte & (1 << (7 - i)) > 0 else False)

    def make_info_block(self, file_name, data_len):
        # インフォメーション
        file_name_b = [ord(c) for c in '{:16}'.format(file_name[0:16])]

        self.add_bytes([0x02]) # 2=BASIC 3=BG-GRAPHIC
        self.add_bytes(file_name_b) # file name
        self.add_bytes([0x00]) # 0
        self.add_word_little_endian(data_len) # length
        self.add_word_little_endian(0x703e) # load address
        self.add_word_little_endian(0x2020) # execute address
        self.add_bytes([0x00] * 104) # padding

    def calc_checksum(self):
        checksum = 0
        for i, b in enumerate(self.bits):
            if b:
                checksum += 1
        return checksum

    def make_data_block(self, lines):
        count = 0
        for line in lines:
            line_len = len(line[1]) + 1
            self.add_bytes([line_len + 3])
            self.add_word_little_endian(line[0])
            self.add_bytes([ord(c) for c in line[1]] + [0x00])
            count += 3 + line_len
        self.add_bytes([0x00])
        return count

class FBBitArray():
    def __init__(self):
        self.bits = []

    def add_bit(self, v):
        self.bits.append(v)

    def add_bits(self, v, num):
        self.bits += [v] * num

    def add_bytes_bits(self, bits):
        for i in range(0, len(bits), 8):
            self.bits += [True] + bits[i:i + 8]

    def make_header(self, num):
        self.add_bits(False, 20000)
        # テープマーク
        self.add_bits(True, num)
        self.add_bits(False, num)

    def bits_to_wave(self):
        cycle_length = 21.683
        volume = 1600

        wave_value = []
        cycle_count_f = 0
        cycle_count_i = 0
        for i, b in enumerate(self.bits):
            cycle_f = cycle_length
            if b:
                cycle_f *= 2

            cycle_count_f += cycle_f
            cycle_i = math.floor(cycle_count_f) - cycle_count_i
            for j in range(cycle_i):
                wave_value.append(-volume if j < cycle_f / 2 else volume)
                cycle_count_i += 1

        return struct.pack("h" * len(wave_value), *wave_value)

def save_wave(binwave, file_name):
    w = wave.Wave_write(file_name)
    # チャンネル数(1:モノラル,2:ステレオ)
    # サンプルサイズ(バイト)
    # サンプリング周波数
    # フレーム数
    # 圧縮形式(今のところNONEのみ)
    # 圧縮形式を人に判読可能な形にしたもの？通常'NONE'に対して'not compressed'
    p = (1, 2, fs, len(binwave), 'NONE', 'not compressed')
    w.setparams(p)
    w.writeframes(binwave)
    w.close()

def make_binwave(file_name, lines):

    # バイト列生成
    data_bytes = FBByteArray()
    data_len = data_bytes.make_data_block(lines)
    data_sum = data_bytes.calc_checksum()
    data_bytes.add_word_big_endian(data_sum)

    info_bytes = FBByteArray()
    info_bytes.make_info_block(file_name, data_len)
    info_sum = info_bytes.calc_checksum()
    info_bytes.add_word_big_endian(info_sum)

    # bit列生成
    info_bits = FBBitArray()
    info_bits.make_header(40)
    info_bits.add_bit(True)
    info_bits.add_bytes_bits(info_bytes.bits)
    info_bits.add_bit(True)
    binwave = info_bits.bits_to_wave()

    data_bits = FBBitArray()
    data_bits.make_header(20)
    data_bits.add_bit(True)
    data_bits.add_bytes_bits(data_bytes.bits)
    data_bits.add_bit(True)
    binwave += data_bits.bits_to_wave()

    return binwave
