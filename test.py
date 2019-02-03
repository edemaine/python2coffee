# Python 2.7 code: run with python2coffee.py -p 2 test.py
'###'
"###"
'# Hello {}, your age is {}'.format(name, age)
if not isinstance(x, str): x = str(x)
### This is a comment
for item in range(17): # up to 16
  assert 0 <= item < 17
  print item if item % 2 == 1 else item/2
for item in range(2, 17):
  print str(item), '->', hex(item + 1)
str(int('123')) == '123'
int(str(123)) == 123
ord(chr(27)) == 27
chr(ord('A')) == 'A'
a = range(17)
b = range(2, 17)
c = range(2, 17, 3)
L = []
for item in range(2, 17, 3):
  L.append (lambda: item)
  L.append (lambda item=item: item)
  L.extend ([item, item+1])
L.extend (L)
L.extend ([x**2 for x in L])
max(L) == max(*L)
[item ** 2 for item in range(2, 17, 3)]
def mysum(initial, *args):
  this = initial
  for arg in args:
    this += arg
  return this
def oneline(x): x += 5; return x
def oneline2(x): x += 5
def twoline(x):
  x += 5; return x
def twoline2(x):
  x += 5
def defaults(x = 5, y = None): pass
while True:
  item = f()
  if item:
    print item
  elif forever:
    continue
  else:
    break
  if not done: break
while not done: break
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
  def getter(self):
    return lambda: self.value
  get = lambda self: self.value
