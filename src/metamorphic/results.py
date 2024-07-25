class Result:

    def __init__(self):
        self.results_dict = dict()

    def add(self, name, results):
        self.results_dict[name] = results

    def __str__(self):
        result = 'Statistics:'
        for rule in self.results_dict:
            total = sum(len(files) for files in self.results_dict[rule].values())
            sat = len(self.results_dict[rule]['pass'])
            fail = len(self.results_dict[rule]['fail'])
            fail_rate = 100.0*fail/(sat+fail)
            result += f'\n - rule {rule}: {total} checks, fail {fail} times, satisfied {sat} times. Fail rate = {fail_rate}'
        return result

    
    