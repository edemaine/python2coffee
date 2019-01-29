# Automatic Python -> CoffeeScript conversion

This project is an experiment to see how easily we can automatically convert
Python code into equivalent CoffeeScript code, inspired by the
[CoffeeScript for Python Programmers document](https://edemaine.github.io/coffeescript-for-python/).

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
