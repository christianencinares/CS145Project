'Print a symmetric pyramid with base size n'
def pyramid(n):
    'Print a symmetric pyramid with base size n'
    for i in range(1, n + 1):
        print(' ' * (n - i) + '#' * (2 * i - 1))
pyramid(5)