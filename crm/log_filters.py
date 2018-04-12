from logging import Filter


class ManagementFilter(Filter):
    def filter(self, record):
        if (hasattr(record, 'funcName') and record.funcName ==  'execute'):
            return False
        else:
            return True
