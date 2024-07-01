[![PyPI](https://img.shields.io/pypi/v/granular.svg)](https://pypi.python.org/pypi/granular/#history)

# Granular: Fast format for datasets

Granular is a library for reading and writing multimodal datasets. Each dataset
is a collection of linked files of the [bag file format][bag], a simple
seekable container structure.

[bag]: ...

## Features

- 🚀 **Performance:** Minimal overhead for maximum read and write throughput.
- 🔎 **Seekable:** Fast random access from disk by datapoint index.
- 🎞️ **Sequences:** Datapoints can contain seekable ranges of modalities.
- 🤸 **Flexible:** User provides encoders and decoders; examples available.
- 👥 **Sharding:** Store datasets into shards to split processing workloads.

## Installation

Granular is [a single file][file], so you can just copy it to your project
directory. Or you can install the package:

```
pip install granular
```

[file]: https://github.com/danijar/granular/blob/main/granular/granular.py

## Quickstart

Writing

```python3
import granular
import msgpack
import numpy as np

spec = {
    'foo': 'int',      # integer
    'bar': 'utf8[]',   # list of strings
    'baz': 'msgpack',  # packed structure
}

encoders = {
    'foo': lambda x: x.to_bytes(8, 'little'),
    'bar': lambda x: x.encode('utf-8'),
    'baz': msgpack.packb,
}

with granular.ShardedDatasetWriter(
    directory, spec, encoders, shardlen=1000) as writer:
  writer.append({'foo': 42, 'bar': ['hello', 'world'], 'baz': {'a': 1})
  # ...
```

Files

```sh
$ tree directory
.
├── 000000
│  ├── spec.json
│  ├── refs.bag
│  ├── foo.bag
│  ├── bar.bag
│  └── baz.bag
├── 000001
│  ├── spec.json
│  ├── refs.bag
│  ├── foo.bag
│  ├── bar.bag
│  └── baz.bag
└── ...
```

Reading

```python
decoders = {
    'foo': lambda x: int.from_bytes(x),
    'bar': lambda x: x.decode('utf-8'),
    'baz': msgpack.unpackb,
}

with granular.ShardedDatasetReader(directory, decoders) as reader:
  print(len(reader))    # Number of datapoints in the dataset.
  print(reader.size)    # Dataset size in bytes.
  print(reader.shards)  # Number of shards.

  # Read data points by index. This will read only the relevant bytes from
  # disk. An additional small read is used when caching index tables is
  # disabled, supporting arbitrarily large datasets with minimal overhead.
  assert reader[0] == {'foo': 42, 'bar': ['hello', 'world'], 'baz': {'a': 1}

  # Read a subset of keys of a datapoint. For example, this allows quickly
  # iterating over the metadata fields of all datapoints without accessing
  # expensive image or video modalities.
  assert reader[0, {'foo': True, 'baz': True}] == {'foo': 42, 'baz': {'a': 1}}

  # Read only a slice of the 'bar' list. Only the requested slice will be
  # fetched from disk. For example, the could be used to load a subsequence of
  # a long video that is stored as list of consecutive MP4 clips.
  assert reader[0, {'bar': range(1, 2)}] == {'bar': ['world']}
```

For small datasets where sharding is not necessary, you can also use
`DatasetReader` and `DatasetWriter`.

For distributed processing using multiple processes or machines, use
`ShardedDatasetReader` and `ShardedDatasetWriter` and set `shardstart` to the
worker index and `shardstop` to the total number of workers.

## Formats

Granular does not impose a serialization solution on the user. Any words can be
used as types, as long as encoder and decoder functions are provided.

Examples of common encode and decode functions are provided in
[formats.py][formats]. These support Numpy arrays, JPG and PNG images, MP4
videos, and more.

You can also use the provided functions for all keys like this:

```python
spec = {'foo': 'int', 'bar': 'utf8[]', 'baz': 'msgpack'}
encoders = {k: granular.encoders[v.strip('[]')] for k, v in spec.items()}
decoders = {k: granular.decoders[v.strip('[]')] for k, v in spec.items()}
```

[formats]: https://github.com/danijar/granular/blob/main/granular/formats.py

## Questions

If you have a question, please [file an issue][issues].

[issues]: https://github.com/danijar/granular/issues

