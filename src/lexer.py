from ply import lex
import sys

operators = (
    'PLUS',
    'MINUS',
    'MULTIPLY',
    'DIVIDE',
    'MODULUS',
    'EXPONENT',
    'IS_EQUAL',
    'IS_NOTEQUAL',
    'IS_EQUALNOTEQUAL',
    'GREATER_THAN',
    'LESS_THAN',
    'GREATER_THAN_EQUALTO',
    'LESS_THAN_EQUALTO',
    'ASSIGN',
    'PLUS_ASSIGN',
    'MINUS_ASSIGN',
    'MULTIPLY_ASSIGN',
    'DIVIDE_ASSIGN',
    'MOD_ASSIGN',
    'EXPONENT_ASSIGN',
    'BIT_NOT',
    'BIT_AND',
    'BIT_OR',
    'BIT_XOR',
    'BIT_COMPLEMENT',
    'BIT_LEFT_SHIFT',
    'BIT_RIGHT_SHIFT',
    # 'AND',
    'C_AND',
    'C_OR',
    'NOT',
    # 'INVERTED_QUOTES',
    'DOT',
    # 'REPEAT',
    # 'RANGE',
    'AUTO_INC',
    'AUTO_DEC',
    'DEREFERENCE',
    'DEREFERENCE_OPEN',
    'SLASH'
)

literals = ['\n']

identifiers = (
    'SCALAR_ID',
    'ARRAY_ID',
    'HASH_ID',
    'ARGUMENT_ARRAY_ID',
    'ARGUMENT_SCALAR_ID'
)

t_PLUS = r'\+'
t_MINUS = r'-'
t_MULTIPLY = r'\*'
t_DIVIDE = r'/'
t_MODULUS = r'%'
t_EXPONENT = r'\*\*'
t_IS_EQUAL = r'=='
t_IS_NOTEQUAL = r'!='
t_IS_EQUALNOTEQUAL = '<=>'
t_GREATER_THAN = r'>'
t_LESS_THAN = r'<'
t_GREATER_THAN_EQUALTO = r'>='
t_LESS_THAN_EQUALTO  = r'<='
t_KEY_VALUE = r'=>'
t_ASSIGN = r'='
t_PLUS_ASSIGN = r'\+='
t_MINUS_ASSIGN = r'-='
t_MULTIPLY_ASSIGN = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_MOD_ASSIGN = r'%='
t_EXPONENT_ASSIGN = r'\*\*='
t_BIT_NOT = r'!'
t_BIT_AND = r'&'
t_BIT_OR = r'\|'
t_BIT_XOR = r'\^'
t_BIT_COMPLEMENT = r'~'
t_BIT_LEFT_SHIFT = r'<<'
t_BIT_RIGHT_SHIFT = r'>>'
# t_AND = r'and'
t_C_AND = r'&&'
t_C_OR = r'\|\|'
t_NOT = r'not'
t_DOT = r'\.'
# t_RANGE = r'\.\.'
# t_REPEAT = r'x'

t_AUTO_INC = r'\+\+'
t_AUTO_DEC = r'--'
t_DEREFERENCE = r'->'
t_DEREFERENCE_OPEN = r'\$\{'
t_SLASH = r'\\'

# Dictionary of reserved keywords
reserved = {
    # 'sort': 'SORT',
    'keys' : 'KEYS',
    'values' : 'VALUES',
    # 'ENV' : 'ENV',
    'shift': 'SHIFT',
    'push' : 'PUSH',
    'pop' : 'POP',
    'unshift': 'UNSHIFT',
    'lt' : 'LT',
    'gt' : 'GT',
    'le' : 'LE',
    'ge' : 'GE',
    'eq' : 'EQ',
    'ne' : 'NE',
    'cmp' : 'CMP',
    # 'chomp' : 'CHOMP',
    # 'use' : 'USE',
    # 'strict' : 'STRICT',
    'my' : 'MY',
    'if' : 'IF',
    'else' : 'ELSE',
    'elsif' :'ELSIF',
    'unless' : 'UNLESS',
    'while' : 'WHILE',
    'print' : 'PRINT',
    'until' : 'UNTIL',
    'for' : 'FOR',
    # 'each' : 'EACH',
    'foreach' : 'FOREACH',
    'continue' : 'CONTINUE',
    'next' : 'NEXT',
    'last' : 'LAST',
    'goto' : 'GOTO',
    'redo' : 'REDO',
    'switch':'SWITCH',
    'case':'CASE',
    'scalar' : 'SCALAR',
    # 'CORE' : 'CORE',
    'do' : 'DO',
    # 'exp' : 'EXP',
    'if' : 'IF',
    # 'lock' : 'LOCK',
    # 'm' : 'M',
    # 'no' : 'NO',      # Opposite of 'use'
    'package': 'PACKAGE', 
    # 'qr' : 'QR',
    'qw' : 'QW',
    # 's' : 'S',
    'sub' : 'SUB',
    # 'tr' : 'TR',
    'xor' : 'XOR',
    # 'y' : 'Y',
    'exit' : 'EXIT',
    'exists' : 'EXISTS',
    # 'die' : 'DIE',
    'and' : 'AND',
    'or' : 'OR',
    # 'reverse' : 'REVERSE',
    # '__DATA__' : '__DATA__'172.27.22.157,
    # '__END__' : '__END__',
    # '__FILE__' : '__FILE__',
    # '__LINE__' : '__LINE__',
    # '__PACKAGE__' : '__PACKAGE__',
    'return' : 'RETURN',
    # 'ref' : 'REF',
    'x' : 'REPEAT',
    'splice' : 'SPLICE',
    'delete' : 'DELETE',
    'local' : 'LOCAL',
    'state' : 'STATE'
}

# List of token names
tokens = operators + (
    # 'STDIN',
    # 'KEYWORD',
    'INTEGER',
    'RANGE',
    'FLOAT',
    'OCTAL',
    'HEX',
    'STRING',
    'OPEN_PAREN',
    'CLOSE_PAREN',
    'OPEN_BRACE',
    'CLOSE_BRACE',
    'OPEN_SBRACKET',
    'CLOSE_SBRACKET',
    'COLON',
    'SEMICOLON',
    'COMMA',
    'KEY_VALUE',
    'QUESTION_CONDITIONAL_OP',
    # 'ENDHELP',
    # 'SINGLE_QUOTES',
    # 'DOUBLE_QUOTES',
    'SUBROUTINE_ID'
) + tuple(reserved.values()) +  identifiers

t_STRING = r'(\'([^\'])*\')|(\"([^\"])*\")'
t_HEX = r'0[xX][0-9a-fA-F]+'
t_INTEGER = r'0|([1-9][0-9]*)'
t_RANGE = r'\.\.'
t_OPEN_PAREN  = r'\('
t_CLOSE_PAREN  = r'\)'
t_OPEN_BRACE = r'\{'
t_CLOSE_BRACE = r'\}'
t_OPEN_SBRACKET = r'\['
t_CLOSE_SBRACKET = r'\]'
t_COLON = r'\:'
t_SEMICOLON = r'\;'
t_COMMA = r'\,'
t_QUESTION_CONDITIONAL_OP = r'\?'
# t_STRING_SLASH = r'(\/([^\/])*\/)'
# t_STRING_BRACKET = r'(\(([^\(\)])*\))'
# t_STDIN = r'<>|<STDIN>'

def t_FLOAT(t):
    r'(\d*[\.]?\d+[Ee][-\+]?\d+)|(\d*\.\d+)'
    return t

def t_OCTAL(t):
    r'[0][0-7][0-7]*'
    return t

def t_ARGUMENT_SCALAR_ID(t):
    r'\$\_'
    return t

def t_ARGUMENT_ARRAY_ID(t):
    r'\@\_'
    return t

def t_SCALAR_ID(t):
    r'\$[a-zA-Z0-9_]+'
    return t

def t_ARRAY_ID(t):
    r'@[a-zA-Z0-9_]+'
    return t

def t_HASH_ID(t):
    r'%[a-zA-Z][a-zA-Z0-9_]*'
    return t

# def t_SINGLE_QUOTES(t):
#     #r'(q\{.*\})|(q/.*/)|(q=.*=)'
#     return t

# def t_DOUBLE_QUOTES(t):
#     #r'(qq\{.*\})|(qq/.*/)|(qq=.*=)'
#     return t

# def t_INVERTED_QUOTES(t):
#     r'(qx\{.*\})|(qx/.*/)|(qx=.*=)'
#     return t

def t_KEYWORD(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    if t.value not in reserved:
        t.type = 'SUBROUTINE_ID'
        return t
    t.type = reserved.get(t.value,'STRING')
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print 'Lex Error: "{}" is not a valid token type in Perl'.format(t.value[0])
    print "Line Number:{}</br>".format(t.lineno)
    t.lexer.skip(1)

def t_COMMENT(t):
    r'\#.*'
    pass

# # Build the lexer
lex.lex()

# freq_dict = {}
# lexeme_dict = {}

# for tok in tokens:
#     freq_dict[tok] = 0
#     lexeme_dict[tok] = []

# file = sys.argv[1]
# f = open(file,'r')
# data = f.read()

# lexer.input(data)

# for tok in lexer:    
#     freq_dict[tok.type] += 1
#     if freq_dict[tok.type] != 0:
#         lexeme_dict[tok.type].append(tok.value)


# print '{0: ^23}'.format('Token'),
# print '{0: ^11}'.format('Occurences'),
# print '{0: ^7}'.format('Lexemes')
# for key,value in lexeme_dict.iteritems():
#     if freq_dict[key] != 0:
#         print '{0: ^23}'.format(key),
#         print '{0: ^12}'.format(freq_dict[key]),
#         for a in set(value):
#             print a,
#         print