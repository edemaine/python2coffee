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
max(L) == max(*L)
def mysum(initial, *args):
  this = initial
  for arg in args:
    this += arg
  return this
while True:
  item = f()
  if item:
    print item
  elif forever:
    continue
  else:
    break
class Point:
  def __init__(self, x, y):
    self.x = x
    self.y = y
  def translate(self, dx, dy):
    self.x += dx
    self.y += dy
  def __str__(self):
    this = self
    return "({}, {})".format(self.x, self.y)
class Accumulator:
  def __init__(self):
    self.value = 0
  def adder(self):
    def add(x):
      self.value += x
    return add
