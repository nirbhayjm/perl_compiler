#!/usr/bin/python

import sys
import pprint
import ply.yacc as yacc
from lexer import tokens
import ThreeAddressCode
import SymbolTable

class Node(object):

    def __init__(self,content,childList=None,parentPtr=None):
        self.content = content
        self.children = childList
        self.parent = parentPtr

    def RecPrint(self):
        # print "ChildList is :",self.children
        for child in self.children:
            if isinstance(child,Node):
                child.RecPrint()
            else: 
                print str(child), 

#==============================================================================
# Start symbol
#==============================================================================
start = 'program'
MAX_ARRAY_SIZE = '100'

def p_program(p):
    '''program          : M_global_next stmts
    '''
    TAC[ST.currentScope].placeLabel(p[1]['labels']['Stmt_End'])
    TAC[ST.currentScope].emit('exit','0','','')

def p_M_global_next(p):
    '''M_global_next :'''

    p[0] = {
        'labels' : {
            'Stmt_Start'  : TAC[ST.currentScope].getNextQuad(),
            'Stmt_End'    : TAC[ST.currentScope].makeLabel(),
            'redo'        : 'Unassigned',
            'last'        : 'Unassigned',
            'continue'    : 'Unassigned',
            'next'        : 'Unassigned'

        },
        'place' : None
    }

#==============================================================================
# Statement types
#==============================================================================

def p_stmts(p):
    '''stmts            : stmts M_stmt_next stmt
                        |       M_stmt_next stmt
    ''' 
    p[0] = p[-1]

def p_M_stmt_next(p):
    '''M_stmt_next :'''

    p[0] = {
        'labels' : {
            'Stmt_Start' : TAC[ST.currentScope].getNextQuad(),   
            'Stmt_End'   : TAC[ST.currentScope].makeLabel(),
            'redo'       : p[-1]['labels']['redo'],
            'last'       : p[-1]['labels']['last'],
            'continue'   : p[-1]['labels']['continue'],
            'next'       : p[-1]['labels']['next']
        }
    }

#--- Only some statements need to terminate with a SEMICOLON (EOS)
def p_stmt(p):
    '''stmt             : exp_stmt                  EOS
                        | print_stmt                EOS
                        | compound_stmt
                        | selection_stmt
                        | iteration_stmt
                        | loop_control_stmt         EOS
                        | subroutine
                        | subroutine_control        EOS
                        | switch_stmt
                        | type_scope M_TS decl_list EOS
                        | PACKAGE SUBROUTINE_ID     EOS
                        | exit_stmt                 EOS
                        | struct_decl               EOS

    '''
    p[0] = p[1]
    TAC[ST.currentScope].placeLabel(p[-1]['labels']['Stmt_End'])

def p_compound_stmt(p):
    '''compound_stmt    : OPEN_BRACE M_CS_next stmts CLOSE_BRACE
                        | OPEN_BRACE                 CLOSE_BRACE
    '''

def p_M_CS_next(p):
    '''M_CS_next :'''

    p[0] = { 'labels' : {
                'last'      : 'Unassigned',
                'redo'      : 'Unassigned',
                'continue'  : 'Unassigned',
                'next'      : 'Unassigned',
        } ,
        'place'     : None
    }

    try:
        # print "Beginning try with ps:",p[0],p[-2]
        p[0]['labels']['redo'] = p[-2]['labels']['redo']
        p[0]['labels']['last'] = p[-2]['labels']['last']
        p[0]['labels']['next'] = p[-2]['labels']['next']        
        p[0]['labels']['continue'] = p[-2]['labels']['continue']
        # print "Try successful in M_CS_next"
        # print p[0]  
    except:
        pass

def p_exp_stmt(p):
    '''exp_stmt         : assignment_exp
                        | arith_relat_exp
    '''
    p[0] = p[1]

def p_exit_stmt(p):
    '''exit_stmt        : EXIT
                        | EXIT arith_relat_exp
                        | EXIT arith_relat_exp IF exp_stmt
                        | EXIT                 IF exp_stmt
    '''
    if len(p) <= 3:
        if len(p) == 3:
            exit_val = p[2]['place']
        else:
            exit_val = 0
        TAC[ST.currentScope].emit('exit',exit_val,'','')        
    elif len(p) > 3:
        if len(p) == 4:
            loc = 3
            exit_val = '0'
        elif len(p) == 5:
            loc = 4
            exit_val = p[2]['place']
        TAC[ST.currentScope].emit('ifgoto','eq',p[loc]['place'],'0',TAC[ST.currentScope].getNextQuad()+2)
        TAC[ST.currentScope].emit('exit',exit_val,'','')

# EOS --> End of statement
def p_EOS(p):
    '''EOS              : SEMICOLON
    '''

#==============================================================================
# Selection statements (if, else)
#
# Note that in Perl, the curly braces are required
# even for single statement if/else blocks. Hence,
# the if/else blocks have compound_stmt
#==============================================================================

def p_selection_stmt(p):
    '''selection_stmt   : IF     OPEN_PAREN exp_stmt CLOSE_PAREN M_ifBegin compound_stmt M_ifEnd else_block
                        | UNLESS OPEN_PAREN exp_stmt CLOSE_PAREN M_ifBegin compound_stmt M_ifEnd else_block
    '''

def p_M_ifBegin(p):
    ''' M_ifBegin :'''

    p[0] = {
        'labels' : {
            'ifEndLabel'    : TAC[ST.currentScope].makeLabel(),
            'stmtEndLabel'  : p[-5]['labels']['Stmt_End'],
            'last'          : p[-5]['labels']['last'],
            'redo'          : p[-5]['labels']['redo'],
            'continue'      : p[-5]['labels']['continue'],
            'next'          : p[-5]['labels']['next'],
        }
    }

    ifEndLabel = p[0]['labels']['ifEndLabel']
    TAC[ST.currentScope].addPatchList(ifEndLabel)
    if p[-4] == 'if':
        #--- If condition is false, go to ifEndLabel
        TAC[ST.currentScope].emit('ifgoto','eq',p[-2]['place'],'0',ifEndLabel)
    elif p[-4] == 'unless':
        #--- Unless: If condition is true, go to ifEndLabel
        TAC[ST.currentScope].emit('ifgoto','eq',p[-2]['place'],'1',ifEndLabel)        

def p_M_ifEnd(p):
    '''M_ifEnd :'''

    #--- Propogate the stmtEndLabel
    p[0] = { 
        'labels' : {
            'stmtEndLabel' : p[-2]['labels']['stmtEndLabel'],
            'last'         : p[-2]['labels']['last'],
            'redo'         : p[-2]['labels']['redo'],
            'continue'     : p[-2]['labels']['continue'],
            'next'          : p[-2]['labels']['next'],
        }
    }
    
    TAC[ST.currentScope].addPatchList(p[-2]['labels']['stmtEndLabel'])
    #--- Place the unconditional jump to the end of the entire selection statement
    TAC[ST.currentScope].emit('goto',p[-2]['labels']['stmtEndLabel'],'','')
    #--- Place the ifEndLabel at the end of the if-block (auto back patches it)
    TAC[ST.currentScope].placeLabel(p[-2]['labels']['ifEndLabel'])

#--- 'If' block may or may not be followed by an else/elsif block
def p_else_block(p):
    '''else_block       : elsif_list ELSE M_elseLast compound_stmt
                        | elsif_list
    '''

def p_M_elseLast(p):
    '''M_elseLast :'''
    #--- Copy from M_ifEnd
    p[0] = p[-3]

def p_elsif_list(p):
    '''elsif_list       : M_propEnd ELSIF OPEN_PAREN exp_stmt CLOSE_PAREN M_elsifBegin compound_stmt M_elsifEnd elsif_list
                        |
    '''

def p_M_propEnd(p):
    '''M_propEnd :'''
    #--- Propogate the statement end label
    p[0] = p[-1]

def p_M_elsifBegin(p):
    '''M_elsifBegin :'''

    elsifEndLabel = TAC[ST.currentScope].makeLabel()
    p[0] = { 
        'labels' : {
            'elsifEndLabel' : elsifEndLabel,
            'stmtEndLabel'  : p[-5]['labels']['stmtEndLabel'],
            'last'          : p[-5]['labels']['last'],
            'redo'          : p[-5]['labels']['redo'],
            'continue'      : p[-5]['labels']['continue'],
            'next'          : p[-5]['labels']['next'],
        } 
    }
        
    TAC[ST.currentScope].addPatchList(elsifEndLabel)
    TAC[ST.currentScope].emit('ifgoto','eq',p[-2]['place'],'0',elsifEndLabel)

def p_M_elsifEnd(p):
    '''M_elsifEnd :'''

    elsifEndLabel = p[-2]['labels']['elsifEndLabel']
    stmtEndLabel  = p[-2]['labels']['stmtEndLabel']
    p[0] = { 
        'labels' : {
            'stmtEndLabel' : stmtEndLabel,
            'last'         : p[-2]['labels']['last'],
            'redo'         : p[-2]['labels']['redo'],
            'continue'     : p[-2]['labels']['continue'],
            'next'          : p[-2]['labels']['next'],
        } 
    }

    TAC[ST.currentScope].addPatchList(stmtEndLabel)
    TAC[ST.currentScope].emit('goto',stmtEndLabel,'','')
    TAC[ST.currentScope].placeLabel(elsifEndLabel)

#--- Follows assignment expression and executes it depending on selection statement
def p_post_selection(p):
    '''post_selection   : IF     OPEN_PAREN exp_stmt CLOSE_PAREN
                        | UNLESS OPEN_PAREN exp_stmt CLOSE_PAREN
                        |
    '''
    if len(p) == 1:
        p[0] = None
    else:
        p[0] = {
            'exp_place' : p[3]['place'],
            'cond'      : p[1]
        }

#==============================================================================
# Switch case statements
#
# Use the Switch.pm library for Perl:
#       use Switch;
#
# Install it by:
#       sudo apt-get install libswitch-perl
#==============================================================================

def p_switch_stmt(p):


    '''switch_stmt      : SWITCH OPEN_PAREN exp_stmt CLOSE_PAREN M_switchBegin OPEN_BRACE switch_block CLOSE_BRACE

    '''
    TAC[ST.currentScope].placeLabel(p[5]['labels']['SwitchStmtEnd'])


def p_switch_block(p):
    '''switch_block     : M_switchStmtValue case_stmt switch_block
                        | M_switchStmtValue default_case
    '''

#--- replaced primary_exp with exp_stmt as it it the same as the if-else expressions
def p_case_stmt(p):
    '''case_stmt        : CASE OPEN_PAREN exp_stmt CLOSE_PAREN M_caseBegin compound_stmt
    '''

    TAC[ST.currentScope].addPatchList(p[-1]['labels']['SwitchStmtEnd'])
    TAC[ST.currentScope].emit('goto',p[-1]['labels']['SwitchStmtEnd'],'','','') 


def p_default_case(p):
    '''default_case     : ELSE M_defaultCase compound_stmt
                        |
    '''

def p_M_switchBegin(p):
    ''' M_switchBegin :'''


    p[0] = { 'place' : p[-2]['place'] ,
             'labels' : 
                {
                'SwitchStmtEnd' : p[-5]['labels']['Stmt_End'],
                'last'          : p[-5]['labels']['Stmt_End'],
                'redo'          : p[-5]['labels']['redo'],
                'continue'      : p[-5]['labels']['continue'],
                'next'          : p[-5]['labels']['next'],
                'caseNextStmtLabel' : 'Unassigned'
                }
            }
    # print p[:]

def p_M_switchStmtValue(p):
    ''' M_switchStmtValue :'''

    # t = TAC.makeLabel()

    p[0] = { 
        'place' : p[-2]['place'],
        'labels' : { 
             'SwitchStmtEnd'        : p[-2]['labels']['SwitchStmtEnd'], 
             'caseNextStmtLabel'    : TAC[ST.currentScope].makeLabel(),
             'last'          : p[-2]['labels']['last'],
             'redo'          : p[-2]['labels']['redo'],
             'continue'      : TAC[ST.currentScope].makeLabel(),
             'next'          : TAC[ST.currentScope].makeLabel()  
        }
    }   
       
    if p[-2]['labels']['caseNextStmtLabel'] != 'Unassigned':
        TAC[ST.currentScope].placeLabel(p[-2]['labels']['caseNextStmtLabel'])
        TAC[ST.currentScope].placeLabel(p[-2]['labels']['next'])      
        TAC[ST.currentScope].placeLabel(p[-2]['labels']['continue'])      

def p_M_caseBegin(p):
    ''' M_caseBegin :'''
    p[0] = p[-5]
    TAC[ST.currentScope].addPatchList(p[-5]['labels']['caseNextStmtLabel'])
    TAC[ST.currentScope].emit('ifgoto','neq',p[-2]['place'], p[-5]['place'] , p[-5]['labels']['caseNextStmtLabel'] )

def p_M_defaultCase(p):
    ''' M_defaultCase :'''
    p[0] = p[-2]    

#==============================================================================
# Iteration statements (for,while,until)
#==============================================================================

#--- The blanks in place of exp_stmt in for loops is necessary
#--- because exp_stmt cannot and should not go to an empty string
def p_iteration_stmt(p):
    '''iteration_stmt   : WHILE OPEN_PAREN exp_stmt CLOSE_PAREN M_CS_begin compound_stmt
                        | UNTIL OPEN_PAREN exp_stmt CLOSE_PAREN M_CS_begin compound_stmt
                        | DO M_DWCS_begin compound_stmt M_DW_End WHILE OPEN_PAREN exp_stmt CLOSE_PAREN M_E_end SEMICOLON
                        | FOREACH SCALAR_ID OPEN_PAREN array_indexer CLOSE_PAREN compound_stmt
                        | FOR OPEN_PAREN for_exp_stmt SEMICOLON M_E2_begin for_exp_stmt SEMICOLON M_E3_begin for_exp_stmt CLOSE_PAREN M_FCS_begin compound_stmt
    '''
    if p[1] in ['while','until']:
        TAC[ST.currentScope].emit('goto',p[-1]['labels']['Stmt_Start'],'','')
    elif p[1] == 'for':
        TAC[ST.currentScope].addPatchList(p[5]['labels']['E3_begin']) 
        TAC[ST.currentScope].emit('goto',p[5]['labels']['E3_begin'],'','')
        TAC[ST.currentScope].placeLabel(p[5]['labels']['S_end'])

def p_for_exp_stmt(p):
    '''for_exp_stmt     : exp_stmt
                        |
    '''
    if len(p) == 2:
        p[0] = p[1]

def p_M_DWCS_begin(p):
    '''M_DWCS_begin :'''

    p[0] = {
        'labels' : {
            'continue'  : TAC[ST.currentScope].makeLabel(),
            'next'      : TAC[ST.currentScope].makeLabel(),        
            'last'      : p[-2]['labels']['Stmt_End'],
            'redo'      : TAC[ST.currentScope].getNextQuad(),
        }
    }

def p_M_DW_End(p):
    '''M_DW_End :'''
    TAC[ST.currentScope].placeLabel(p[-2]['labels']['continue'])
    TAC[ST.currentScope].placeLabel(p[-2]['labels']['next'])

def p_M_E_end(p):
    ''' M_E_end   : '''
    TAC[ST.currentScope].emit('ifgoto','eq',p[-2]['place'],1,p[-9]['labels']['Stmt_Start'])

def p_M_E2_begin(p):
    ''' M_E2_begin  : '''

    p[0] = {
        'labels': {
            'E2_begin' : TAC[ST.currentScope].getNextQuad(),
            'E3_begin' : None,  #To be assigned by M_E3
            'S_begin'  : TAC[ST.currentScope].makeLabel(), 
            'S_end'    : TAC[ST.currentScope].makeLabel()
        }
    }

def p_M_E3_begin(p):
    ''' M_E3_begin  : '''

    if p[-2] != None:
        TAC[ST.currentScope].addPatchList(p[-3]['labels']['S_end'])
        TAC[ST.currentScope].emit('ifgoto','eq',p[-2]['place'],0,p[-3]['labels']['S_end'])
    else:
        TAC[ST.currentScope].patchMap[p[-3]['labels']['S_end']] = []
    TAC[ST.currentScope].addPatchList(p[-3]['labels']['S_begin'])
    TAC[ST.currentScope].emit('goto',p[-3]['labels']['S_begin'],'','')
    p[-3]['labels']['E3_begin'] = TAC[ST.currentScope].getNextQuad()

def p_M_FCS_begin(p):
    ''' M_FCS_begin     : '''

    p[0] = {
        'labels' : {
            'continue'  : p[-6]['labels']['E3_begin'],
            'last'      : p[-11]['labels']['Stmt_End'],
            'redo'      : TAC[ST.currentScope].getNextQuad() + 1,
            'next'      : p[-6]['labels']['E3_begin']
        }
    }

    TAC[ST.currentScope].addPatchList(p[-6]['labels']['E2_begin'])
    TAC[ST.currentScope].emit('goto',p[-6]['labels']['E2_begin'],'','')
    TAC[ST.currentScope].placeLabel(p[-6]['labels']['S_begin'])

def p_M_CS_begin(p):
    '''M_CS_begin   : '''

    Stmt_End = p[-5]['labels']['Stmt_End']
    TAC[ST.currentScope].addPatchList(Stmt_End)
    if p[-4] == 'while':
        TAC[ST.currentScope].emit('ifgoto','eq',p[-2]['place'],0,Stmt_End)
    elif p[-4] == 'until':
        TAC[ST.currentScope].emit('ifgoto','eq',p[-2]['place'],1,Stmt_End)

    p[0] = {
        'labels' : {
            'continue'  : p[-5]['labels']['Stmt_Start'],
            'last'      : p[-5]['labels']['Stmt_End'],
            'redo'      : TAC[ST.currentScope].getNextQuad(),
            'next'      : p[-5]['labels']['Stmt_Start'] 
       }
    }

#==============================================================================
# Loop control statements
#  'next' is equivalent to the C 'continue'
#  'last' is equivalent to the C 'break'
#  'redo' restarts loop without evaluating expression again
#==============================================================================

def p_loop_control_stmt(p):
    '''loop_control_stmt    : NEXT
                            | LAST
                            | CONTINUE
                            | REDO
                            | GOTO 
    '''
        
    if p[-1]['labels']['last'] is 'Unassigned':
        print "Semantic Error! Can't use loop control statement outside of loops!"
    
    if p[1] == 'last':
        TAC[ST.currentScope].addPatchList(p[-1]['labels']['last'])
        TAC[ST.currentScope].emit('goto',p[-1]['labels']['last'],'','')
    elif p[1] == 'redo':
        TAC[ST.currentScope].emit('goto',p[-1]['labels']['redo'],'','')
    elif p[1] == 'next':
        TAC[ST.currentScope].addPatchList(p[-1]['labels']['next'])
        TAC[ST.currentScope].emit('goto',p[-1]['labels']['next'],'','')    
    elif p[1] == 'continue':
        TAC[ST.currentScope].addPatchList(p[-1]['labels']['continue'])
        TAC[ST.currentScope].emit('goto',p[-1]['labels']['continue'],'','')

#==============================================================================
# Subroutine rules
#==============================================================================

def p_subroutine(p):
    '''subroutine           : SUB SUBROUTINE_ID M_SubBegin compound_stmt
    '''
    TAC[ST.currentScope].emit('ret','','','')
    ST.endDeclareSub()

def p_M_SubBegin(p):
    '''M_SubBegin : '''
    #TODO: Check if method is already declared in current scope
    

    ST.declareSub(p[-1])
    TAC[ST.currentScope] = ThreeAddressCode.ThreeAddressCode()
    TAC[ST.currentScope].emit('label',ST.getSubLabel(),'','')

def p_subroutine_control(p):
    '''subroutine_control   : RETURN arith_relat_exp
    '''
    p[0] = p[2]
    TAC[ST.currentScope].emit('ret',p[2]['place'],'','')

#==============================================================================
# Class/Struct rules
#==============================================================================

def p_struct_decl(p):
    '''struct_decl          : STRUCT OPEN_PAREN SUBROUTINE_ID M_classInit KEY_VALUE OPEN_SBRACKET hash_decl_struct CLOSE_SBRACKET CLOSE_PAREN
                            | STRUCT OPEN_PAREN SUBROUTINE_ID M_classInit KEY_VALUE OPEN_BRACE    hash_decl_struct CLOSE_BRACE    CLOSE_PAREN
                            | STRUCT SUBROUTINE_ID M_classInit KEY_VALUE OPEN_SBRACKET hash_decl_struct CLOSE_SBRACKET 
                            | STRUCT SUBROUTINE_ID M_classInit KEY_VALUE OPEN_BRACE    hash_decl_struct CLOSE_BRACE 
    '''
    if len(p) == 10:
        p[0] = { 'size' : p[7]['size'] }
    else :
        p[0] = { 'size' : p[6]['size'] }
    ST.endDeclareClass()

def p_M_classInit(p):
    '''M_classInit :'''
    ST.declareClass(p[-1])

#--- Hash declaration list for declaring variables in class
def p_hash_decl_struct(p):
    '''hash_decl_struct     : SUBROUTINE_ID KEY_VALUE   type_of_var COMMA hash_decl_struct
                            | SUBROUTINE_ID KEY_VALUE   type_of_var
                            | SUB SUBROUTINE_ID M_class_sub compound_stmt M_class_end COMMA hash_decl_struct
                            | SUB SUBROUTINE_ID M_class_sub compound_stmt
    '''
    if len(p) == 4:
        if p[1] != 'sub':
            p[0] = { 'size' : p[3]['size'] }
        else :
            p[0] = { 'size' : 0 }    
    elif len(p) == 6 :
        if p[1] != 'sub':
            p[0] = { 'size' : p[3]['size'] + p[5]['size'] }
    else :
        p[0] = { 'size' : 0 }    
    # print ST.currentScope    
    if p[1] == 'sub':
        if len(p) != 5 :
            print ST.currentScope
            TAC[ST.currentScope].emit('ret','','','')
            ST.endDeclareSub()    
    else:        
        ST.insertIdentifier(p[1],idType=p[3]['type'],size=p[3]['size'])

def p_M_class_sub(p):
    '''M_class_sub : '''
    #TODO: Check if method is already declared in current scope    

    ST.declareSub(p[-1])
    print ST.currentScope
    TAC[ST.currentScope] = ThreeAddressCode.ThreeAddressCode()
    TAC[ST.currentScope].emit('label',ST.getSubLabel(),'','')

def p_M_class_end(p):
    '''M_class_end  :  ''' 
    TAC[ST.currentScope].emit('ret','','','')
    ST.endDeclareSub()     

#--- Hash declaration list for calling new instance of class
def p_struct_arg_hash(p):
    '''struct_arg_hash      : struct_arg_hash COMMA SUBROUTINE_ID KEY_VALUE arith_relat_exp 
                            |                       SUBROUTINE_ID KEY_VALUE arith_relat_exp
    '''
    if len(p) == 4:
        idName  = p[1]
        src     = p[3]['place']
    else:
        idName  = p[3]
        src     = p[5]['place']

    thisPtr   = p[-1]['place']
    className = p[-1]['target']
    offset    = ST.getIdOffset(idName,className)
    varPtr    = ST.createTemp()

    TAC[ST.currentScope].emit( '+',varPtr,thisPtr,offset,'' )
    TAC[ST.currentScope].emit( '*=',varPtr,src,'' )

def p_type_of_var(p):
    '''type_of_var          : DOLLAR
                            | AT
                            | MODULUS
                            | SUBROUTINE_ID                        
    '''
    if p[1] == '$':
        p[0] = {
                'type':  'scalar',
                'size': 4
            }
    elif p[1] == '@':
        p[0] = {
                'type':  'array',
                'size' : 400
            }
    elif p[1] == '%':
        p[0] = {
                'type':  'hash',
                'size': 400
            }
    else :
        p[0] = {
                'type':  'struct',
                'size':  ST.getAttribute(p[1][1:],'size')   
            }         

def p_primary_exp_struct(p):
    '''primary_exp          : SUBROUTINE_ID DEREFERENCE NEW OPEN_PAREN M_structAlloc struct_arg_hash CLOSE_PAREN
    '''
    p[0] = p[5]

def p_primary_exp_subroutine_struct(p):
    '''primary_exp          : SCALAR_ID DEREFERENCE SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN
    '''

    lhs_place = ST.createTemp()
    p[0] = {
        'place': lhs_place,
        'type': 'func'
    }

    # assert (ST.lookupIdentifier(p[1][1:]))
    lhs_place = ST.getAttribute(p[1][1:],'place')
    lhs_type = ST.getAttribute(p[1][1:],'type')
    lhs_target = ST.getAttribute(p[1][1:],'target')
        
    TAC[ST.currentScope].emit('param', lhs_place ,'','')
    if p[5] is not None:
        for param in p[5]['place']:
            TAC[ST.currentScope].emit('param',param,'','')

    idName = p[1][1:]
    idType = None

    if ST.lookupIdentifier(idName):
        idType = ST.getAttribute(idName,'type')
    # print idType    
    if idType == 'address':
        className   = ST.getAttribute(idName,'target') #p[1]['target']
        thisPtr     = ST.getAttribute(idName,'place') #p[1]['place']
        # offset      = ST.getIdOffset(p[3],className)
        varPtr      = ST.createTemp()
        # lhs_place   = ST.createTemp()
        lhs_type    = ST.table[className]['subroutines'][p[3]]['fullName']
        label_name = ST.table[lhs_type]['label']
        # lhs_size    = ST.table[className]['identifiers'][p[3]]['size']
        # print lhs_type, label_name


    TAC[ST.currentScope].emit('call',label_name,p[0]['place'],'')

def p_M_structAlloc(p):

    '''M_structAlloc :'''
    thisPtr   = ST.createTemp()
    classSize = ST.getClassSize(p[-4])

    p[0] = {
        'place' : thisPtr,
        'type'  : 'address',
        'target': p[-4]
    }
    TAC[ST.currentScope].emit( 'new',classSize,thisPtr,'' )

def p_object_var_deref(p): 
    '''scalar_indexer       : SCALAR_ID DEREFERENCE SUBROUTINE_ID
    '''
    #--- Example: $cat->furry
    #--- Note that this is only makes a copy of the data in $cat->furry
    #--- Hence, it will only be used in RHS of
    idName = p[1][1:]
    idType = None

    if ST.lookupIdentifier(idName):
        idType = ST.getAttribute(idName,'type')

    if idType == 'address':
        className   = ST.getAttribute(idName,'target') #p[1]['target']
        thisPtr     = ST.getAttribute(idName,'place') #p[1]['place']
        offset      = ST.getIdOffset(p[3],className)
        varPtr      = ST.createTemp()
        # lhs_place   = ST.createTemp()
        lhs_type    = ST.table[className]['identifiers'][p[3]]['type']
        lhs_size    = ST.table[className]['identifiers'][p[3]]['size']

        p[0] = {
            'place'     : varPtr,
            'type'      : lhs_type,
            'size'      : lhs_size,
            'deref'     : 'True',
        }

        TAC[ST.currentScope].emit( '+',varPtr,thisPtr,offset,'' )
        # TAC[ST.currentScope].emit( '=*',lhs_place,varPtr,'' )
    else:
        print "Error! Type:",idType," is not the pointer of the correct object!"
        assert(False)

def p_primary_exp_class_subroutine_call(p):
    '''primary_exp          : SUBROUTINE_ID DEREFERENCE SUBROUTINE_ID OPEN_PAREN array_decl_list  CLOSE_PAREN
                            | SUBROUTINE_ID DEREFERENCE SUBROUTINE_ID OPEN_PAREN hash_decl        CLOSE_PAREN
                            
    '''

#==============================================================================
# 'print' function implementation
#==============================================================================

def p_print_stmt(p):
    '''print_stmt       : PRINT print_list post_selection
                        | OPEN_PAREN PRINT print_list CLOSE_PAREN post_selection
    '''
    if len(p) == 4:
        ps_loc = 3
    else:
        ps_loc = 6
    if p[ps_loc] != None: #--- Post-selection
        if p[ps_loc]['cond'] == 'if':
            TAC[ST.currentScope].emit('ifgoto','eq',p[ps_loc]['exp_place'],'0',TAC[ST.currentScope].getNextQuad()+2)
        elif p[ps_loc]['cond'] == 'unless':
            TAC[ST.currentScope].emit('ifgoto','ne',p[ps_loc]['exp_place'],'0',TAC[ST.currentScope].getNextQuad()+2)

    if len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = p[3]

def p_print_list(p):
    '''print_list       : print_list print_sep arith_relat_exp
                        | arith_relat_exp
    '''
    if len(p) == 2:
        p[0] = p[1]
        TAC[ST.currentScope].emit('print',p[1]['place'],'','')
    else:
        p[0] = p[3]
    #TODO: Insert a blank space between prints list items
        TAC[ST.currentScope].emit('print',p[3]['place'],'','')

def p_print_sep(p):
    '''print_sep        : COMMA
    '''
    p[0] = p[1]

#==============================================================================
# Assignment and arithmetic-relational expressions
#==============================================================================

# defined for my $a; and my @a; local $a

def p_decl_list(p):
    '''decl_list            : OPEN_PAREN decl_var CLOSE_PAREN 
    '''

def p_decl_var(p):
    '''decl_var             : decl_var COMMA ARRAY_ID 
                            | decl_var COMMA HASH_ID
                            | decl_var COMMA SCALAR_ID
                            | ARRAY_ID
                            | HASH_ID
                            | SCALAR_ID
    ''' 
    p[0] = p[-2]

    if len(p) == 2:
        if not ST.lookupIdentifier(p[1][1:]):
            lhs_place = ST.createTemp()
            ST.insertIdentifier(p[1][1:],lhs_place,type_scope=p[-2],idType='scalar')
            p[0] = {
                'place' : lhs_place,
                'type' : 'scalar',
                'size' : 4,

            }
        else:
            lhs_place = ST.getAttribute(p[1][1:],'place')
            lhs_type = ST.getAttribute(p[1][1:],'type')
            lhs_type = ST.getAttribute(p[1][1:],'size')
            p[0] = {
                'place' : lhs_place,
                'type' : lhs_type,
                'size' : lhs_size
            }

# array_indexer ASSIGN SUBROUTINE_ID SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN added to support objects
                             
def p_assignment_exp_scalar(p):
    '''assignment_exp       : scalar_indexer  assignment_op     arith_relat_exp     post_selection
    '''

    post_label = TAC[ST.currentScope].makeLabel()
    lhs_place = None
    assignee_place = None

    if 'deref' in p[1]:
        lhs_place       = p[1]['place']
        assignee_place  = ST.createTemp()
    else:
        lhs_place = p[1]['place']
        assignee_place = p[1]['place']
    #--- Do not change this^
    temp            = ST.createTemp()
    src_place       = p[3]['place']

    if p[4] != None: #--- Post-selection
        # print p[4]
        if p[4]['cond'] == 'if':
            TAC[ST.currentScope].addPatchList(post_label)
            TAC[ST.currentScope].emit('ifgoto','eq',p[4]['exp_place'],'0',post_label)
        elif p[4]['cond'] == 'unless':
            TAC[ST.currentScope].addPatchList(post_label)
            TAC[ST.currentScope].emit('ifgoto','ne',p[4]['exp_place'],'0',post_label)

    if p[2] != "=":
        TAC[ST.currentScope].emit(p[2][0],assignee_place,assignee_place,src_place)
    else:
        if 'deref' in p[3]:
            TAC[ST.currentScope].emit('=*',temp,src_place,'')
            TAC[ST.currentScope].emit('=',src_place,temp,'')

        TAC[ST.currentScope].emit('=',assignee_place,src_place,'')
        
        if 'deref' in p[1]:
            TAC[ST.currentScope].emit('*=',lhs_place,assignee_place,'')

    if p[1]['type'] != p[3]['type']:
        for attr in p[3]:
            ST.addAttribute(p[1]['place'],attr,p[3][attr])

    TAC[ST.currentScope].placeLabel(post_label)
    p[0] = p[1]

def p_assignment_exp_array(p):
    '''assignment_exp       : array_indexer ASSIGN OPEN_PAREN array_decl_list CLOSE_PAREN 
    '''
    p[0] = {
        'type'  : 'array',
        'place' : p[1]['place']
    }
    for i,place in enumerate(p[4]['place']):
        TAC[ST.currentScope].emit('=',p[1]['place'] + '[' + str(i) + ']',place,'')

def p_assignment_hash_decl(p):
    '''assignment_exp       : hash_indexer  ASSIGN OPEN_PAREN hash_decl_list CLOSE_PAREN
                            | hash_indexer  ASSIGN OPEN_PAREN hash_decl      CLOSE_PAREN
    '''
    p[0] = {
        'type'  : 'hash',
        'place' : p[1]['place']
    }
    for place in p[4]['place']:
        TAC[ST.currentScope].emit('=',p[1]['place'] + '{' + place[0] + '}',place[1],'')

def p_assignment_exp_general(p):
    '''assignment_exp       : OPEN_PAREN      assignment_exp    CLOSE_PAREN

                            | array_indexer ASSIGN SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN
                            | hash_indexer  ASSIGN SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN
                            | array_indexer ASSIGN QW DIVIDE     string_list DIVIDE
                            | array_indexer ASSIGN QW OPEN_PAREN string_list CLOSE_PAREN
                            | array_indexer ASSIGN array_indexer
                            | hash_indexer  ASSIGN hash_indexer
                            | hash_indexer  ASSIGN array_indexer
                            | array_indexer ASSIGN hash_indexer
                            | array_indexer ASSIGN ARRAY_ID OPEN_BRACE array_decl_list CLOSE_BRACE
                            | array_indexer ASSIGN KEYS HASH_ID
                            | array_indexer ASSIGN VALUES HASH_ID

                            | type_scope M_TS SCALAR_ID assignment_op  arith_relat_exp
                            | type_scope M_TS ARRAY_ID ASSIGN OPEN_PAREN    array_decl_list CLOSE_PAREN 
                            | type_scope M_TS HASH_ID  ASSIGN OPEN_PAREN    array_decl_list CLOSE_PAREN
                            | type_scope M_TS ARRAY_ID ASSIGN SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN
                            | type_scope M_TS HASH_ID  ASSIGN SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN
                            | type_scope M_TS ARRAY_ID ASSIGN QW DIVIDE     string_list DIVIDE
                            | type_scope M_TS ARRAY_ID ASSIGN QW OPEN_PAREN string_list CLOSE_PAREN
                            | type_scope M_TS ARRAY_ID ASSIGN array_indexer
                            | type_scope M_TS HASH_ID  ASSIGN hash_indexer
                            | type_scope M_TS HASH_ID  ASSIGN array_indexer
                            | type_scope M_TS ARRAY_ID ASSIGN hash_indexer
                            | type_scope M_TS HASH_ID  ASSIGN OPEN_PAREN hash_decl CLOSE_PAREN
                            | type_scope M_TS ARRAY_ID ASSIGN ARRAY_ID OPEN_BRACE array_decl_list CLOSE_BRACE
                            | type_scope M_TS ARRAY_ID ASSIGN KEYS HASH_ID
                            | type_scope M_TS ARRAY_ID ASSIGN VALUES HASH_ID    
                            | type_scope M_TS OPEN_PAREN decl_list CLOSE_PAREN ASSIGN OPEN_PAREN array_decl_list CLOSE_PAREN
                            
                            | array_indexer ASSIGN SUBROUTINE_ID SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN
                            | hash_indexer  ASSIGN SUBROUTINE_ID SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN
                            | type_scope M_TS ARRAY_ID ASSIGN SUBROUTINE_ID SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN
                            | type_scope M_TS HASH_ID  ASSIGN SUBROUTINE_ID SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN    
    '''

def p_assignment_op(p):
    '''assignment_op        : ASSIGN
                            | PLUS_ASSIGN
                            | MINUS_ASSIGN  
                            | MULTIPLY_ASSIGN
                            | DIVIDE_ASSIGN         
                            | MOD_ASSIGN
                            | EXPONENT_ASSIGN
    '''
    p[0] = p[1]

def p_arith_relat_exp(p):
    '''arith_relat_exp      : arith_relat_exp PLUS      arith_relat_exp
                            | arith_relat_exp MINUS     arith_relat_exp
                            | arith_relat_exp MULTIPLY  arith_relat_exp
                            | arith_relat_exp DIVIDE    arith_relat_exp
                            | arith_relat_exp MODULUS   arith_relat_exp
                            | arith_relat_exp REPEAT    arith_relat_exp
                            | arith_relat_exp EXPONENT  arith_relat_exp
                            | arith_relat_exp BIT_AND   arith_relat_exp
                            | arith_relat_exp BIT_OR    arith_relat_exp
                            | arith_relat_exp BIT_XOR   arith_relat_exp
                            | arith_relat_exp XOR       arith_relat_exp
                            | arith_relat_exp RANGE     arith_relat_exp
                            | arith_relat_exp NOT       arith_relat_exp
                            | arith_relat_exp DOT       arith_relat_exp

                            | arith_relat_exp C_AND     M_sc arith_relat_exp
                            | arith_relat_exp C_OR      M_sc arith_relat_exp
                            | arith_relat_exp AND       M_sc arith_relat_exp
                            | arith_relat_exp OR        M_sc arith_relat_exp

                            | arith_relat_exp IS_EQUAL              arith_relat_exp
                            | arith_relat_exp IS_NOTEQUAL           arith_relat_exp
                            | arith_relat_exp IS_EQUALNOTEQUAL      arith_relat_exp
                            | arith_relat_exp EQ                    arith_relat_exp
                            | arith_relat_exp NE                    arith_relat_exp
                            | arith_relat_exp CMP                   arith_relat_exp
                            | arith_relat_exp GREATER_THAN          arith_relat_exp
                            | arith_relat_exp LESS_THAN             arith_relat_exp
                            | arith_relat_exp GREATER_THAN_EQUALTO  arith_relat_exp
                            | arith_relat_exp LESS_THAN_EQUALTO     arith_relat_exp
                            | arith_relat_exp GT                    arith_relat_exp
                            | arith_relat_exp LT                    arith_relat_exp
                            | arith_relat_exp GE                    arith_relat_exp
                            | arith_relat_exp LE                    arith_relat_exp
                            | arith_relat_exp BIT_LEFT_SHIFT        arith_relat_exp
                            | arith_relat_exp BIT_RIGHT_SHIFT       arith_relat_exp

                            | arith_relat_exp QUESTION_CONDITIONAL_OP arith_relat_exp COLON arith_relat_exp

                            | unary_exp
    '''
    if p[1]['type'] == 'array':
        temp = ST.createTemp()
        TAC[ST.currentScope].emit('=',temp,p[1]['place'],'')
        p[1]['place'] = temp

    if len(p) == 2:
        p[0] = p[1]
    
    elif len(p) >= 4:
        if p[3]['type'] == 'array':
            temp = ST.createTemp()
            TAC[ST.currentScope].emit('=',temp,p[3]['place'],'')
            p[3]['place'] = temp

        lhs_place = ST.createTemp()
        p[0] = {
            'place': lhs_place,
            'type':'NoType'

        }

        if p[2] == '+':
            TAC[ST.currentScope].emit('+',lhs_place,p[1]['place'],p[3]['place'])
        elif p[2] == '-':
            TAC[ST.currentScope].emit('-',lhs_place,p[1]['place'],p[3]['place'])
        elif p[2] == '*':
            TAC[ST.currentScope].emit('*',lhs_place,p[1]['place'],p[3]['place'])
        elif p[2] == '/':
            TAC[ST.currentScope].emit('/',lhs_place,p[1]['place'],p[3]['place'])
        elif p[2] == '%':
            TAC[ST.currentScope].emit('%',lhs_place,p[1]['place'],p[3]['place'])
        elif p[2] == '&':
            TAC[ST.currentScope].emit('&',lhs_place,p[1]['place'],p[3]['place'])
        elif p[2] == '|':
            TAC[ST.currentScope].emit('|',lhs_place,p[1]['place'],p[3]['place'])
        elif p[2] == '^':
            TAC[ST.currentScope].emit('^',lhs_place,p[1]['place'],p[3]['place'])


        elif p[2] in ['>','gt']:
            TAC[ST.currentScope].emit('=',lhs_place,1,'')
            TAC[ST.currentScope].emit('ifgoto','gt',p[1]['place'],p[3]['place'],TAC[ST.currentScope].getNextQuad()+2)
            TAC[ST.currentScope].emit('=',lhs_place,0,'')
        elif p[2] in ['<','lt']:
            TAC[ST.currentScope].emit('=',lhs_place,1,'')
            TAC[ST.currentScope].emit('ifgoto','lt',p[1]['place'],p[3]['place'],TAC[ST.currentScope].getNextQuad()+2)
            TAC[ST.currentScope].emit('=',lhs_place,0,'')
        elif p[2] in ['<=','le']:
            TAC[ST.currentScope].emit('=',lhs_place,1,'')
            TAC[ST.currentScope].emit('ifgoto','leq',p[1]['place'],p[3]['place'],TAC[ST.currentScope].getNextQuad()+2)
            TAC[ST.currentScope].emit('=',lhs_place,0,'')
        elif p[2] in ['>=','ge']:
            TAC[ST.currentScope].emit('=',lhs_place,1,'')
            TAC[ST.currentScope].emit('ifgoto','geq',p[1]['place'],p[3]['place'],TAC[ST.currentScope].getNextQuad()+2)
            TAC[ST.currentScope].emit('=',lhs_place,0,'')
        elif p[2] in ['==','eq']:
            TAC[ST.currentScope].emit('=',lhs_place,1,'')
            TAC[ST.currentScope].emit('ifgoto','eq',p[1]['place'],p[3]['place'],TAC[ST.currentScope].getNextQuad()+2)
            TAC[ST.currentScope].emit('=',lhs_place,0,'')
        elif p[2] in ['!=','ne']:
            TAC[ST.currentScope].emit('=',lhs_place,1,'')
            TAC[ST.currentScope].emit('ifgoto','ne',p[1]['place'],p[3]['place'],TAC[ST.currentScope].getNextQuad()+2)
            TAC[ST.currentScope].emit('=',lhs_place,0,'')

        elif p[2] == '**':
            base       = p[1]['place']
            exponent   = ST.createTemp()
            tMul       = ST.createTemp()

            TAC[ST.currentScope].emit('=',tMul       ,'1','')
            TAC[ST.currentScope].emit('=',exponent   ,p[3]['place'],'')

            TAC[ST.currentScope].emit('ifgoto','leq',exponent,'0',TAC[ST.currentScope].getNextQuad()+4)
            TAC[ST.currentScope].emit('*',tMul,tMul,base)
            TAC[ST.currentScope].emit('-',exponent,exponent,'1')
            TAC[ST.currentScope].emit('goto',TAC[ST.currentScope].getNextQuad()-3,'','')

            TAC[ST.currentScope].emit('=',lhs_place,tMul,'')

        elif p[2] in ["&&","and"]:
            TAC[ST.currentScope].emit('ifgoto','eq',p[4]['place'],'0',TAC[ST.currentScope].getNextQuad()+3)
            TAC[ST.currentScope].emit('=',lhs_place,'1','','')
            TAC[ST.currentScope].emit('goto',TAC[ST.currentScope].getNextQuad()+2,'','')
            TAC[ST.currentScope].placeLabel(p[3]['label'])
            TAC[ST.currentScope].emit('=',lhs_place,'0','')
        elif p[2] in ["||","or"]:
            TAC[ST.currentScope].emit('ifgoto','ne',p[4]['place'],'0',TAC[ST.currentScope].getNextQuad()+3)
            TAC[ST.currentScope].emit('=',lhs_place,'0','','')
            TAC[ST.currentScope].emit('goto',TAC[ST.currentScope].getNextQuad()+2,'','')
            TAC[ST.currentScope].placeLabel(p[3]['label'])
            TAC[ST.currentScope].emit('=',lhs_place,'1','')

def p_M_sc(p):
    '''M_sc :'''
    scLabel = TAC[ST.currentScope].makeLabel()
    p[0] = { 
        'label' : scLabel,
        'type' : 'marker_label' 
    }

    #--- Short circuiting of evaluation of AND,OR
    TAC[ST.currentScope].addPatchList(scLabel)
    if p[-1] in ["&&","and"]:
        TAC[ST.currentScope].emit('ifgoto','eq',p[-2]['place'],'0',scLabel)
    elif p[-1] in ["||","or"]:
        TAC[ST.currentScope].emit('ifgoto','ne',p[-2]['place'],'0',scLabel)

#==============================================================================
# Fundamental expressions
#==============================================================================

#--- Unary Expression may be preceded by a number of unary operators 
def p_unary_exp(p):
    '''unary_exp            : postfix_exp
                            | unary_operator postfix_exp
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        #--- NOTE: Unary operators ++,-- are first applied then postfix_exp is assigned to lhs
        lhs_place = ST.createTemp()
        p[0] = p[2]
        p[0]['place'] = lhs_place
        # p[0] = {
        #     'place' : lhs_place,
        #     'type' : p[2]['type']
        # }

        if p[1] == '-':
            TAC[ST.currentScope].emit('-',lhs_place,'0',p[2]['place'])
        elif p[1] in ['++','--']:  #--- Please note the order of operations.
            TAC[ST.currentScope].emit(p[1][0],p[2]['place'],p[2]['place'],'1')
            TAC[ST.currentScope].emit('=',lhs_place,p[2]['place'],'')

        elif p[1] == "\\":
            p[0] = {
                'place'     : lhs_place,
                'size'      : 4,
                'type'      : 'address',
                'target'    : p[2]['type']
            }
            TAC[ST.currentScope].emit('=&',lhs_place,p[2]['place'],'')

def p_unary_operator(p):
    '''unary_operator       : PLUS
                            | MINUS
                            | AUTO_INC
                            | AUTO_DEC
                            | BIT_NOT
                            | BIT_COMPLEMENT
                            | SLASH
                            | SCALAR
    '''
    p[0] = p[1]

def p_postfix_exp(p):
    '''postfix_exp          : primary_exp
                            | primary_exp AUTO_INC
                            | primary_exp AUTO_DEC
    '''
    p[0] = p[1]
    if len(p) == 3:   #--- Emits '+' or '-' according to AUTO_INC or AUTO_DEC
        lhs_place = ST.createTemp()
        p[0]['place'] = lhs_place
        # p[0] = {
        #     'place' : lhs_place,
        #     'type' : p[1]['type']
        # }
        #--- NOTE: POST Increment i.e. primary_exp is incremented after assignment to lhs_place
        TAC[ST.currentScope].emit('=',lhs_place,p[1]['place'],'')
        TAC[ST.currentScope].emit(p[2][0],p[1]['place'],p[1]['place'],'1')

#--- SUBROUTING_ID --> Function return value
#--- SLASH BIT_AND SUB... --> Address of function
def p_primary_exp_literal(p):
    '''primary_exp          : INTEGER
                            | FLOAT
                            | OCTAL
                            | HEX
                            | STRING
    '''
    lhs_place = ST.createTemp()
    p[0] = {
        'place': lhs_place,
        'type' : 'scalar',
        'size' : 4
        # 'value': p[1]
    }
    TAC[ST.currentScope].emit('=',lhs_place,p[1],'')

def p_primary_exp_indexer(p):
    '''primary_exp          : scalar_indexer
                            | array_indexer
                            | hash_indexer
                            | OPEN_PAREN arith_relat_exp CLOSE_PAREN
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

def p_primary_exp_subroutine_call(p):
    '''primary_exp          : SUBROUTINE_ID OPEN_PAREN array_decl_list  CLOSE_PAREN
                            | SUBROUTINE_ID OPEN_PAREN hash_decl        CLOSE_PAREN

    '''
    lhs_place = ST.createTemp()
    p[0] = {
        'place': lhs_place,
        'type': 'func',
        'size': 4
    }
    if p[3] is not None:
        for param in p[3]['place']:
            TAC[ST.currentScope].emit('param',param,'','')
    TAC[ST.currentScope].emit('call',ST.lookupSub(p[1]),p[0]['place'],'')




def p_primary_exp_misc(p):
    '''primary_exp          : QW DIVIDE string_list DIVIDE
                            | QW OPEN_PAREN string_list CLOSE_PAREN
                            | array_op_exp
                            | KEYS HASH_ID
                            | VALUES HASH_ID
                            | EXISTS OPEN_PAREN SCALAR_ID OPEN_BRACE arith_relat_exp CLOSE_BRACE CLOSE_PAREN
                            | DELETE SCALAR_ID  OPEN_BRACE     arith_relat_exp CLOSE_BRACE
                            | DELETE SCALAR_ID  OPEN_SBRACKET  arith_relat_exp CLOSE_SBRACKET
                            | DELETE ARRAY_ID   OPEN_SBRACKET  array_decl_list CLOSE_SBRACKET
                            | DELETE ARGUMENT_SCALAR_ID OPEN_SBRACKET   arith_relat_exp CLOSE_SBRACKET 
                            | SUBROUTINE_ID SUBROUTINE_ID OPEN_PAREN array_decl_list CLOSE_PAREN
    '''
    if len(p) == 2:
        p[0] = p[1]
    # print p[0]

#--- added open_paren and close_paren around each of the expr, like in push expr, added a rule push (expr), 
def p_array_op_exp(p):
    '''array_op_exp         : PUSH      ARRAY_ID    COMMA OPEN_PAREN array_decl_list CLOSE_PAREN
                            | PUSH      OPEN_PAREN  ARRAY_ID COMMA OPEN_PAREN array_decl_list CLOSE_PAREN CLOSE_PAREN
                            | POP       ARRAY_ID
                            | POP       OPEN_PAREN  ARRAY_ID CLOSE_PAREN
                            | SHIFT     array_indexer
                            | SHIFT     OPEN_PAREN  array_indexer CLOSE_PAREN
                            | UNSHIFT   array_indexer COMMA OPEN_PAREN array_decl_list CLOSE_PAREN
                            | UNSHIFT   OPEN_PAREN  ARRAY_ID COMMA OPEN_PAREN array_decl_list CLOSE_PAREN CLOSE_PAREN
                            | UNSHIFT   OPEN_PAREN  ARRAY_ID CLOSE_PAREN COMMA OPEN_PAREN array_decl_list CLOSE_PAREN
                            | UNSHIFT   OPEN_PAREN  OPEN_PAREN ARRAY_ID CLOSE_PAREN COMMA OPEN_PAREN array_decl_list CLOSE_PAREN CLOSE_PAREN
                            | SPLICE    OPEN_PAREN  ARRAY_ID COMMA primary_exp COMMA primary_exp COMMA array_decl_list CLOSE_PAREN
    '''

def p_array_decl_list(p):
    '''array_decl_list      : arith_relat_exp
                            | arith_relat_exp COMMA array_decl_list
                            |
    '''
    if len(p) == 2:
        p[0] = { 'place' : [p[1]['place']] }
    elif len(p) == 4:
        p[0]['place'] += p[3]['place']

def p_string_list(p):
    '''string_list          : SUBROUTINE_ID string_list
                            | INTEGER       string_list
                            | FLOAT         string_list
                            | OCTAL         string_list
                            | HEX           string_list
                            | 
    '''

def p_type_scope(p):
    '''type_scope           : MY
                            | LOCAL
                            | STATE
    '''         
    p[0] = p[1]

def p_M_TS(p):
    '''M_TS :'''
    p[0] = p[-1]

#--- Scalar indexer produces a scalar which is either:
#--- $a, $a[ ] or $a{ } according their respective identifier type
def p_scalar_indexer(p):
    '''scalar_indexer       : SCALAR_ID
                            | ARGUMENT_SCALAR_ID
                            | ARGUMENT_SCALAR_ID OPEN_SBRACKET   arith_relat_exp CLOSE_SBRACKET
                            | ARGUMENT_ARRAY_ID OPEN_SBRACKET   arith_relat_exp CLOSE_SBRACKET
    '''    
    if len(p) == 2:
        if not ST.lookupIdentifier(p[1][1:]):
            lhs_place = ST.createTemp()
            ST.insertIdentifier(p[1][1:],lhs_place,type_scope=p[-1],idType='scalar')
            p[0] = {
                'place' : lhs_place,
                'type' : 'scalar'
            }
        else:
            lhs_place = ST.getAttribute(p[1][1:],'place')
            lhs_type = ST.getAttribute(p[1][1:],'type')
            p[0] = {
                'place' : lhs_place,
                'type' : lhs_type
            }
    elif len(p) == 5:
        if p[1] == '@_':
            p[0] = {}
            lhs_place = ST.createTemp()
            p[0]['place'] = lhs_place
            p[0]['type'] = 'scalar'
            TAC[ST.currentScope].emit('=',p[0]['place'],'param' + '[' + p[3]['place'] + ']','')
        else:
            if not ST.lookupIdentifier(p[1][1:]):
                lhs_place = ST.createTemp()
                ST.insertIdentifier(p[1][1:],lhs_place,idType='array')
                p[0] = {
                    'place' : lhs_place,
                    'type' : 'array'
                }
            else:
                lhs_place = ST.table[ST.lookupScope(p[1][1:])]['identifiers'][p[1][1:]]['place']
                lhs_type = 'array'
                p[0] = {
                    'place' : lhs_place,
                    'type' : lhs_type
                }
            p[0]['place'] = lhs_place + '[' + p[3]['place'] + ']'

def p_scalar_indexer_deref(p):
    '''scalar_indexer       : DEREFERENCE_OPEN      scalar_indexer  CLOSE_BRACE
                            | SCALAR_ID OPEN_BRACE  arith_relat_exp CLOSE_BRACE
                            | SCALAR_ID DEREFERENCE OPEN_SBRACKET   arith_relat_exp CLOSE_SBRACKET
                            | SCALAR_ID DEREFERENCE OPEN_BRACE      arith_relat_exp CLOSE_BRACE
    '''
    lhs_place = ST.createTemp()
    p[0] = { 'place' : lhs_place }

    if len(p) == 4:
        p[0]['type'] = p[2]['type']
        TAC[ST.currentScope].emit('=*',lhs_place,p[2]['place'],'')
    elif len(p) is 6:
        if not ST.lookupIdentifier(p[1][1:]):
            print "ERROR! Cannot dereference undefined address."
        else:
            id_place = ST.getAttribute(p[1][1:],'place')
            p[0]['type'] = ST.getAttribute(p[1][1:],'types')
            addr_temp = ST.createTemp()
            TAC[ST.currentScope].emit('+',addr_temp,id_place,p[4]['place'])
            TAC[ST.currentScope].emit('=*',lhs_place,addr_temp,'')

def p_scalar_indexer_array_index(p):
    '''scalar_indexer       : SCALAR_ID         OPEN_SBRACKET   arith_relat_exp CLOSE_SBRACKET
    '''
    if not ST.lookupIdentifier(p[1][1:]):
        lhs_place = ST.createTemp()
        ST.insertIdentifier(p[1][1:],lhs_place,idType='array')
        p[0] = {
            'place' : lhs_place,
            'type' : 'array'
        }
    else:
        lhs_place = ST.table[ST.lookupScope(p[1][1:])]['identifiers'][p[1][1:]]['place']
        lhs_type = 'array'
        p[0] = {
            'place' : lhs_place,
            'type' : lhs_type
        }
    p[0]['place'] = lhs_place + '[' + p[3]['place'] + ']'

def p_array_indexer(p):
    '''array_indexer        : ARRAY_ID
                            | ARRAY_ID OPEN_SBRACKET array_decl_list CLOSE_SBRACKET
                            | DEREFERENCE_OPEN array_indexer CLOSE_BRACE  
                            | ARGUMENT_ARRAY_ID
    '''
    if len(p) == 2:
        if not ST.lookupIdentifier(p[1][1:]):
            lhs_place = ST.createTemp()
            ST.insertIdentifier(p[1][1:],lhs_place,idType='array')
            p[0] = {
                'place' : lhs_place,
                'type' : 'array',
            }
        else:
            lhs_place = ST.getAttribute(p[1][1:],'place')
            lhs_type = ST.getAttribute(p[1][1:],'type')
            p[0] = {
                'place' : lhs_place,
                'type' : lhs_type,
            }

def p_hash_indexer(p):
    '''hash_indexer         : HASH_ID
                            | HASH_ID OPEN_BRACE    arith_relat_exp CLOSE_BRACE
                            | HASH_ID OPEN_BRACE    SUBROUTINE_ID   CLOSE_BRACE
    '''
    idName = p[1][1:]
    if not ST.lookupIdentifier(idName):
        lhs_place = ST.createTemp()
        lhs_type = 'hash'
        ST.insertIdentifier(idName,lhs_place,idType='hash')
    else:
        lhs_place = ST.getAttribute(idName,'place')
        lhs_type = ST.getAttribute(idName,'type')
    p[0] = {
        'place' : lhs_place,
        'type' : lhs_type,
    }
    if len(p) == 5:
        p[0]['place'] = lhs_place + '{' + p[3]['place'] + '}'
            
def p_hash_decl(p):
    '''hash_decl            : arith_relat_exp KEY_VALUE arith_relat_exp COMMA hash_decl
                            | arith_relat_exp KEY_VALUE arith_relat_exp
    '''
    p[0] = { 'place' : [(p[1]['place'],p[3]['place'])] }
    if len(p) == 6:
        p[0]['place'] += p[5]['place']

def p_hash_decl_list(p):
    '''hash_decl_list       : arith_relat_exp COMMA arith_relat_exp COMMA hash_decl_list
                            | arith_relat_exp COMMA arith_relat_exp
    '''
    p[0] = { 'place' : [(p[1]['place'],p[3]['place'])] }
    if len(p) == 6:
        p[0]['place'] += p[5]['place']

#--- Syntax error rule
def p_error(p):
    global ErrorFound
    ErrorFound = True
    if not p:
        print "Syntax arror at EOF"
    else:
        print "Syntax error! "
        print ("At %s '%s' at line number: %s")%(p.type,p.value,p.lineno)
        # print "</br>"
        while True:
            tok = parser.token()    # Next token
            if not tok or tok.type == 'SEMICOLON':
                break
        parser.restart()

#==============================================================================
# Precedence Rules
#==============================================================================

precedence = (
    ('left','OR','XOR'),
    ('left','AND'),
    ('right','NOT'),
    ('right','QUESTION_CONDITIONAL_OP','COLON'),
    ('nonassoc','RANGE'),       # RANGE is '..'
    ('left','C_OR'),
    ('left','C_AND'),
    ('left','BIT_OR','BIT_XOR'),
    ('left','BIT_AND'),
    ('nonassoc','IS_EQUAL','IS_NOTEQUAL','IS_EQUALNOTEQUAL','EQ','NE','CMP'),
    ('left','LESS_THAN','GREATER_THAN','LESS_THAN_EQUALTO','GREATER_THAN_EQUALTO','LT','GT','LE','GE'),
    ('left','BIT_LEFT_SHIFT','BIT_RIGHT_SHIFT'),
    ('left','PLUS','MINUS','DOT'),
    ('left','MULTIPLY','DIVIDE','MODULUS','REPEAT'),
    ('left','BIT_NOT','BIT_COMPLEMENT',),
    ('left','EXPONENT'),
    ('nonassoc','AUTO_DEC','AUTO_INC'),
    ('left','DEREFERENCE'),
)

#==============================================================================
# End of Perl grammar
#==============================================================================

ST = SymbolTable.SymbolTable(debug='i')
TAC = {}
TAC[ST.currentScope] = ThreeAddressCode.ThreeAddressCode()
parser = yacc.yacc()

with open(sys.argv[1],'r') as file:
    raw = file.read()
    result = parser.parse(raw)
    if len(sys.argv) > 2:
        option = int(sys.argv[2])
    else:
        option = 0

    if option > 0:
        print "ThreeAddressCode :"
    quad = TAC['main'].printCode(1)
    for tac in TAC.keys():
        if tac != 'main':
            quad = TAC[tac].printCode(quad)

    if option > 0:
        pp = pprint.PrettyPrinter(indent=4)
        print "\nSymbol Table :"
        pp.pprint(ST.table)
