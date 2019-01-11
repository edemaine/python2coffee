#!/usr/bin/python3
import re
import parso, parso.python.tree

#tree = parso.parse(open('Bibtex.py', 'r').read(), version='2.7')
tree = parso.parse('y = """Hello {}""".format(x, y(5), key=z-w)', version='2.7')

def is_leaf(node, type, value = None):
  return node.type == type and (value is None or node.value == value)
def is_operator(node, op = None):
  return is_leaf(node, 'operator', op)
def is_name(node, op = None):
  return is_leaf(node, 'name', op)
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

level = 0
def recurse(tree):
  global level
  level += 1
  if hasattr(tree, 'children'):
    print('  ' * level + tree.type, '[%d]' % len(tree.children))
  elif hasattr(tree, 'value'):
    print('  ' * level + tree.type, repr(tree.value))
  else:
    print('  ' * level + tree.type)
  s = ''
  if isinstance(tree, parso.python.tree.Leaf):
    s += tree.prefix
  if tree.type in ['name', 'number', 'string', 'operator', 'endmarker']:
    s += tree.value
  elif hasattr(tree, 'children'):
    if tree.type == 'power':
      if len(tree.children) >= 3 and \
         is_string(tree.children[0]) and \
         is_method_trailer(tree.children[1], 'format') and \
         is_call_trailer(tree.children[2]):
        args = split_call_trailer(tree.children[2])
        count = -1
        def arg(match):
          nonlocal count
          count += 1
          return '#{' + recurse(args[count]) + '}'
        tree.children[0].value = re.sub(r'{}', arg, tree.children[0].value)
        tree.children[1:3] = []
    s += ''.join(map(recurse, tree.children))
  else:
    s += str(tree)
  level -= 1
  return s

print(recurse(tree))
