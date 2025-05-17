import re

with open('MaDump.txt', 'r') as f_in, open('MaDumpCleaned.txt', 'w') as f_out:
    for line in f_in:
        line = re.sub(r'^\d+h\d+m\d+\.\d+s\s+LUA :\s+', '', line)
        f_out.write(line)

