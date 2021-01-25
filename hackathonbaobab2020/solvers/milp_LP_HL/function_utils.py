
import time

def no_duplicates(l):
    return list(set(l))

class Chrono:
    """
    Class to measure time
    """
    __slots__ = ('start', 'name', 'stop_time', 'finish_time')
    
    def __init__(self, operation_name, silent=True):
        """
        :param operation_name: The name of the measured operation.
        :param silent: if False, it will print "Starting operation_name" when the class is created.
        """
        self.start = time.time()
        self.name = operation_name
        self.stop_time = 0
        self.finish_time = 0
        if not silent:
            print("Starting %s" % self.name)
    
    def time(self, prec=1, silent=False):
        """
        Measure the time spent between start and current time.

        :param prec: The rounding precision.
        :param silent: if true, it will print the time spent since start.
        :return: The time spent since start in seconds.
        """
        dur = round(time.time() - self.start, prec)
        if not silent:
            print("Time passed since %s started: %s seconds" % (self.name, dur))
        return dur
    
    def stop(self, prec=1, silent=False):
        """
        Stop the chronometer.

        :param prec: The rounding precision.
        :param silent: if true, it will print the time spent since start.
        :return: The time spent since start.
        """
        self.stop_time = time.time()
        self.finish_time = round(self.stop_time - self.start, prec)
        if not silent:
            print("%s finished in %s seconds" % (self.name, self.finish_time))
        return self.finish_time
    
    def get_finish_time(self):
        """
        If the chronometer is stopped, return the total time.

        :return: the total time spent when stopped.
        """
        return self.finish_time