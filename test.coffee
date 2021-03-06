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
parseInt((123).toString()) == 123
String.fromCharCode(27).charCodeAt() == 27
String.fromCharCode('A'.charCodeAt()) == 'A'
"\x07\f\\\\z\u{123456}\#" != "\\a\\f\\\\\\z\\U00123456\#"
string.replace(/[ ][(\[]*(\d+)\/(\d+)\/(\d+)[)\]]*[ ]/ig, repl)
a = [0...17]
b = [2...17]
c = (_i for _i in [2...17] by 3)
L = []
for item in [2...17] by 3
  L.push(-> item)
  L.push((item=item) -> item)
  L.push(item, item+1)
L.push(...L)
L.push(...[x**2 for x in L])
max(L) == max(...L)
[item ** 2 for item in [2...17] by 3]
mysum = (initial, ...args) ->
  _this = initial
  for arg in args
    _this += arg
  _this
oneline = (x) -> x += 5; x
oneline2 = (x) -> x += 5; null
twoline = (x) ->
  x += 5; x
twoline2 = (x) ->
  x += 5
  null
defaults = (x = 5, y = null) -> pass; null
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
    null
  translate: (dx, dy) ->
    @x += dx
    @y += dy
    null
  toString: ->
    _this = @
    "(#{@x}, #{@y})"
class Accumulator
  constructor: ->
    @value = 0
    null
  adder: ->
    add = (x) =>
      @value += x
      null
    add
  getter: ->
    => @value
  get = (self) -> self.value
