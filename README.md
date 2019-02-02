# Automatic Python &rarr; CoffeeScript (rough) conversion

This project is a rough experiment to see how easily/effectively we can
automatically convert Python code into equivalent CoffeeScript code,
inspired by the
[CoffeeScript for Python Programmers guide](https://edemaine.github.io/coffeescript-for-python/).
The goal is to preserve the existing code's indentation style, comments, etc.,
but it's still very much a work-in-progress, is not feature complete,
and may incorrectly convert some features, so please use with care.
Hopefully, if you have some Python code to convert to CoffeeScript,
this tool will provide a useful starting point, but you will almost certainly
still need to do some manual fixes.

## Usage

If your code is in Python 3, the following will convert `filename.py` to
`filename.coffee`:
```
python2coffee.py filename.py
```

If your code is in Python 2, use the following instead:
```
python2coffee.py -p 2 filename.py
```

## Features Supported So Far

* Python 2 or 3 input
* Built-ins
  * Escape `this` variable and CoffeeScript keyword `function`
  * `print` -> `console.log` (with warning about final comma in Python 2)
  * `assert` -> `console.assert`
  * `range` (1, 2, or 3 arguments)
  * `str`, `bin`, `oct`, `hex` -> `.toString`
  * `int`, `float` -> `parseInt`, `parseFloat`
  * `ord` -> `.charCodeAt`
  * `chr` -> `String.fromCharCode`
  * `isinstance` -> `instanceof`
  * `len` -> `.length`
* Blocks
  * `for...in`, `while`, `if...elif...else`
  * One-line versions of above
  * `if not` -> `unless`
  * `while not` -> `until`
  * `while True` -> `loop`
* Functions
  * `def` and `lambda`
  * `*args` -> `...args` in function definition and function call
  * Remove spaces between function and arguments in function call
* Booleans
  * `True` -> `true`
  * `False` -> `false`
* Strings
  * Replace `"...".format(...)` with CoffeeScript interpolation
  * Escape accidental interpolation (`"#"` )
  * `.startswith` -> `.startsWith`
  * `.endswith` -> `.endsWith`
  * `.find` -> `.indexOf`
  * `.rfind` -> `.lastIndexOf`
  * `.lower` -> `.toLowerCase`
  * `.upper` -> `.toUpperCase`
  * `.strip` -> `.trim`
  * `.lstrip` -> `.trimStart`
  * `.rstrip` -> `.trimEnd`
* Lists/arrays
  * `.append` -> `.push`
* Comments
  * Close accidental comment blocks (`###`)
* Classes
  * `class` blocks
  * Automatic stripping of first `self` argument from methods
  * `self.foo` -> `@foo`
  * `self` -> `@`
  * `__init__` -> `constructor`
  * `__str__` -> `toString`
  * `=>` for closures within methods, `->` for all other functions

## Related Work

This project is based on the excellent
[parso](https://parso.readthedocs.io/en/latest/) Python parser
(which must be [installed](https://parso.readthedocs.io/en/latest/docs/installation.html) first).

This is not the first attempt to automatically convert Python to CoffeeScript.

* [python-to-coffeescript](https://github.com/edreamleo/python-to-coffeescript)
  translates Python syntax to CoffeeScript **syntax**, but does not try to
  preserve semantics.
  It's based on a [mix of `ast` parsing and tokenization](https://github.com/edreamleo/python-to-coffeescript/blob/master/theory.md) to preserve comments etc.
* [Transcrypt](http://www.transcrypt.org/) converts Python to **JavaScript**.
* [pyscript](https://github.com/avinoamr/pyscript/) may also convert Python to **JavaScript**.
