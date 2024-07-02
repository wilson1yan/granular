import io
from functools import partial as bind

import msgpack


def encode_int(value, size=None, endian='little'):
  import numpy as np
  if size is None:
    size = np.ceil(np.log2(1 + value) / 8)
  return value.to_bytes(int(size), endian)


def decode_int(buffer, size=None, endian='little'):
  return int.from_bytes(buffer, endian)


def encode_array(value):
  assert value.data.c_contiguous
  return msgpack.packb((value.dtype.str, value.shape, value.data))


def decode_array(buffer):
  import numpy as np
  dtype, shape, data = msgpack.unpackb(buffer)
  return np.frombuffer(data, dtype).reshape(shape)


def encode_tree(value):
  import numpy as np
  def fn(xs):
    if isinstance(xs, (list, tuple)):
      return [fn(x) for x in xs]
    elif isinstance(xs, dict):
      return {k: fn(v) for k, v in xs.items()}
    elif isinstance(xs, np.ndarray):
      assert xs.data.c_contiguous
      return ('_', xs.dtype.str, xs.shape, xs.data)
    else:
      return xs
  return msgpack.packb(fn(value))


def decode_tree(buffer):
  import numpy as np
  def fn(xs):
    if isinstance(xs, list) and len(xs) == 4 and xs[0] == '_':
      _, dtype, shape, data = xs
      return np.frombuffer(data, dtype).reshape(shape)
    elif isinstance(xs, (list, tuple)):
      return [fn(x) for x in xs]
    elif isinstance(xs, dict):
      return {k: fn(v) for k, v in xs.items()}
    else:
      return xs
  return fn(msgpack.unpackb(buffer))


def encode_image(value, quality=100, format='jpg'):
  format = ('jpeg' if format == 'jpg' else format).upper()
  from PIL import Image
  stream = io.BytesIO()
  Image.fromarray(value).save(stream, format=format)
  return stream.getvalue()


def decode_image(buffer, *args):
  import numpy as np
  from PIL import Image
  return np.asarray(Image.open(io.BytesIO(buffer)))


def encode_video(array, fps=20, format='mp4', codec='h264'):
  import av
  T, H, W = array.shape[:3]
  fp = io.BytesIO()
  output = av.open(fp, mode='w', format=format)
  stream = output.add_stream(codec, rate=float(fps))
  stream.width = W
  stream.height = H
  stream.pix_fmt = 'yuv420p'
  for t in range(T):
    frame = av.VideoFrame.from_ndarray(array[t], format='rgb24')
    frame.pts = t
    output.mux(stream.encode(frame))
  output.mux(stream.encode(None))
  output.close()
  return fp.getvalue()


def decode_video(buffer, *args):
  import numpy as np
  import av
  container = av.open(io.BytesIO(buffer))
  array = []
  for frame in container.decode(video=0):
    array.append(frame.to_ndarray(format='rgb24'))
  array = np.stack(array)
  container.close()
  return array


encoders = {
    'bytes': lambda x: x,
    'utf8': lambda x: x.encode('utf-8'),
    'msgpack': msgpack.packb,
    'int': encode_int,
    'array': encode_array,
    'tree': encode_tree,
    'jpg': bind(encode_image, format='jpg'),
    'png': bind(encode_image, format='png'),
    'mp4': bind(encode_video, format='mp4', codec='h264'),
    'webm': bind(encode_video, format='webm', codec='vp9'),
}


decoders = {
    'bytes': lambda x: x,
    'utf8': lambda x: x.decode('utf-8'),
    'msgpack': msgpack.unpackb,
    'int': decode_int,
    'array': decode_array,
    'tree': decode_tree,
    'jpg': decode_image,
    'png': decode_image,
    'mp4': decode_video,
    'webm': decode_video,
}
