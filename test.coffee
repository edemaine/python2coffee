# Python 2.7 code: run with python2coffee.py -p 2 test.py
'###'
"\#\#\#"
"\# Hello #{name}, your age is #{age}"
x = x.toString() unless x instanceof str
### This is a comment ###
for item in [0...17] # up to 16
  console.assert 0 <= item < 17
  console.log if item % 2 == 1 then item else item/2
for item in [2...17]
  console.log item.toString(), '->', (item + 1).toString(16)
parseInt('123').toString() == '123'
parseInt(123.toString()) == 123
String.fromCharCode(27).charCodeAt() == 27
String.fromCharCode('A'.charCodeAt()) == 'A'
a = [0...17]
b = [2...17]
c = (_i for _i in [2...17] by 3)
L = []
for item in [2...17] by 3
  L.push(() -> item)
  L.push((item=item) -> item)
max(L) == max(...L)
[item ** 2 for item in [2...17] by 3]
mysum = (initial, ...args) ->
  _this = initial
  for arg in args
    _this += arg
  return _this
loop
  item = f()
  if item
    console.log item
  else if forever
    continue
  else
    break
  break unless done
break until done
class Point
  constructor: (x, y) ->
    @x = x
    @y = y
  translate: (dx, dy) ->
    @x += dx
    @y += dy
  toString: () ->
    _this = @
    return "(#{@x}, #{@y})"
class Accumulator
  constructor: () ->
    @value = 0
  adder: () ->
    add = (x) =>
      @value += x
    return add
