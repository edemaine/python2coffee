#!/usr/bin/python3
import argparse, os, re, warnings
import parso, parso.python.tree

def is_node(node, type):
  return node.type == type
def is_leaf(node, type, value = None):
  return node.type == type and (value is None or node.value == value or
    (hasattr(value, 'search') and value.search(node.value)))
def is_newline(node):
  return is_leaf(node, 'newline')
def is_operator(node, op = None):
  return is_leaf(node, 'operator', op)
def is_keyword(node, op = None):
  return is_leaf(node, 'keyword', op)
def is_name(node, name = None):
  return is_leaf(node, 'name', name)
def is_string(node):
  return is_leaf(node, 'string')
def is_block(node):
  return is_node(node, 'suite') or is_node(node, 'simple_stmt')
## True and False are keywords in Python 3, names in Python 2
def is_true(node):
  return node.type in ['keyword', 'name'] and node.value == 'True'
def is_false(node):
  return node.type in ['keyword', 'name'] and node.value == 'False'
def is_method_trailer(node, method = None):
  return node.type == 'trailer' and len(node.children) == 2 and \
    is_operator(node.children[0], '.') and \
    is_name(node.children[1], method)

def set_children_parents(node):
  for child in node.children:
    child.parent = node

def is_call_trailer(node):
  return node.type == 'trailer' and \
    is_operator(node.children[0], '(') and \
    is_operator(node.children[-1], ')') and \
    len(node.children) == 3
def split_call_trailer(node):
  assert is_call_trailer(node)
  args = node.children[1]
  if args.type == 'arglist':
    groups = [[]]
    for arg in args.children:
      if is_operator(arg, ','):
        groups.append([])
      else:
        groups[-1].append(arg)
    if not groups[-1]:
      groups.pop()
    return groups
  else:
    return [node.children[1:-1]]
def force_call_trailer_arglist(node):
  assert is_call_trailer(node)
  if node.children[1].type != 'arglist':
    node.children[1:-1] = \
      [parso.python.tree.Node('arglist', node.children[1:-1])]
    node.children[1].parent = node
    set_children_parents(node.children[1])
def fix_call_trailer(node):
  assert is_call_trailer(node)
  args = node.children[1]
  if args.type == 'arglist':
    children = args.children
  else:
    children = node.children[1:-1]
  for arg in children:
    if is_operator(arg, '*'):
      arg.value = '...'
    elif is_operator(arg, '**'):
      warnings.warn('No analog to f(**dargs) in CoffeeScript')
    elif is_operator(arg, '='):
      warnings.warn('No support yet for f(key=value)')
def fix_parameters(node):
  assert is_node(node, 'parameters')
  assert is_operator(node.children[0], '(')
  assert is_operator(node.children[-1], ')')
  for param in node.children[1:-1]:
    assert is_node(param, 'param')
    for arg in param.children:
      if is_operator(arg, '*'):
        arg.value = '...'
      elif is_operator(arg, '**'):
        warnings.warn('No analog to def(**dargs) in CoffeeScript')

def avoid_string_for_interpolation(node):
  assert is_string(node)
  if re.search(r'''['"]''', node.value).group(0) == "'":
    return # no need to escape '#' in single-quoted strings
  def sub(match):
    if len(match.group(1)) % 2 == 0:
      return '\\' + match.group(0)
    else:
      return match.group(0)  # already escaped
  node.value = re.sub(r'(\\*)#', sub, node.value)

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
  avoid_string_for_interpolation(node)

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

def block_ends_with_return(block):
  ## Returns a list of "final" return_stmt's,
  ## or None if the block ends with something else.
  if block.type == 'simple_stmt':
    last = block
  else:
    last = block.children[-1]
  if last.type == 'simple_stmt':
    ## For simple statements, check that the last in the semicolon-separated
    ## sequence is a return.
    for child in reversed(last.children):
      if is_newline(child) or is_operator(child, ';'):
        continue
      elif child.type == 'return_stmt':
        return [child]
      else:
        return
  elif last.type == 'if_stmt':
    ## For if statements, recursively check the last in each block.
    returns = []
    for child in last.children:
      if is_block(child):
        child_returns = block_ends_with_return(child)
        if not child_returns: return
        returns.extend(child_returns)
    return returns
  else:
    return

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
  'instanceof': 5, # CoffeeScript only
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
  elif isinstance(root, CoffeeScript):
    return root.outermost
  elif isinstance(root, parso.python.tree.BaseNode):
    frontier = root.children
  while frontier:
    rest = []
    for node in frontier:
      if isinstance(node, parso.python.tree.Leaf) and node.value in precedence:
        return node.value
      elif isinstance(node, CoffeeScript):
        return node.outermost
      elif isinstance(node, parso.python.tree.BaseNode):
        rest.extend(node.children)
    frontier = rest
  warnings.warn('Could not determine top operator in %s' % node)
  return 'lambda'

def maybe_paren(node, op):
  s = recurse(node)
  node_op = top_op(node)
  if precedence[node_op] < precedence[op] or \
     (op == '.' and node.type == 'number' and '.' not in node.value):
    s = '(' + s + ')'
  return s

method_mapping = {
  # list
  'append': 'push',
  # str
  'startswith': 'startsWith',
  'endswith': 'endsWith',
  'find': 'indexOf',
  'rfind': 'lastIndexOf',
  'lower': 'toLowerCase',
  'upper': 'toUpperCase',
  'strip': 'trim',
  'lstrip': 'trimStart',
  'rstrip': 'trimEnd',
}

def leaf_iter(node):
  first = node.get_first_leaf()
  last = node.get_last_leaf()
  leaf = first
  yield leaf
  while leaf is not last:
    leaf = leaf.get_next_leaf()
    yield leaf

def name_replace(node, match, repl):
  for leaf in leaf_iter(node):
    if is_name(leaf, match):
      if hasattr(match, 'sub'):
        leaf.value = match.sub(repl, leaf.value)
      else:
        leaf.value = repl

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
    return node.prefix + node.value

  s = ''
  if isinstance(node, parso.python.tree.Leaf):
    if node.type == 'error_leaf':
      warnings.warn('ERROR LEAF DETECTED: %s' % node)
    terminate_comments(node)
    s += node.prefix

    if node.type == 'string':
      avoid_string_for_interpolation(node)
    elif node.type == 'name':
      if is_name(node, 'this'): # Now-unescaped this must be from class method
        node.value = '@'
      elif is_name(node, 'None'):
        node.value = 'null'

    if is_true(node):
      node.value = 'true'
    elif is_false(node):
      node.value = 'false'

  if isinstance(node, parso.python.tree.BaseNode):
    if is_call_trailer(node):
      ## Process *args
      fix_call_trailer(node)
      ## Avoid spaces before function and arguments in function call
      node.children[0].prefix = node.children[0].prefix.lstrip()

    if node.type == 'print_stmt':
      node.children[0].value = 'console.log'
      if is_operator(node.children[-1], ','):
        warnings.warn('No known analog of print with comma to prevent newline')

    elif node.type == 'assert_stmt':
      node.children[0].value = 'console.assert'

    elif node.type == 'funcdef':
      assert is_keyword(node.children[0], 'def')
      assert is_name(node.children[1])
      node.children[1].prefix = node.children[0].prefix
      del node.children[0]
      if node.parent and node.parent.parent and \
         node.parent.parent.type == 'classdef':  ## class method
        if is_name(node.children[0], '__init__'):
          node.children[0].value = 'constructor'
        elif is_name(node.children[0], '__str__'):
          node.children[0].value = 'toString'
        node.children[1:1] = [CoffeeScript(': ', 'leaf')]
        self = node.children[2].children[1].children[0]
        if is_name(self):
          name_replace(node.children[-1], self.value, 'this')
          parameters = node.children[2]
          del parameters.children[1]
          if len(parameters.children) > 2:
            if isinstance(parameters.children[1], parso.python.tree.Leaf):
              parameters.children[1].prefix = parameters.children[1].prefix.lstrip()
            else:
              parameters.children[1].children[0].prefix = parameters.children[1].children[0].prefix.lstrip()
        else:
          warnings.warn('method without self argument: %s' % self)
      else:
        node.children[1:1] = [CoffeeScript(' = ', 'leaf')]
      fix_parameters(node.children[2])
      ## Omit null arguments ()
      if len(node.children[2].children) == 2:
        del node.children[2]
        space = ''
      else:
        space = ' '
      block = node.children[-1]
      assert is_block(block)
      returns = block_ends_with_return(block)
      if returns:
        # Remove final 'return' keywords, and space that follows
        for return_stmt in returns:
          assert is_keyword(return_stmt.children[0], 'return')
          return_stmt.children[0].value = ''
          return_stmt.children[1].get_first_leaf().prefix = ''
      else:
        # If no final return (implicit 'return None'), return 'null' instead
        if block.type == 'simple_stmt': # one-line def
          block.children[-1:-1] = [CoffeeScript('; null', 'leaf')]
        else:
          block.children.append(CoffeeScript('null\n', 'leaf',
            block.children[-1].get_first_leaf().prefix))
      assert is_operator(node.children[-2], ':')
      in_class = parso.tree.search_ancestor(node, 'classdef')
      if in_class and in_class is not node.parent.parent:
        node.children[-2].value = space + '=>'
      else:
        node.children[-2].value = space + '->'

    elif node.type == 'lambdef':
      assert is_keyword(node.children[0], 'lambda')
      in_class = parso.tree.search_ancestor(node, 'classdef')
      if in_class and in_class is not node.parent.parent.parent.parent:
        arrow = '=>'
      else:
        arrow = '->'
      if node.children[1].type == 'param':
        node.children[0].value = '('
        node.children[1].children[0].prefix = \
          node.children[1].children[0].prefix.lstrip()
        assert is_operator(node.children[2], ':')
        node.children[2].value = ') ' + arrow
      else:
        assert is_operator(node.children[1], ':')
        node.children[0].value = arrow
        del node.children[1]

    elif node.type in ['atom_expr', 'power']:
      ## Literal string with format method immediately applied
      if len(node.children) >= 3 and \
         is_string(node.children[0]) and \
         is_method_trailer(node.children[1], 'format') and \
         is_call_trailer(node.children[2]):
        fix_call_trailer(node.children[2])
        args = split_call_trailer(node.children[2])
        count = -1
        def arg(match):
          nonlocal count
          count += 1
          return '#{' + recurse_list(args[count]).lstrip() + '}'
        prepare_string_for_interpolation(node.children[0])
        node.children[0] = CoffeeScript(
          re.sub(r'{}', arg, node.children[0].value),
          'leaf', node.children[0].prefix)
        node.children[1:3] = []

      ## Function call, possibly built-in
      elif len(node.children) >= 2 and is_name(node.children[0]) and \
           is_call_trailer(node.children[1]):
        function = node.children[0].value
        prefix = node.children[0].prefix
        args = split_call_trailer(node.children[1])
        r = None
        def assert_simple_arg(arg):
          if len(arg) != 1:
            warnings.warn('Unrecognized argument to %s: %s' %
              (function, arg))
        def assert_simple_args():
          for arg in args:
            assert_simple_arg(arg)

        if function == 'range':
          assert_simple_args()
          args = tuple(recurse(arg[0]).lstrip() for arg in args)
          if len(args) == 1:
            r = CoffeeScript('[0...%s]' % args[0], '[', prefix)
          elif len(args) == 2:
            r = CoffeeScript('[%s...%s]' % args, '[', prefix)
          elif len(args) == 3:
            if node.parent and node.parent.type in ['for_stmt', 'comp_for', 'sync_comp_for']:
              r = CoffeeScript('[%s...%s] by %s' % args, '[', prefix)
            else:
              r = CoffeeScript('(_i for _i in [%s...%s] by %s)' % args, '(', prefix)
          else:
            warnings.warn('range with %d args' % len(args))

        elif function in ['str', 'bin', 'oct', 'hex']:
          assert_simple_args()
          if function == 'str' and len(args) == 0: # str()
            r = CoffeeScript("''", 'leaf')
          elif len(args) == 1: # str(x) or related
            if function == 'str':
              base = ''
            elif function == 'bin':
              base = 2
            elif function == 'oct':
              base = 8
            elif function == 'hex':
              base = 16
            r = CoffeeScript(maybe_paren(args[0][0], '.') +
                  '.toString(%s)' % base, '.', prefix)
          else:
            warnings.warn('%s() with %d arguments' % (function, len(args)))

        elif function in ['int', 'float']:
          assert_simple_args()
          node.children[0].value = 'parse' + function.capitalize()

        elif function == 'ord':
          assert_simple_args()
          if len(args) == 1:
            r = CoffeeScript(maybe_paren(args[0][0], '.') +
                  '.charCodeAt()', '.', prefix)
          else:
            warnings.warn('%s() with %d arguments' % (function, len(args)))

        elif function == 'chr':
          assert_simple_args()
          if len(args) == 1:
            r = CoffeeScript('String.fromCharCode(%s)' %
              recurse(args[0][0]), '.', prefix)
          else:
            warnings.warn('%s() with %d arguments' % (function, len(args)))

        elif function == 'isinstance':
          assert_simple_args()
          if len(args) == 2:
            r = CoffeeScript('%s instanceof %s' %
              (maybe_paren(args[0][0], 'instanceof'),
               maybe_paren(args[1][0], 'instanceof').lstrip()),
              'instanceof', prefix)
          else:
            warnings.warn('%s() with %d arguments' % (function, len(args)))

        elif function == 'len':
          assert_simple_args()
          if len(args) == 1:
            r = CoffeeScript('%s.length' % maybe_paren(args[0][0], '.'),
                  '.', prefix)
          else:
            warnings.warn('%s() with %d arguments' % (function, len(args)))

        if r is not None:
          node.children[:2] = [r]

      ## this.x -> @x
      elif len(node.children) >= 2 and is_name(node.children[0], 'this') and \
           is_method_trailer(node.children[1]):
        if parso.tree.search_ancestor(node, 'classdef'):
          node.children[0].value = '@'
          del node.children[1].children[0]

      ## Method name mapping
      for child in node.children:
        if is_method_trailer(child) and child.children[1].value in method_mapping:
          child.children[1].value = method_mapping[child.children[1].value]

      ## .extend(x) -> .push(...x)
      for i in range(len(node.children)-1):
        if is_method_trailer(node.children[i]) and \
           is_call_trailer(node.children[i+1]) and \
           node.children[i].children[1].value == 'extend':
          args = split_call_trailer(node.children[i+1])
          if len(args) != 1:
            warnings.warn('%d parameters passed to .extend()' % len(args))
            continue
          if is_operator(args[0][0], '*'):
            warnings.warn('*args passed to .extend()')
            continue
          force_call_trailer_arglist(node.children[i+1])
          if len(args[0]) == 1 and args[0][0].type == 'atom' and \
             is_operator(args[0][0].children[0], '[') and \
             is_node(args[0][0].children[1], 'testlist_comp') and \
             is_operator(args[0][0].children[2], ']') and \
             not any(child.type in ['comp_for', 'sync_comp_for']
                     for child in args[0][0].children[1].children):
            ## .extend([1, 2]) -> .push(1, 2)
            node.children[i+1].children[1].children[0].children = \
              node.children[i+1].children[1].children[0].children[1].children
            set_children_parents(node.children[i+1].children[1])
          else:
            node.children[i+1].children[1].children.insert(0,
              parso.python.tree.Operator('*',
                node.children[i+1].children[1].children[0].start_pos))
          node.children[i].children[1].value = 'push'

    elif node.type in ['for_stmt', 'while_stmt', 'if_stmt']:
      assert is_keyword(node.children[0], node.type.split('_', 1)[0])
      for i, child in reversed(list(enumerate(node.children))):
        if is_operator(child, ':'):
          if child.prefix:
            warnings.warn('Discarding prefix %r to colon' % child.prefix)
          del node.children[i]
        if is_keyword(child, 'elif'):
          child.value = 'else if'
        elif is_keyword(child, 'else') and node.type != 'if_stmt':
          warnings.warn('No support for else clause in %s' % node.type)

      if node.type == 'while_stmt' and is_true(node.children[1]):
        node.children[0].value = 'loop'
        del node.children[1]

      if is_node(node.children[1], 'not_test') and \
         is_keyword(node.children[1].children[0], 'not'):
        unnot = True
        if node.type == 'while_stmt':
          node.children[0].value = 'until'
        elif node.type == 'if_stmt':
          node.children[0].value = 'unless'
        else:
          unnot = True
        if unnot:
          assert len(node.children[1].children) == 2
          node.children[1] = node.children[1].children[1]

      ## One-liners
      assert is_block(node.children[-1])
      if is_node(node.children[-1], 'simple_stmt'): # vs. suite
        node.children[0:0] = [node.children.pop()]
        node.children[0].get_first_leaf().prefix, node.children[1].prefix = \
          node.children[1].prefix, node.children[0].get_first_leaf().prefix or ' '
        if is_newline(node.children[0].children[-1]):
          node.children.append(node.children[0].children.pop())

    elif node.type == 'classdef':
      assert is_operator(node.children[-2], ':')
      del node.children[-2]

    elif node.type in ['test']:
      if is_keyword(node.children[1], 'if') and \
         is_keyword(node.children[3], 'else'):
        node.children = [node.children[1], node.children[2],
          CoffeeScript('then', 'if', ' '), node.children[0],
          node.children[3], node.children[4]]

  #if node.type in ['name', 'number', 'string', 'operator', 'endmarker', 'newline']:
  if isinstance(node, parso.python.tree.Leaf):
    s += node.value
  elif isinstance(node, parso.python.tree.BaseNode):
    s += recurse_list(node.children)
  else:
    s += str(node)
  return s

def recurse_list(node_list):
  return ''.join(map(recurse, node_list))

def convert_tree(node):
  # Escape existing use of CoffeeScript keywords not in Python
  name_replace(node, re.compile(r'^_*(this|function)$'), r'_\g<0>')
  return recurse(node)

argparser = argparse.ArgumentParser(
  description="Attempt to convert Python code into CoffeeScript")
argparser.add_argument('-p', '--python', metavar='N.N',
  dest='python_version', default='3.6', help='Python version (e.g. 2.7)')
argparser.add_argument('filenames', metavar='filename.py', type=str,
  nargs='+', help='Python code to convert into filename.coffee')

def main():
  args = argparser.parse_args()
  for filename in args.filenames:
    print(filename)
    if filename.endswith('.coffee'): continue  ## avoid overwrite
    with open(filename, 'r', encoding='utf8') as pyfile:
      py = pyfile.read()
      newline = pyfile.newlines
    if isinstance(newline, tuple): newline = newline[0]
    tree = parso.parse(py, version=args.python_version)
    dump_tree(tree)
    csname = os.path.splitext(filename)[0] + '.coffee'
    print('==>', csname)
    cs = convert_tree(tree)
    with open(csname, 'w', newline=newline, encoding='utf8') as csfile:
      csfile.write(cs)

if __name__ == '__main__': main()
