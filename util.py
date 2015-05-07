import functools

def memoize(f):
    memo = {}
    @functools.wraps(f)
    def helper(*args):
        if args not in memo:
            memo[args] = f(*args)
        return memo[args]
    return helper
