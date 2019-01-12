#!/usr/bin/python3
import re, warnings
import parso, parso.python.tree

def is_node(node, type):
  return node.type == type
def is_leaf(node, type, value = None):
  return node.type == type and (value is None or node.value == value)
def is_operator(node, op = None):
  return is_leaf(node, 'operator', op)
def is_name(node, name = None):
  return is_leaf(node, 'name', name)
def is_string(node):
  return is_leaf(node, 'string')
def is_method_trailer(node, method = None):
  return node.type == 'trailer' and len(node.children) == 2 and \
    is_operator(node.children[0], '.') and \
    (method is None or is_name(node.children[1], method))

def is_call_trailer(node):
  return node.type == 'trailer' and \
    is_operator(node.children[0], '(') and \
    is_operator(node.children[-1], ')') and \
    len(node.children) == 3
def split_call_trailer(node):
  assert is_call_trailer(node)
  args = node.children[1]
  if args.type == 'arglist':
    commas = args.children[1::2]
    for comma in commas:
      assert is_operator(comma, ',')
    return args.children[0::2]
  else:
    return [args]

def prepare_string_for_interpolation(node):
  assert is_string(node)
  # not handling prefix like r'...'
  if node.value.startswith("'''"):
    assert node.value.endswith("'''")
    node.value = re.sub(r'"""', '"\\"\\"', node.value)
    node.value = '"""' + node.value[3:-3] + '"""'
  elif node.value.startswith("'"):
    assert node.value.endswith("'")
    node.value = re.sub(r'"', '\\"', node.value)
    node.value = '"' + node.value[1:-1] + '"'
  node.value = re.sub(r'#', '\#', node.value)

def terminate_comments(node):
  '''Fix ### (not shorter or longer) to not go beyond the line'''
  def sub(match):
    s = match.group(0)
    def end(endMatch):
      if len(endMatch.group(1)) == 0:
        return match.group(1) + '###' + endMatch.group(2)
      elif len(endMatch.group(1)) != 3:
        return '###' + endMatch.group(2)
      else:
        return endMatch.group(0)
    s = re.sub(r'(#*)(\s*)$', end, s)
    split = re.search(r'^(\s*###)(.*?)(###\s*)$', s)
    assert split is not None
    middle = split.group(2)
    middle = re.sub(r'(?<!#)###(?!#)', '####', middle)
    s = split.group(1) + middle + split.group(3)
    return s
  node.prefix = re.sub(r'^\s*###(?!#)(\s*).*$',
    sub, node.prefix, re.MULTILINE)

# https://docs.python.org/3/reference/expressions.html#operator-precedence
precedence = {
  'lambda': 0,
  'if': 1,
  'or': 2,
  'and': 3,
  'not': 4,
  'in': 5,
  'not in': 5,
  'is': 5,
  'not is': 5,
  '<': 5,
  '<=': 5,
  '>': 5,
  '>=': 5,
  '!=': 5,
  '==': 5,
  '|': 6,
  '^': 7,
  '&': 8,
  '<<': 9,
  '>>': 9,
  '+': 10,
  '-': 10,
  '*': 11,
  '/': 11,
  '//': 11,
  '%': 11,
  '@': 11,
  'u+': 12,
  'u-': 12,
  '~': 12,
  '**': 13,
  'await': 14,
  '[': 15,
  '.': 15,
  '(': 15,
  '{': 15,
  'leaf': 16,
}

def top_op(root):
  if isinstance(root, parso.python.tree.Leaf):
    return 'leaf'
  elif isinstance(root, parso.python.tree.BaseNode):
    frontier = root.children
  while frontier:
    rest = []
    for node in frontier:
      if isinstance(node, parso.python.tree.Leaf) and node.value in precedence:
        return node.value
      elif isinstance(node, parso.python.tree.BaseNode):
        rest.extend(node.children)
    frontier = rest
  warnings.warn('Could not determine top operator in %s' % node)
  return 'lambda'

def maybe_paren(node, op):
  s = recurse(node)
  node_op = top_op(node)
  if precedence[node_op] < precedence[op]:
    s = '(' + s + ')'
  return s

def dump_tree(node, level = 0):
  if hasattr(node, 'prefix'):
    prefix = 'prefix=' + repr(node.prefix)
  else:
    prefix = ''
  if hasattr(node, 'children'):
    print('  ' * level + node.type, '[%d]' % len(node.children), prefix)
  elif hasattr(node, 'value'):
    print('  ' * level + node.type, repr(node.value), prefix)
  else:
    print('  ' * level + node.type, prefix)
  if isinstance(node, parso.python.tree.BaseNode):
    for child in node.children:
      dump_tree(child, level+1)

class CoffeeScript(parso.python.tree.Leaf):
  type = 'coffee'
  def __init__(self, value, outermost, prefix=''):
    parso.python.tree.Leaf.__init__(self, value, (-1,-1), prefix)
                                               # start_pos meaningless
    self.outermost = outermost

def recurse(node):
  if isinstance(node, CoffeeScript):
    ## Code already compiled into CoffeeScript
    return node.value

  s = ''
  if isinstance(node, parso.python.tree.Leaf):
    if node.type == 'error_leaf':
      warnings.warn('ERROR LEAF DETECTED: %s' % node)
    terminate_comments(node)
    s += node.prefix

  if isinstance(node, parso.python.tree.BaseNode):
    if node.type == 'print_stmt':
      node.children[0] = node.children[0].prefix + 'console.log'
      if is_operator(node.children[-1], ','):
        warnings.warn('No known analog of print with comma to prevent newline')

    elif node.type == 'power':
      if len(node.children) >= 3 and \
         is_string(node.children[0]) and \
         is_method_trailer(node.children[1], 'format') and \
         is_call_trailer(node.children[2]):
        args = split_call_trailer(node.children[2])
        count = -1
        def arg(match):
          nonlocal count
          count += 1
          return '#{' + recurse(args[count]).lstrip() + '}'
        prepare_string_for_interpolation(node.children[0])
        node.children[0].value = re.sub(r'{}', arg, node.children[0].value)
        node.children[1:3] = []

      elif len(node.children) >= 2 and is_name(node.children[0]) and \
           is_call_trailer(node.children[1]):
        ## Function call, possibly built-in
        function = node.children[0].value
        args = split_call_trailer(node.children[1])
        r = None

        if function == 'range':
          prefix = node.children[0].prefix
          args = tuple(recurse(arg).lstrip() for arg in args)
          if len(args) == 1:
            r = CoffeeScript(prefix + '[0...%s]' % args[0], '[')
          elif len(args) == 2:
            r = CoffeeScript(prefix + '[%s...%s]' % args, '[')
          elif len(args) == 3:
            r = CoffeeScript(prefix + '(_i for _i in [%s...%s] by %s)' % args, '(')
          else:
            warnings.warn('range with %d args' % len(args))

        elif function in ['str', 'bin', 'oct', 'hex']:
          if function == 'str' and len(args) == 0: # str()
            r = "''"
          elif len(args) == 1: # str(x) or related
            if function == 'str':
              base = ''
            elif function == 'bin':
              base = 2
            elif function == 'oct':
              base = 8
            elif function == 'hex':
              base = 16
            r = CoffeeScript(node.children[0].prefix +
                  maybe_paren(args[0], '.') +
                  '.toString(%s)' % base, '.')
          else:
            warnings.warn('%s() with %d arguments' % (function, len(args)))

        if r is not None:
          node.children[:2] = [r]

    elif node.type in ['for_stmt', 'while_stmt']:
      assert is_node(node.children[-1], 'suite')
      assert is_operator(node.children[-2], ':')
      #node.children[-1].prefix = node.children[-2].prefix + node.children[-1].prefix
      node.children[-2:-1] = []

  #if node.type in ['name', 'number', 'string', 'operator', 'endmarker', 'newline']:
  if isinstance(node, parso.python.tree.Leaf):
    s += node.value
  elif isinstance(node, parso.python.tree.BaseNode):
    s += ''.join(map(recurse, node.children))
  else:
    s += str(node)
  return s

#tree = parso.parse(open('Bibtex.py', 'r').read(), version='2.7')
tree = parso.parse('''\
'# Hello {}, your age is {}'.format(name, age)
### This is a comment
for item in range(17): # up to 16
  print item
for item in range(2, 17):
  print str(item), 'eh?'
for item in range(2, 17, 3):
  print hex(item + 1)
while True:
  print item
''', version='2.7')

dump_tree(tree)
print('==> CoffeeScript:')
print(recurse(tree))
