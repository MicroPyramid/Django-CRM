"""
This file is originally based on code from https://github.com/nylas/nylas-perftools, which is published under the following license:

The MIT License (MIT)

Copyright (c) 2014 Nylas

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import atexit
import signal
import time
from contextlib import contextmanager

import sentry_sdk
from sentry_sdk._compat import PY2
from sentry_sdk.utils import logger

if PY2:
    import thread  # noqa
else:
    import threading

from sentry_sdk._types import MYPY

if MYPY:
    import typing
    from typing import Generator
    from typing import Optional
    import sentry_sdk.tracing


if PY2:

    def thread_id():
        # type: () -> int
        return thread.get_ident()

    def nanosecond_time():
        # type: () -> int
        return int(time.clock() * 1e9)

else:

    def thread_id():
        # type: () -> int
        return threading.get_ident()

    def nanosecond_time():
        # type: () -> int
        return int(time.perf_counter() * 1e9)


class FrameData:
    def __init__(self, frame):
        # type: (typing.Any) -> None
        self.function_name = frame.f_code.co_name
        self.module = frame.f_globals["__name__"]

        # Depending on Python version, frame.f_code.co_filename either stores just the file name or the entire absolute path.
        self.file_name = frame.f_code.co_filename
        self.line_number = frame.f_code.co_firstlineno

    @property
    def _attribute_tuple(self):
        # type: () -> typing.Tuple[str, str, str, int]
        """Returns a tuple of the attributes used in comparison"""
        return (self.function_name, self.module, self.file_name, self.line_number)

    def __eq__(self, other):
        # type: (typing.Any) -> bool
        if isinstance(other, FrameData):
            return self._attribute_tuple == other._attribute_tuple
        return False

    def __hash__(self):
        # type: () -> int
        return hash(self._attribute_tuple)


class StackSample:
    def __init__(self, top_frame, profiler_start_time, frame_indices):
        # type: (typing.Any, int, typing.Dict[FrameData, int]) -> None
        self.sample_time = nanosecond_time() - profiler_start_time
        self.stack = []  # type: typing.List[int]
        self._add_all_frames(top_frame, frame_indices)

    def _add_all_frames(self, top_frame, frame_indices):
        # type: (typing.Any, typing.Dict[FrameData, int]) -> None
        frame = top_frame
        while frame is not None:
            frame_data = FrameData(frame)
            if frame_data not in frame_indices:
                frame_indices[frame_data] = len(frame_indices)
            self.stack.append(frame_indices[frame_data])
            frame = frame.f_back
        self.stack = list(reversed(self.stack))


class Sampler(object):
    """
    A simple stack sampler for low-overhead CPU profiling: samples the call
    stack every `interval` seconds and keeps track of counts by frame. Because
    this uses signals, it only works on the main thread.
    """

    def __init__(self, transaction, interval=0.01):
        # type: (sentry_sdk.tracing.Transaction, float) -> None
        self.interval = interval
        self.stack_samples = []  # type: typing.List[StackSample]
        self._frame_indices = dict()  # type: typing.Dict[FrameData, int]
        self._transaction = transaction
        self.duration = 0  # This value will only be correct after the profiler has been started and stopped
        transaction._profile = self

    def __enter__(self):
        # type: () -> None
        self.start()

    def __exit__(self, *_):
        # type: (*typing.List[typing.Any]) -> None
        self.stop()

    def start(self):
        # type: () -> None
        self._start_time = nanosecond_time()
        self.stack_samples = []
        self._frame_indices = dict()
        try:
            signal.signal(signal.SIGVTALRM, self._sample)
        except ValueError:
            logger.error(
                "Profiler failed to run because it was started from a non-main thread"
            )
            return

        signal.setitimer(signal.ITIMER_VIRTUAL, self.interval)
        atexit.register(self.stop)

    def _sample(self, _, frame):
        # type: (typing.Any, typing.Any) -> None
        self.stack_samples.append(
            StackSample(frame, self._start_time, self._frame_indices)
        )
        signal.setitimer(signal.ITIMER_VIRTUAL, self.interval)

    def to_json(self):
        # type: () -> typing.Any
        """
        Exports this object to a JSON format compatible with Sentry's profiling visualizer.
        Returns dictionary which can be serialized to JSON.
        """
        return {
            "samples": [
                {
                    "frames": sample.stack,
                    "relative_timestamp_ns": sample.sample_time,
                    "thread_id": thread_id(),
                }
                for sample in self.stack_samples
            ],
            "frames": [
                {
                    "name": frame.function_name,
                    "file": frame.file_name,
                    "line": frame.line_number,
                }
                for frame in self.frame_list()
            ],
        }

    def frame_list(self):
        # type: () -> typing.List[FrameData]
        # Build frame array from the frame indices
        frames = [None] * len(self._frame_indices)  # type: typing.List[typing.Any]
        for frame, index in self._frame_indices.items():
            frames[index] = frame
        return frames

    def stop(self):
        # type: () -> None
        self.duration = nanosecond_time() - self._start_time
        signal.setitimer(signal.ITIMER_VIRTUAL, 0)

    @property
    def transaction_name(self):
        # type: () -> str
        return self._transaction.name


def has_profiling_enabled(hub=None):
    # type: (Optional[sentry_sdk.Hub]) -> bool
    if hub is None:
        hub = sentry_sdk.Hub.current

    options = hub.client and hub.client.options
    return bool(options and options["_experiments"].get("enable_profiling"))


@contextmanager
def profiling(transaction, hub=None):
    # type: (sentry_sdk.tracing.Transaction, Optional[sentry_sdk.Hub]) -> Generator[None, None, None]
    if has_profiling_enabled(hub):
        with Sampler(transaction):
            yield
    else:
        yield
