import re
s = 'c(qwdqw, dqwko())'
result = re.search('()', s)
print(result.group(1))