# -*- coding: utf-8 -*-
"""项目三 · MP3 解码（借 Electron 自带的 ffmpeg.dll 的 avcodec 接口）

背景：本机装不了 ffmpeg 命令行，但 DSH/Electron 自带 `D:\\deepseek\\ffmpeg.dll`，
它导出了 avcodec_find_decoder / avcodec_send_packet / avcodec_receive_frame 等。
所以用 ctypes 直接调 libavcodec 解 MP3，不依赖任何外部工具。

只做两件事：MP3 → float32 单/双声道 PCM。
帧切分自己写（不依赖 av_parser），进制表全在下面。
"""
import ctypes
import os
import struct

DLL_CANDIDATES = [
    r"D:\deepseek\ffmpeg.dll",
    r"D:\deepseek\resources\ffmpeg.dll",
]

AV_CODEC_ID_MP3 = 86017

# MPEG1 Layer3 比特率表（kbps），索引 0 为 free，15 非法
BR_V1L3 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
# MPEG2/2.5 Layer3
BR_V2L3 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
SR_V1 = [44100, 48000, 32000, 0]
SR_V2 = [22050, 24000, 16000, 0]
SR_V25 = [11025, 12000, 8000, 0]


class _Pkt(ctypes.Structure):
    """只声明前 5 个字段，偏移与 FFmpeg 3.x–6.x 的 AVPacket 一致。"""
    _fields_ = [("buf", ctypes.c_void_p),
                ("pts", ctypes.c_int64),
                ("dts", ctypes.c_int64),
                ("data", ctypes.POINTER(ctypes.c_uint8)),
                ("size", ctypes.c_int)]


def _load():
    for p in DLL_CANDIDATES:
        if os.path.exists(p):
            return ctypes.CDLL(p), p
    raise FileNotFoundError("找不到 ffmpeg.dll")


class _Api(object):
    def __init__(self):
        d, self.path = _load()
        self.d = d
        P = ctypes.POINTER
        d.avcodec_find_decoder.restype = ctypes.c_void_p
        d.avcodec_find_decoder.argtypes = [ctypes.c_int]
        d.avcodec_alloc_context3.restype = ctypes.c_void_p
        d.avcodec_alloc_context3.argtypes = [ctypes.c_void_p]
        d.avcodec_open2.restype = ctypes.c_int
        d.avcodec_open2.argtypes = [ctypes.c_void_p, ctypes.c_void_p, P(ctypes.c_void_p)]
        d.avcodec_send_packet.restype = ctypes.c_int
        d.avcodec_send_packet.argtypes = [ctypes.c_void_p, P(_Pkt)]
        d.avcodec_receive_frame.restype = ctypes.c_int
        d.avcodec_receive_frame.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        d.av_packet_alloc.restype = P(_Pkt)
        d.av_new_packet.restype = ctypes.c_int
        d.av_new_packet.argtypes = [P(_Pkt), ctypes.c_int]
        d.av_packet_unref.argtypes = [P(_Pkt)]
        d.av_packet_free.argtypes = [P(P(_Pkt))]
        d.av_frame_alloc.restype = ctypes.c_void_p
        d.av_frame_unref.argtypes = [ctypes.c_void_p]
        d.av_frame_free.argtypes = [P(ctypes.c_void_p)]
        d.avcodec_free_context.argtypes = [P(ctypes.c_void_p)]
        try:
            d.av_log_set_level(ctypes.c_int(-8))
        except Exception:
            pass

    def open(self):
        dec = self.d.avcodec_find_decoder(AV_CODEC_ID_MP3)
        if not dec:
            raise RuntimeError("这个 ffmpeg.dll 没有 MP3 解码器")
        ctx = self.d.avcodec_alloc_context3(dec)
        if not ctx:
            raise RuntimeError("avcodec_alloc_context3 失败")
        r = self.d.avcodec_open2(ctx, dec, None)
        if r < 0:
            raise RuntimeError("avcodec_open2 失败：%d" % r)
        return ctx


_API = None


def _api():
    global _API
    if _API is None:
        _API = _Api()
    return _API


# ---------------------------------------------------------------- 帧切分
def split_frames(raw):
    """把裸 MP3 字节流切成一个个完整帧。返回 [(offset, length, sr, ch)]。"""
    out = []
    i, n = 0, len(raw)
    while i + 4 <= n:
        if raw[i] != 0xFF or (raw[i + 1] & 0xE0) != 0xE0:
            i += 1
            continue
        h = raw[i:i + 4]
        ver = (h[1] >> 3) & 0x3       # 3=MPEG1, 2=MPEG2, 0=MPEG2.5
        layer = (h[1] >> 1) & 0x3     # 1=Layer3
        br_i = (h[2] >> 4) & 0xF
        sr_i = (h[2] >> 2) & 0x3
        pad = (h[2] >> 1) & 0x1
        mode = (h[3] >> 6) & 0x3      # 3=单声道

        if layer != 1 or br_i == 0 or br_i == 15 or sr_i == 3:
            i += 1
            continue
        if ver == 3:
            br, sr = BR_V1L3[br_i] * 1000, SR_V1[sr_i]
            flen = 144 * br // sr + pad
        else:
            tab = SR_V2 if ver == 2 else SR_V25
            br, sr = BR_V2L3[br_i] * 1000, tab[sr_i]
            flen = 72 * br // sr + pad
        if flen <= 4 or i + flen > n:
            i += 1
            continue
        out.append((i, flen, sr, 1 if mode == 3 else 2))
        i += flen
    return out


# ---------------------------------------------------------------- 解码
def decode_mp3(path):
    """返回 (samples float32 [n, ch], sample_rate)。"""
    import numpy as np
    raw = open(path, "rb").read()
    frames = split_frames(raw)
    if not frames:
        raise RuntimeError("没切出任何 MP3 帧，可能不是 MPEG Layer3")

    sr = frames[0][2]
    nch = frames[0][3]

    api = _api()
    ctx = api.open()
    pkt = api.d.av_packet_alloc()
    fr = api.d.av_frame_alloc()
    try:
        chunks = []
        for off, ln, _, _ in frames:
            pkt.contents.size = 0
            rc = api.d.av_new_packet(pkt, ln)
            if rc < 0:
                break
            ctypes.memmove(pkt.contents.data, raw[off:off + ln], ln)
            api.d.avcodec_send_packet(ctx, pkt)
            api.d.av_packet_unref(pkt)
            while True:
                r = api.d.avcodec_receive_frame(ctx, fr)
                if r != 0:
                    break
                iv = ctypes.cast(fr, ctypes.POINTER(ctypes.c_int))
                nbs, fmt = int(iv[28]), int(iv[29])   # nb_samples@112, format@116
                planes = ctypes.cast(fr, ctypes.POINTER(ctypes.c_void_p))
                if not planes[0]:
                    api.d.av_frame_unref(fr)
                    continue
                def read_plane(p, fmt, n):
                    if fmt in (6, 7):        # S16P / S32P
                        a = np.ctypeslib.as_array(
                            ctypes.cast(p, ctypes.POINTER(ctypes.c_int16)), shape=(n,))
                        return a.astype(np.float64) / 32768.0
                    a = np.ctypeslib.as_array(
                        ctypes.cast(p, ctypes.POINTER(ctypes.c_float)), shape=(n,))
                    return a.astype(np.float64)

                n = nbs if nbs > 0 else 1152
                L = read_plane(planes[0], fmt, n)
                if nch == 2 and planes[1]:
                    R = read_plane(planes[1], fmt, n)
                    chunks.append(np.stack([L, R], axis=1))
                else:
                    chunks.append(L.reshape(-1, 1))
                api.d.av_frame_unref(fr)
        if not chunks:
            raise RuntimeError("解码没产出任何帧")
        return np.concatenate(chunks, axis=0), sr
    finally:
        api.d.av_frame_free(ctypes.byref(ctypes.c_void_p(fr)))
        api.d.av_packet_free(ctypes.byref(pkt))
        api.d.avcodec_free_context(ctypes.byref(ctypes.c_void_p(ctx)))


def mp3_to_wav(src, dst, gain=1.0):
    """MP3 → 16 bit WAV（多声道自动混成单声道）。"""
    import numpy as np
    x, sr = decode_mp3(src)
    mono = x.mean(axis=1) * float(gain)
    peak = float(np.max(np.abs(mono))) if len(mono) else 0.0
    if peak > 0.999:
        mono = mono / peak * 0.99
    import audio as A
    A.write_wav(dst, mono, sr)
    return sr, len(mono) / float(sr)


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else r"D:\Temp\Cache\oPlusConnect\TempFiles\标准录音 1.mp3"
    x, sr = decode_mp3(p)
    print("解码成功")
    print("  采样率：%d Hz" % sr)
    print("  声道  ：%d" % x.shape[1])
    print("  时长  ：%.2f s" % (x.shape[0] / float(sr)))
    print("  峰值  ：%.4f" % float(abs(x).max()))
