from collections import deque
import threading
import time

class Empty(Exception):
    'Exception raised by MyQueue.get(block=0)/get_nowait().'
    pass
class MyQueue:

    def __init__(self):
        self.queue = deque()
        self.cursor = 0
        self.mutex = threading.Lock()
        # Notify not_empty whenever an item is added to the queue; a
        # thread waiting to get is notified then.
        self.not_empty = threading.Condition(self.mutex)

        # NOTE: we assume the queue would not be full in our case

    def put(self, item):
        self.queue.append(item)
        try:
            with self.not_empty:
                self.not_empty.notify()
        except RuntimeError:
            pass


    def get(self, timeout: float = None, block: bool = True):

        """
        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until an item is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return an item if one is immediately
        available, else raise the Empty exception ('timeout' is ignored
        in that case).

        for now, we block until an item is available or timeout
        """
        with self.not_empty:
            endtime = time.time() + timeout
            while self.cursor == len(self.queue):
                remaining = endtime - time.time()
                if remaining <= 0.0:
                    # raise Empty
                    # TODO: raise Empty with timeout
                    return None
                self.not_empty.wait(remaining)
            item = self.queue[self.cursor]
            self.cursor += 1
            return item
        
    def reset(self):
        with self.mutex:
            self.cursor = 0

    def clear(self):
        with self.mutex:
            self.queue.clear()
            self.cursor = 0


    # return the cursor reached the end
    @property
    def is_tail(self):
        with self.mutex:
            return self.cursor == len(self.queue)
        
    @property
    def is_empty(self):
        """
        Check if the queue was empty.

        Returns:
            bool: True if the queue is empty, False otherwise.
        """
        with self.mutex:
            return len(self.queue) == 0

    def _qsize(self):
        return len(self.queue)
