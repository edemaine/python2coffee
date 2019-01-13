# Python 2.7 code
'###'
"###"
'# Hello {}, your age is {}'.format(name, age)
### This is a comment
for item in range(17): # up to 16
  print item if item % 2 == 1 else item/2
for item in range(2, 17):
  print str(item), '->', hex(item + 1)
L = []
for item in range(2, 17, 3):
  L.append (lambda: item)
  L.append (lambda item=item: item)
while True:
  item = f()
  if item:
    print item
  elif forever:
    continue
  else:
    break
