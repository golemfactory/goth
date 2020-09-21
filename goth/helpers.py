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

    def __init__(self, stream):
        def output_queue(s, q):
            for line in iter(s.readline, b""):
                q.put(line)

        q: queue.Queue = queue.Queue()
        qt = threading.Thread(target=output_queue, args=[stream, q])
        qt.daemon = True
        qt.start()

        self._output_queue = q

    def lines(self) -> typing.List[bytes]:
        """Yield the lines of the output that have been captured so far."""
        while True:
            try:
                yield self._output_queue.get_nowait()
            except queue.Empty:
                break
