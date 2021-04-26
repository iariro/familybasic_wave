# [python]　sin波の音をWAV形式で出力する
# https://qiita.com/kinaonao/items/c3f2ef224878fbd232f5

# Pythonでサウンドを扱う
# https://qiita.com/hisshi00/items/62c555095b8ff15f9dd2
# pip install simpleaudio

import numpy as np
import wave
import struct

fs = 44100

def create_wave(hz, rate, time, volume, square):
    # f0:基本周波数,fs:サンプリング周波数,再生時間[s]
    point = np.arange(0, rate * time)
    wave_value = - np.sin(2 * np.pi * hz * point / rate) * volume

    if square:
        # 正弦波を矩形波に変換
        for i in range(len(wave_value)):
            if wave_value[i] > 0:
                wave_value[i] = volume
            elif wave_value[i] < 0:
                wave_value[i] = -volume

    # 16bit符号付き整数に変換
    return [int(x * 32767) for x in wave_value]

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

def bits_to_wave(bits):
    wave_value = []
    w1 = create_wave(2005, fs, 1/2005, 0.1, True)
    w2 = create_wave(2005/2, fs, 2/2005, 0.1, True)
    for b in bits:
        if b:
            wave_value += w1
        else:
            wave_value += w2
    return struct.pack("h" * len(wave_value), *wave_value)
