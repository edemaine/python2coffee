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

level = -1
def recurse(node):
  global level
  level += 1
  if isinstance(node, str):
    ## Code already compiled into CoffeeScript
    return node
  if hasattr(node, 'children'):
    print('  ' * level + node.type, '[%d]' % len(node.children))
  elif hasattr(node, 'value'):
    print('  ' * level + node.type, repr(node.value))
  else:
    print('  ' * level + node.type)

  s = ''
  if isinstance(node, parso.python.tree.Leaf):
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
      elif len(node.children) >= 2 and \
         is_name(node.children[0], 'range') and \
         is_call_trailer(node.children[1]):
        args = split_call_trailer(node.children[1])
        r = node.children[0].prefix
        args = tuple(recurse(arg).lstrip() for arg in args)
        if len(args) == 1:
          r += '[0...%s]' % args[0]
        elif len(args) == 2:
          r += '[%s...%s]' % args
        elif len(args) == 3:
          r += '(_i for _i in [%s...%s] by %s)' % args
        else:
          warnings.warn('range with %d args' % len(args))
          r = None
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

  level -= 1
  return s

#tree = parso.parse(open('Bibtex.py', 'r').read(), version='2.7')
tree = parso.parse('''\
'# Hello {}, your age is {}'.format(name, age)
### This is a comment
for item in range(17):
  print item
for item in range(2, 17):
  print item, 'eh?'
for item in range(2, 17, 3):
  print item
while True:
  print item
''', version='2.7')

print(recurse(tree))
