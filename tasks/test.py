from tasks import task


class Test(task.Task):
    def __init__(self, config):
        print('%s task initialized.' % self.__class__)

    def __call__(self):
        print('%s task called.' % self.__class__)

    def cleanup(self):
        print('%s task cleanup called.' % self.__class__)
        pass

    def stop(self):
        print('%s task stop check called.' % self.__class__)
        return True

    def status(self):
        return '%s status.' % self.__class__

    @classmethod
    def parameters(cls):
        print('%s parameters class method called.' % cls)
        return dict()

    @classmethod
    def validate(cls, config):
        print('%s validate class method called.' % cls)
        return config