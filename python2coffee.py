#!/usr/bin/python3
import re
import parso, parso.python.tree

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

level = -1
def recurse(node):
  global level
  level += 1
  if hasattr(node, 'children'):
    print('  ' * level + node.type, '[%d]' % len(node.children))
  elif hasattr(node, 'value'):
    print('  ' * level + node.type, repr(node.value))
  else:
    print('  ' * level + node.type)
  s = ''
  if isinstance(node, parso.python.tree.Leaf):
    s += node.prefix
  if node.type in ['name', 'number', 'string', 'operator', 'endmarker', 'newline']:
    s += node.value
  elif hasattr(node, 'children'):
    if node.type == 'power':
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
    s += ''.join(map(recurse, node.children))
  else:
    s += str(node)
  level -= 1
  return s

#tree = parso.parse(open('Bibtex.py', 'r').read(), version='2.7')
tree = parso.parse('''\
'# Hello {}, your age is {}'.format(name, age)
''', version='2.7')

print(recurse(tree))
