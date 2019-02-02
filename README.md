# Automatic Python -> CoffeeScript conversion

This project is a rough experiment to see how easily/effectively we can
automatically convert Python code into equivalent CoffeeScript code,
inspired by the
[CoffeeScript for Python Programmers guide](https://edemaine.github.io/coffeescript-for-python/).
It's still very much a work-in-progress, is not feature complete,
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
