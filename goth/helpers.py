"""helper classes and functions used by the test harness."""
import queue
import threading
import typing


class IOStreamQueue:
    """
    Maintains a queue for an output stream - e.g. a launched process' stdout.

    example:
    ```
    p = subprocess.Popen(args=['cmd'], stdout=subprocess.PIPE)
    out_queue = helpers.IOStreamQueue(p.stdout)

    while True:
        for l in out_queue.lines():
            print(l.decode('utf-8'), end='')

        if p.poll() is not None:
            break

        time.sleep(0.1)

    ```
    """

    _output_queue: queue.Queue

    def __init__(self, stream: typing.IO[bytes]):
        def output_queue(s, q):
            for line in iter(s.readline, b""):
                q.put(line)

        self._output_queue = queue.Queue()
        qt = threading.Thread(target=output_queue, args=[stream, self._output_queue])
        qt.daemon = True
        qt.start()

    def lines(self) -> typing.Iterator[bytes]:
        """Yield the lines of the output that have been captured so far."""
        while True:
            try:
                yield self._output_queue.get_nowait()
            except queue.Empty:
                break
