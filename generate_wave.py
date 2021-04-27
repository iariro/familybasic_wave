# [python]　sin波の音をWAV形式で出力する
# https://qiita.com/kinaonao/items/c3f2ef224878fbd232f5

# Pythonでサウンドを扱う
# https://qiita.com/hisshi00/items/62c555095b8ff15f9dd2
# pip install simpleaudio

'''
import simpleaudio
import familybasic_wave.generate_wave

lines = [[10, "' 2021/04/27 kumagai"]]

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

class FBBitArray():
    def __init__(self):
        self.bits = []

    def add_bit(self, v):
        self.bits.append(v)

    def add_bits(self, v, num):
        self.bits += [v] * num

    def add_bytes(self, bytes_):
        for byte in bytes_:
            self.bits.append(True)
            for i in range(8):
                self.bits.append(True if byte & (1 << (7 - i)) > 0 else False)

    def add_word_little_endian(self, word):
        self.add_bytes([word % 0x100, word // 0x100])

    def add_word_big_endian(self, word):
        self.add_bytes([word // 0x100, word % 0x100])

    def make_info_header(self):
        self.add_bits(False, 20000)
        # テープマーク
        self.add_bits(True, 40)
        self.add_bits(False, 40)
        self.add_bit(True)

    def make_data_header(self):
        self.add_bits(False, 20000)
        # テープマーク
        self.add_bits(True, 20)
        self.add_bits(False, 20)
        self.add_bit(True)

    def make_info_block(self, file_name, data_len):
        # インフォメーション
        file_name_b = [ord(c) for c in '{:16}'.format(file_name[0:16])]

        self.add_bytes([0x02]) # 2=BASIC 3=BG-GRAPHIC
        self.add_bytes(file_name_b) # file name
        self.add_bytes([0x00]) # 0
        self.add_word_little_endian(data_len) # length
        self.add_bytes([0x00, 0x00])
        self.add_bytes([0x00, 0x00])
        self.add_bytes([0x00] * 104)

    def calc_checksum(self):
        checksum = 0
        for i, b in enumerate(self.bits):
            if i % 9 > 0 and b:
                checksum += 1
        return checksum

    def make_data_block(self, lines):
        for line in lines:
            line_len = len(line[1]) + 1
            self.add_bytes([line_len + 3])
            self.add_word_little_endian(line[0])
            self.add_bytes([ord(c) for c in line[1]] + [0x00])
        self.add_bytes([0x00])

    def bits_to_wave(self):
        cycle_length = 21.683
        volume = 1600

        wave_value = []
        cycle_count = 0
        cycle_count2 = 0
        for i, b in enumerate(self.bits):
            if b:
                cycle_count += cycle_length * 2
                for i in range(math.floor(cycle_count) - cycle_count2):
                    wave_value.append(-volume if i < cycle_length else volume)
            else:
                cycle_count += cycle_length
                for j in range(math.floor(cycle_count) - cycle_count2):
                    wave_value.append(-volume if j < cycle_length / 2 else volume)
            cycle_count2 += (math.floor(cycle_count) - cycle_count2)

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
    data_len = 0
    for line in lines:
        data_len += 1 + 2 + len(line[1]) + 1

    info_header_bits = FBBitArray()
    info_header_bits.make_info_header()
    binwave = info_header_bits.bits_to_wave()

    info_bits = FBBitArray()
    info_bits.make_info_block(file_name, data_len)
    info_sum = info_bits.calc_checksum()
    info_bits.add_word_big_endian(info_sum)
    info_bits.add_bit(True)
    binwave += info_bits.bits_to_wave()

    data_header_bits = FBBitArray()
    data_header_bits.make_data_header()
    binwave += data_header_bits.bits_to_wave()
    data_bits = FBBitArray()
    data_bits.make_data_block(lines)
    info_sum = info_bits.calc_checksum()
    data_bits.add_word_big_endian(info_sum)
    data_bits.add_bit(True)
    binwave += data_bits.bits_to_wave()
    return binwave
