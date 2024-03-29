class OperationStatusChecker:
    def __init__(self):
        self.running = True
        self.paused = False
        self.finished = False
    def reset(self):
        self.running = True
        self.paused = False
        self.finished = False
    def isRunning(self):
        if self.running:
            return True
        return False
    def isPaused(self):
        if self.paused and self.running:
            return True
        return False
    def isFinished(self):
        if self.finished:
            return True
        return False
    def shouldLocate(self):
        if self.running and (not self.paused):
            return True
        return False
    def start(self):
        self.running = True
        self.paused = False
    def stop(self):
        self.running = False
    def finish(self):
        print("Finishing OSC")
        self.running = False
        self.finished = True
    def pause(self):
        if self.paused:
            self.paused = False
            print("Resume")
        else:
            self.paused = True
            print("Paused")