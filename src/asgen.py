#!/usr/bin/python

import sys

class AssCodeGen:

    def __init__(self,tac_file):
        self.reg = {
            '%eax': 0,
            '%ebx': 0,
            '%ecx': 0,
            '%edx': 0,
            '%esi': 0,
            '%edi': 0,
        }
        self.bitops = {
            '&' : "andl",
            '|' : "orl",
            '^' : "xorl"
        }
        self.shiftop = {
            '>>': "shrl",
            '<<': "shll"
        }
        self.function_leaders = []  
        self.function_blocks = []
        self.pointers = {}
        self.tac_file = tac_file
        self.instr_set = self.read_tac(self.tac_file)
        self.variable_list,self.variable_dict = self.extract_variables(self.instr_set)
        self.function_list = self.extract_functions(self.instr_set)
        self.params = 0
        self.setup_data_region()
        self.basic_blocks = self.make_basic_blocks(self.instr_set)
        self.next_use = self.evaluate_next_uses(self.basic_blocks)
        self.add_desc = {}
        self.context = {}
        self.label = {}
        self.label[0] = 0
        # print "LEADERS:"
        # print self.leaders

    def extract_variables(self,instr_set):          # Function for extracting all variables in the 3AC code
        variables = []
        variable_dict = {}
        for instr in instr_set:
            if instr[1] in ['=','+','-','*','/','%','=&','*=','=*'] + self.bitops.keys() + self.shiftop.keys():
                if '[' in instr[2]:
                    variable_dict[instr[2]] = 'array'
                    variable_dict[instr[2][:instr[2].index('[')]] = 'array'
                    variables.append(instr[2][:instr[2].index('[')])
                elif '{' in instr[2]:
                    variable_dict[instr[2]] = 'hash'
                    variable_dict[instr[2][:instr[2].index('{')]] = 'hash'
                    variables.append(instr[2][:instr[2].index('{')])
                elif instr[3].isdigit():
                    variable_dict[instr[2]] = 'int'
                    variables.append(instr[2])
                elif instr[3][0] in ['"',"'"]:
                    variable_dict[instr[2]] = instr[3]
                    variables.append(instr[2])
                elif '.' in instr[3]:
                    variable_dict[instr[2]] = 'float'
                    variables.append(instr[2])
                # elif instr[3] in variable_dict.keys():
                #     if variable_dict[instr[3]] == 'pointer':
                #         variable_dict[instr[2]] = 'pointer'
                #         self.pointers[instr[2]] = 0
                #         print instr[2]
                else:
                    variable_dict[instr[2]] = 'int'
                    variables.append(instr[2])
            elif instr[1] in ['scan']:
            	variable_dict[instr[2]] = 'int'
            	variables.append(instr[2])
            elif instr[1] == 'new':
                variable_dict[instr[3]] = 'pointer'
                variables.append(instr[3])
                self.pointers[instr[3]] = instr[2]
            elif instr[1] == 'call':
                try:
                    variables.append(instr[3])
                    variable_dict[instr[3]] = 'int'
                except IndexError:
                    pass
            if instr[1] == '=&':
                self.pointers[instr[2]] = instr[3]
            if instr[1] == '=' and instr[3] in self.pointers.keys():
                self.pointers[instr[2]] = self.pointers[instr[3]]       # Storing where does a particular pointer point
        variables.append('param')
        variable_dict['param'] = 'array'
        variables = list(set(variables))
        return variables,variable_dict

    def extract_functions(self,instr_set):         # Function for extracting all functions defined in the 3AC code
        functions = []
        for instr in instr_set:
            if instr[1] == 'call':
                functions.append(instr[2])
        functions = list(set(functions))
        return functions

    def evaluate_next_uses(self,basic_blocks):      # Function for making next_use data structure at every program point
        next_use = {}
        for instr in self.instr_set:
            next_use[instr[0]] = {}
            for variable in self.variable_list:
                next_use[instr[0]][variable] = 0
        next_use[len(self.instr_set)+1] = {}
        for variable in self.variable_list:
            next_use[len(self.instr_set)+1][variable] = 0
        for i,block in enumerate(basic_blocks):
            for index,instr in enumerate(reversed(block)):
                if index != 0:                                  # Assigning next use of all variables to their values in next program point in the basic block 
                    for variable in self.variable_list:
                        next_use[instr[0]][variable] = next_use[instr[0]+1][variable]
                if instr[1] == '=':
                    next_use[instr[0]][instr[2]] = 0
                if instr[1] in ['=','+','-','*','/','%'] + self.bitops.keys() + ['ifgoto'] + self.shiftop.keys():
                    if instr[3] in self.variable_list:
                        next_use[instr[0]][instr[3]] = instr[0]
                    try:
                        if instr[4] in self.variable_list:
                            next_use[instr[0]][instr[4]] = instr[0]
                    except IndexError:
                        pass
        return next_use

    def setup_data_region(self):                # Setting up data regions with all variables and required strings
        print "#include <stdio.h>"
        print ".section .data"
        print
        print "output_string: .asciz \"%d\\n\""
        print "print_string: .asciz \"%s\\n\""
        print "input_string: .asciz \"%d\""
        print
        print "scan: .asciz \"Enter Value: \""
        print
        for variable in self.variable_list:
            if self.variable_dict[variable] not in ['int','array','hash','pointer']:
                print variable + ":    .asciz " + self.variable_dict[variable]
            elif self.variable_dict[variable] == 'array':
                if '[' in variable:
                    print variable[:variable.index('[')] + ":",
                else:
                    print variable + ":",
                print "   .space 400"
            # elif self.variable_dict[variable] == 'pointer':
            #     print "%s    .space %s"%(variable,self.pointers[variable])
            else:
                print variable + ":",
                print "   .int 0"
        print
        print ".section .text"
        print
        print ".globl _start"
        print
        
    def spillreg(self,reg):                                    # Spilling a register
        print "    movl " + reg + ", " + self.reg[reg]
        var = self.reg[reg]
        self.reg[reg] = 0
        try:
            del self.add_desc[var] 
        except KeyError:
            pass
        return 

    def getregx(self,lineno,x,y):           # Getreg function for variable x in x = y op z
        if y in self.variable_list and y in self.add_desc.keys() and self.next_use[lineno+1][y] == 0:       # Flag=1 if we assign register of y to x if this condition is true
            return self.add_desc[y],1
        else:   
            for reg, taken in self.reg.items():
                if taken == 0:
                    break
            if taken == 0:
                self.add_desc[x] = reg
                self.reg[reg] = x
                return reg,2                        #  Flag=2 if an empty register is found
            if self.next_use[lineno+1][x] != 0:         
                var = min(self.next_use[lineno], key = self.next_use[lineno].get)       # Pick register of a variable which is not live in current basic block
                if self.next_use[lineno][var] != 0 or var not in self.reg.values():     # If no such register, then pick the one with highest next use
                    sorted_last_use = sorted(self.next_use[lineno], key=self.next_use[lineno].get)
                    for var in reversed(sorted_last_use):
                        if var in self.reg.values():
                            break
                reg = self.add_desc[var]
                self.spillreg(reg)
                self.add_desc[x] = reg
                self.reg[self.add_desc[x]] = x
                return self.add_desc[x],3       # flag=3 if variable with furthest next use if spilled and its register is returned
            else:                          
                return x,4                   # Returning memory address itself if x has no further use (flag=4 in this case)

    def getreg(self,y):             # getreg function for y or z in x = y op z
        for reg, taken in self.reg.items():
            if taken == 0:
                break
        if taken == 0:
            self.add_desc[y] = reg
            self.reg[reg] = y
            print "    movl " + y + ", " + reg
            return reg                          # Returning an empty register if found
        return y                                # Otherwise returning the memory location

    def getregforced(self,y,instr):
        for reg,taken in self.reg.items():                  # In the index of array cannot be a constant, hence a register has to be assigned to it
            if taken == 0:   # Returning an empty register
                break
        if taken != 0:
            sorted_last_use = sorted(self.next_use[instr[0]], key=self.next_use[instr[0]].get)      # If no empty register found, then spilling the furthest use variable
            for furthest_use in reversed(sorted_last_use):
                if furthest_use in self.reg.values():
                    break
            reg = self.add_desc[furthest_use]
            self.spillreg(reg)
        self.add_desc[y] = reg
        self.reg[reg] = y
        return reg

    def make_basic_blocks(self,instr_set):      # Function for separating basic blocks from the instruction set
        self.leaders = [1]
        flag = 1
        for i,instr in enumerate(instr_set):
            if instr[1] == 'ifgoto' or instr[1] == 'goto':
                self.leaders.append(int(instr[-1]))
                self.leaders.append(i+2)
                if flag == 0:
                    self.function_leaders.append(int(instr[-1]))
                    self.function_leaders.append(i+2)
            elif instr[1] == 'call':
                self.leaders.append(i+2)
                if flag == 0:
                    self.function_leaders.append(i+2)
            elif instr[1] == 'label':
                flag = 0
                self.leaders.append(i+1)

        self.leaders.append(len(instr_set)+1)
        self.leaders = list(set(self.leaders))
        self.leaders.sort()
        if flag == 0:                           # Extracting basic blocks of functions separately since they are to be print before the main function's basic blocks
            self.function_leaders.append(len(instr_set)+1)
            self.function_leaders = list(set(self.function_leaders))
            self.function_leaders.sort()
        basic_blocks = []
        for i in range(len(self.leaders)-1):    
            basic_blocks.append(instr_set[self.leaders[i]-1:self.leaders[i+1]-1])
            if self.leaders[i] in self.function_leaders:
                self.function_blocks.append(instr_set[self.leaders[i]-1:self.leaders[i+1]-1])
        return basic_blocks
    
    def read_tac(self,filename):            # Reading the 3AC file and separating all the instructions
        f = open(filename, 'r')
        instr_set = f.readlines()
        instructions =  []
        for line in instr_set:
            instr = "".join(line.split())
            instr = instr.split(",")
            instr[0] = int(instr[0])
            instructions.append(instr)
        return instructions
        
    def emit_code(self):                    # This function assigns labels to all the basic blocks, and print assembly code per basic block
        for block in self.basic_blocks:
            if block[0][0] in self.leaders:
                label = max(self.label.values()) + 1
                self.label[block[0][0]] = label
        for block in self.basic_blocks:         # First printng basic blocks of all functions except main
            if block[0][1] == 'label':
                for i,fblock in enumerate(self.basic_blocks[self.basic_blocks.index(block):]):
                    self.emit_block_code(fblock)
                    if fblock[-1][1] == 'ret' and i+1 < len(self.basic_blocks[self.basic_blocks.index(block):]) and self.basic_blocks[self.basic_blocks.index(block):][i+1][0][1] != 'ret': 
                        break
                continue         
        print "_start:"
        # while True:
        #     pass
        for var,types in self.variable_dict.iteritems():
            if types == 'hash' and '{' not in var:
                print "    call createHash"
                print "    movl %eax, " + var

        for block in self.basic_blocks:
            if block[0][1] == 'label' or block in self.function_blocks: 
                continue
            self.emit_block_code(block)             # Printing basic blocks of main function
        print
        print "    movl $1, %eax        # Exit system call"
        print "    movl $0, %ebx"
        print "    int $0x80"

    def emit_block_code(self,block):
        if block[0][0] in self.leaders:
            if block[0][1] != 'label':          # Printing label of the basic block before its assembly code
                print
                print "L" + str(self.label[block[0][0]]) + ":"

        for reg in self.reg.keys():
            self.reg[reg] = 0
        self.add_desc = {}

        for instr in block:
            if instr[1] == 'exit':
                print "    movl $1, %eax        # Exit system call"
                print "    movl $0, %ebx"
                print "    int $0x80"
            elif instr[1] == '=' and instr[2] != instr[3]:

                if self.variable_dict[instr[2]] not in ['int','hash','array','pointer']:
                    pass
                elif '[' in instr[2]:
                    if instr[2][:instr[2].index('[')] not in self.add_desc.keys():
                        reg = self.getregforced(instr[2][:instr[2].index('[')],instr)
                        print "    movl $" + instr[2][:instr[2].index('[')] + ", " + reg
                        self.reg[reg] = instr[2][:instr[2].index('[')]
                        self.add_desc[instr[2][:instr[2].index('[')]] = reg
                    try:
                        reg = self.add_desc[instr[2][instr[2].index('[')+1:-1]]
                    except KeyError:
                        if instr[2][instr[2].index('[')+1:-1] in self.variable_list:
                            reg = self.getregforced(instr[2][instr[2].index('[')+1:-1],instr)
                            print "    movl " + instr[2][instr[2].index('[')+1:-1] + ", " + reg
                        else:
                            print "    movl $" + instr[2][instr[2].index('[')+1:-1] + ", " + reg
                        self.reg[reg] = 0
                    if instr[3] in self.variable_list:
                        try:
                            instr[3] = self.add_desc[instr[3]]
                        except KeyError:
                            instr[3] = self.getregforced(instr[3],instr)
                    else:
                    	instr[3] = '$' + instr[3]
                    print "    movl %s, (%s,%s,4) " % (instr[3],self.add_desc[instr[2][:instr[2].index('[')]],reg)

                elif '[' in instr[3]:
                    if instr[2] in self.variable_list:
                    	try:
                    		instr[2] = self.add_desc[instr[2]]
                    	except KeyError:
                            instr[2] = self.getregforced(instr[2],instr)
                    else:
                    	instr[2] = '$' + instr[2]
                    #print 'a',self.add_desc,self.reg
                    if 'param' in instr[3]:
                        self.add_desc['param'] = '%ebp'
                    else:
	                    if instr[3][:instr[3].index('[')] not in self.add_desc.keys():
	                        self.getregforced(instr[3][:instr[3].index('[')],instr)
                    try:
                        reg = self.add_desc[instr[3][instr[3].index('[')+1:-1]]
                    except KeyError:
                        if instr[3][instr[3].index('[')+1:-1] in self.variable_list:
                            reg = self.getregforced(instr[3][instr[3].index('[')+1:-1],instr)
                            print "    movl " + instr[3][instr[3].index('[')+1:-1] + ", " + reg
                        else:
                            print "    movl $" + instr[3][instr[3].index('[')+1:-1] + ", " + reg
                    print "    movl (%s,%s,4), %s"%(self.add_desc[instr[3][:instr[3].index('[')]],reg,instr[2])
                    self.reg[reg] = 0
                    del self.add_desc[instr[3][instr[3].index('[')+1:-1]]
                    
                else:
                    try:
                        dest,flag = self.add_desc[instr[2]],0
                    except KeyError:
                        dest,flag = self.getregx(instr[0],instr[2],instr[3])
                        if flag == 1:
                            reg = self.add_desc[instr[3]]
                            #print reg,self.reg[reg]
                            self.spillreg(reg)              # Spilling out variable y since it has no next use if flag=1
                            self.add_desc[instr[2]] = reg
                            self.reg[self.add_desc[instr[2]]] = instr[2]
                            #print self.reg,self.add_desc,'d'
                            continue
                    #print flag,'c'
                    if instr[3] in self.variable_list:       # Else in all cases move y into register of x
                        if instr[3] in self.add_desc.keys():
                            print "    movl " + self.add_desc[instr[3]] + ", " + dest
                        else:
                            print "    movl " + self.getreg(instr[3]) + ", " + dest
                    else:
                        print "    movl $" + instr[3] + ", " + dest            

            elif instr[1] == '+':
                if instr[2] == instr[4]:        # Considering all the cases separately such as a=a+b,a=b+a,a=b+c for all the operators like+,-,*,/,%,shiftops,binaryops
                    if instr[2] in self.add_desc.keys():
                        reg = self.add_desc[instr[2]]
                        print "    movl " + reg + ", " + instr[2]
                        if instr[3] not in self.variable_list:
                            print "    movl $" + instr[3] + ", " + reg
                        else:
                            if instr[3] in self.add_desc.keys():
                                if reg != self.add_desc[instr[3]]:
                                    print "    movl " + self.add_desc[instr[3]] + ", " + reg
                            else:
                                print "    movl " + self.getreg(instr[3]) + ", " + reg
                        print "    addl " + instr[2] + ", " + reg
                    else:
                        if instr[3] not in self.variable_list:
                            print "    addl $" + instr[3] + ", " + instr[2]
                        else:
                            if instr[3] in self.add_desc.keys():
                                print "    addl " + self.add_desc[instr[3]] + ", " + instr[2]
                            else:
                                print "    addl " + self.getreg(instr[3]) + ", " + dest                    
                    continue

                elif instr[2] == instr[3]:          # Case of a=a+b
                    try:
                        dest = self.add_desc[instr[2]]
                    except KeyError:
                        dest = self.getreg(instr[2])
                else:
                    try:
                        dest,flag = self.add_desc[instr[2]],0
                    except KeyError:
                        dest,flag = self.getregx(instr[0],instr[2],instr[3])
                        if flag == 1:                           # This is the case when y has no further use, so spilling it and assigning register of y to x
                            reg = self.add_desc[instr[3]]
                            self.spillreg(reg)
                            self.add_desc[instr[2]] = reg
                            self.reg[self.add_desc[instr[2]]] = instr[2]

                    if instr[3] not in self.variable_list:          # Checking if y is a variable or a constant
                        print "    movl $" + instr[3] + ", " + dest
                    elif flag != 1:
                        if instr[3] in self.add_desc.keys():
                            if dest != self.add_desc[instr[3]]:
                                print "    movl " + self.add_desc[instr[3]] + ", " + dest
                        else:
                            print "    movl " + self.getreg(instr[3]) + ", " + dest
                    
                if instr[4] not in self.variable_list:              # Checking if z is a variable or a constant
                    print "    addl $" + instr[4] + ", " + dest
                else:
                    if instr[4] in self.add_desc.keys():
                        print "    addl " + self.add_desc[instr[4]] + ", " + dest
                    else:
                        print "    addl " + self.getreg(instr[4]) + ", " + dest
         
            elif instr[1] == '-':                   # '-' and '*' are handled exactly same as '+'
                if instr[2] == instr[4]:
                    if instr[2] in self.add_desc.keys():
                        reg = self.add_desc[instr[2]]
                        print "    movl " + reg + ", " + instr[2]
                        if instr[3] not in self.variable_list:
                            print "    movl $" + instr[3] + ", " + reg
                        else:
                            if instr[3] in self.add_desc.keys():
                                if reg != self.add_desc[instr[3]]:
                                    print "    movl " + self.add_desc[instr[3]] + ", " + reg
                            else:
                                print "    movl " + self.getreg(instr[3]) + ", " + reg
                        print "    subl " + instr[2] + ", " + reg
                    else:
                        reg = self.getreg(instr[2])
                        if instr[3] not in self.variable_list:
                            print "    movl $" + instr[3] + ", " + reg
                            print "    subl " + instr[2] + ", " + reg
                            #print "    subl $" + instr[3] + ", " + reg
                        else:
                            if instr[3] in self.add_desc.keys():
                                print "    subl " + self.add_desc[instr[3]] + ", " + reg
                            else:
                                print "    subl " + self.getreg(instr[3]) + ", " + dest                    
                    continue
                
                elif instr[2] == instr[3]:
                    try:
                        dest = self.add_desc[instr[2]]
                    except KeyError:
                        dest = self.getreg(instr[2])
                else:
                    try:
                        dest,flag = self.add_desc[instr[2]],0
                    except KeyError:
                        dest,flag = self.getregx(instr[0],instr[2],instr[3])
                        if flag == 1:
                            reg = self.add_desc[instr[3]]
                            self.spillreg(reg)
                            #print "    movl " + self.add_desc[instr[3]] + ", " + instr[3]
                            self.add_desc[instr[2]] = reg
                            self.reg[self.add_desc[instr[2]]] = instr[2]
                            #del self.add_desc[instr[3]]


                    if instr[3] not in self.variable_list:
                        print "    movl $" + instr[3] + ", " + dest
                    elif flag != 1:
                        if instr[3] in self.add_desc.keys():
                            if dest != self.add_desc[instr[3]]:
                                print "    movl " + self.add_desc[instr[3]] + ", " + dest
                        else:
                            print "    movl " + self.getreg(instr[3]) + ", " + dest
                    
                if instr[4] not in self.variable_list:
                    print "    subl $" + instr[4] + ", " + dest
                else:
                    if instr[4] in self.add_desc.keys():
                        print "    subl " + self.add_desc[instr[4]] + ", " + dest
                    else:
                        print "    subl " + self.getreg(instr[4]) + ", " + dest

            elif instr[1] == '*':
                if instr[2] == instr[4]:
                    if instr[2] in self.add_desc.keys():
                        reg = self.add_desc[instr[2]]
                        print "    movl " + reg + ", " + instr[2]
                        if instr[3] not in self.variable_list:
                            print "    movl $" + instr[3] + ", " + reg
                        else:
                            if instr[3] in self.add_desc.keys():
                                if reg != self.add_desc[instr[3]]:
                                    print "    movl " + self.add_desc[instr[3]] + ", " + reg
                            else:
                                print "    movl " + self.getreg(instr[3]) + ", " + reg
                        print "    imul " + instr[2] + ", " + reg
                    else:
                        if instr[3] not in self.variable_list:
                            print "    imul $" + instr[3] + ", " + instr[2]
                        else:
                            if instr[3] in self.add_desc.keys():
                                print "    imul " + self.add_desc[instr[3]] + ", " + instr[2]
                            else:
                                print "    imul " + self.getreg(instr[3]) + ", " + dest                    
                    continue
                elif instr[2] == instr[3]:
                    try:
                        dest = self.add_desc[instr[2]]
                    except KeyError:
                        dest = self.getreg(instr[2])
                else:
                    try:
                        dest,flag = self.add_desc[instr[2]],0
                    except KeyError:
                        dest,flag = self.getregx(instr[0],instr[2],instr[3])
                        if flag == 1:
                            reg = self.add_desc[instr[3]]
                            self.spillreg(reg)
                            #print "    movl " + self.add_desc[instr[3]] + ", " + instr[3]
                            self.add_desc[instr[2]] = reg
                            self.reg[self.add_desc[instr[2]]] = instr[2]
                            #del self.add_desc[instr[3]]

                    if instr[3] not in self.variable_list:
                        print "    movl $" + instr[3] + ", " + dest
                    elif flag != 1:
                        if instr[3] in self.add_desc.keys():
                            if dest != self.add_desc[instr[3]]:
                                print "    movl " + self.add_desc[instr[3]] + ", " + dest
                        else:
                            print "    movl " + self.getreg(instr[3]) + ", " + dest
                    
                if instr[4] not in self.variable_list:

                    print "    imul $" + instr[4] + ", " + dest
                else:
                    if instr[4] in self.add_desc.keys():
                        print "    imul " + self.add_desc[instr[4]] + ", " + dest
                    else:
                        print "    imul " + self.getreg(instr[4]) + ", " + dest

            elif instr[1] == '/':
                if self.reg['%eax'] != 0:           # Spilling register eax and edx before divide operation since they will be overwritten with quotient and remainder respectively
                    self.spillreg('%eax')
                if self.reg['%edx'] != 0:
                    self.spillreg('%edx')

                try:
                    if self.add_desc[instr[2]] != '%eax':
                        self.spillreg(self.add_desc[instr[2]])
                except KeyError:
                    pass
                
                dest = '%eax'                        # Quotient will be stored in eax, hence it is the destination
                self.reg['%eax'] = instr[2]
                self.add_desc[instr[2]] = '%eax'
                
                if instr[3] == instr[2]:
                    print "    movl " + instr[3] + ", " + dest
                elif instr[3] not in self.variable_list:
                    print "    movl $" + instr[3] + ", " + dest
                else:
                    if instr[3] in self.add_desc.keys():
                        if self.add_desc[instr[3]] != dest:
                            print "    movl " + self.add_desc[instr[3]] + ", " + dest
                    else:
                        print "    movl " + instr[3] + ", " + dest
                print "    cdq"                     # cdq command is for sign extended division. It puts 0 or -1 in edx depending upon the dividend stored in eax
                if instr[2] == instr[4]:
                    print "    idivl " + instr[2]
                    continue

                if instr[4] not in self.variable_list:
                    for reg,taken in self.reg.items():                  # In x=y/z z cannot be a constant, hence a register has to be assigned to it
                        if taken == 0 and reg not in ['%eax','%edx']:   # Returning an empty register other than eax or edx
                            break
                    if taken != 0 or reg in ['%eax','%edx']:
                        sorted_last_use = sorted(self.next_use[instr[0]], key=self.next_use[instr[0]].get)      # If no empty register found, then spilling the furthest use variable
                        for furthest_use in reversed(sorted_last_use):
                            if furthest_use in self.reg.values() and self.add_desc[furthest_use] not in ['%eax','%edx']:
                                break
                        reg = self.add_desc[furthest_use]
                        self.spillreg(reg)

                    print "    movl $" + instr[4] + ", " + reg
                    print "    idivl " + reg
                    self.reg[reg] = 0
                
                else:
                    if instr[4] in self.add_desc.keys():
                        print "    idivl " + self.add_desc[instr[4]]
                    else:
                        print "    idivl " + instr[4]
                
                self.reg['%edx'] = 0                # edx register is free now

            elif instr[1] == '%':                # modulo operator is handled in almost the same way as divide operator
                if self.reg['%eax'] != 0:
                    self.spillreg('%eax')
                if self.reg['%edx'] != 0:
                    self.spillreg('%edx')
                                     
                if instr[2] == instr[4]:
                    if instr[2] in self.add_desc.keys():
                        reg = self.add_desc[instr[2]]
                        self.spillreg(reg)

                if instr[2] in self.add_desc.keys():
                    reg = self.add_desc[instr[2]]
                    self.spillreg(reg)

                dest = '%edx'
                self.reg['%edx'] = instr[2]
                self.add_desc[instr[2]] = '%edx'

                if instr[3] == instr[2]:
                    print "    movl " + instr[3] + ", " + "%eax"
                elif instr[3] not in self.variable_list:
                    print "    movl $" + instr[3] + ", " + "%eax"
                else:
                    if instr[3] in self.add_desc.keys():
                        if self.add_desc[instr[3]] != "%eax":
                            print "    movl " + self.add_desc[instr[3]] + ", " + "%eax"
                    else:
                        print "    movl " + instr[3] + ", " + "%eax"
                print "    cdq"
                if instr[2] == instr[4]:
                    print "    idivl " + instr[2]
                    continue

                if instr[4] not in self.variable_list:
                    for reg,taken in self.reg.items():
                        if taken == 0 and reg not in ['%eax','%edx']:
                            break
                    if taken != 0 or reg in ['%eax','%edx']:
                        sorted_last_use = sorted(self.next_use[instr[0]], key=self.next_use[instr[0]].get)
                        for furthest_use in reversed(sorted_last_use):
                            if furthest_use in self.reg.values() and self.add_desc[furthest_use] not in ['%eax','%edx']:
                                break
                        reg = self.add_desc[furthest_use]
                        self.spillreg(reg)
                    print "    movl $" + instr[4] + ", " + reg
                    print "    idivl " + reg
                    self.reg[reg] = 0
                
                else:
                    if instr[4] in self.add_desc.keys():
                        print "    idivl " + self.add_desc[instr[4]]
                    else:
                        print "    idivl " + instr[4]

            elif instr[1] == '=&':               # a=&b , storing address of b in a
                self.pointers[instr[2]] = instr[3]
                #print "    movl $" + instr[3] + ", " + instr[2]
                if instr[2] in self.add_desc.keys():
                    print "    movl $" + instr[3] + ", " + self.add_desc[instr[2]]
                else:
                    print "    movl $" + instr[3] + ", " + self.getreg(instr[2])

            elif instr[1] == '*=':               # *a=b, storing value of b in memory location where a is pointing
                # if self.pointers[instr[2]] in self.add_desc.keys():
                #     reg = self.add_desc[self.pointers[instr[2]]]
                #     self.spillreg(reg)
                if instr[2] in self.add_desc.keys():
                    reg = self.add_desc[instr[2]]
                else:
                    reg = self.getregforced(instr[2],instr)
                    print "    movl " + instr[2] + ", " + reg
                if instr[3] in self.add_desc.keys():
                    print "    movl " + self.add_desc[instr[3]] + ", (" + reg + ")"
                else:
                    if instr[3] in self.variable_list:
                        reg1 = self.getregforced(instr[3],instr)
                        if reg1 == reg:
                            reg1 = self.getregforced(instr[3],instr)
                        print "    movl " + instr[3] + ", " + reg1
                        print "    movl " + reg1 + ", (" + reg + ")"
                    else:
                        print "    movl $" + instr[3] + ", (" + reg + ")"

            elif instr[1] == '=*':           # a=*b, storing value of memory location where b is pointing to a
                # if self.pointers[instr[3]] in self.add_desc.keys():
                #     reg = self.add_desc[self.pointers[instr[3]]]
                #     self.spillreg(reg)
                #print "hereh"
                if instr[3] in self.add_desc.keys():
                    reg = self.add_desc[instr[3]]
                else:
                    reg = self.getregforced(instr[3],instr)
                    print "    movl " + instr[3] + ", " + reg
                #print reg,instr
                if instr[2] in self.add_desc.keys():
                    print "    movl (" + reg + "), " + self.add_desc[instr[2]]
                else:
                    if instr[2] in self.variable_list:
                        instr[2] = self.getregforced(instr[2],instr)
                        print "    movl (" + reg + "), " + instr[2]
                    else:
                        print "    movl (" + reg + "), $" + instr[2]

                # if instr[3] in self.add_desc.keys():
                #     if instr[2] in self.add_desc.keys():
                #         print "    movl (" + self.add_desc[instr[3]] + "), " + self.add_desc[instr[2]]
                #     else:
                #         print "    movl (" + self.add_desc[instr[3]] + "), " + self.getreg(instr[2])
                # else:
                #     if instr[2] in self.add_desc.keys():
                #         print "    movl " + self.pointers[instr[3]] + ", " + self.add_desc[instr[2]]
                #     else:
                #         print "    movl " + self.pointers[instr[3]] + ", " + self.getreg(instr[2])            

            elif instr[1] in self.bitops.keys():        # Handling bitwise operators(same as other arithmetic operators)
                sys_op = self.bitops[instr[1]]
                # -------------------------------------------------- 
                # BITWISE AND
                # x = y & z
                # &, x, y, z
                # 1, 2, 3, 4 
                # --------------------------------------------------
                #print self.add_desc[instr[2]]
                try:
                    dest,flag = self.add_desc[instr[2]],0
                except KeyError:
                    dest,flag = self.getregx(instr[0],instr[2],instr[3])
                    if flag == 1:   # X will get register of Y
                        reg = self.add_desc[instr[3]]
                        self.spillreg(reg)
                        self.add_desc[instr[2]] = reg
                        self.reg[self.add_desc[instr[2]]] = instr[2]

                if instr[3] not in self.variable_list:
                    print "    movl $" + instr[3] + ", " + dest
                elif flag != 1:
                    if instr[3] in self.add_desc.keys():
                        if dest != self.add_desc[instr[3]]:
                            print "    movl " + self.add_desc[instr[3]] + ", " + dest
                    else:
                        print "    movl " + self.getreg(instr[3]) + ", " + dest
                    
                if instr[4] not in self.variable_list:
                    print "    " + sys_op + " $" + instr[4] + ", " + dest
                else:
                    if instr[4] in self.add_desc.keys():
                        print "    " + sys_op + " " + self.add_desc[instr[4]] + ", " + dest
                    else:
                        print "    " + sys_op + " " + self.getreg(instr[4]) + ", " + dest

            elif instr[1] in self.shiftop.keys():       # Handling bitshift operators
                sys_op = self.shiftop[instr[1]]
                # -------------------------------------------------- 
                # <<
                # x = y << z
                # x - dest, y - source, z is count
                # &, x, y, z
                # 1, 2, 3, 4 
                # shld z, y, x
                # --------------------------------------------------
                if instr[4]  in self.variable_list:
                    print '#' + sys_op +" needs the count argument to be a constant "
                    continue
                try:
                    dest,flag = self.add_desc[instr[2]],0
                except KeyError:
                    dest,flag = self.getregx(instr[0],instr[2],instr[3])
                    if flag == 1:   # X will get register of Y
                        reg = self.add_desc[instr[3]]
                        self.spillreg(reg)
                        self.add_desc[instr[2]] = reg
                        self.reg[self.add_desc[instr[2]]] = instr[2]

                if instr[3] not in self.variable_list:
                    print "    movl $" + instr[3] + ", " + dest
                elif flag != 1:
                    if instr[3] in self.add_desc.keys():
                        if dest != self.add_desc[instr[3]]:
                            print "    movl " + self.add_desc[instr[3]] + ", " + dest
                    else:
                        print "    movl " + self.getreg(instr[3]) + ", " + dest
                    
                if instr[4] not in self.variable_list:
                    print "    " + sys_op + " $" + instr[4] + "," + dest

            elif instr[1] == 'print':           # Handling print statement using stdio.h library
                if self.reg['%eax'] != 0:       # Spilling registers eax,ecx and edx since their values will be overwritten in print call function
                    self.spillreg('%eax')
                if self.reg['%ecx'] != 0:
                    self.spillreg('%ecx')
                if self.reg['%edx'] != 0:
                    self.spillreg('%edx')
                if self.variable_dict[instr[2]] not in ['int','array','string','pointer']:
                    if instr[2] in self.add_desc.keys():
                        reg = self.add_desc[instr[2]]
                        self.spillreg(reg)
                    print "    pushl $" + instr[2]
                    print "    pushl $print_string"
                    # else:
                    #     if instr[2] in self.variable_list:
                    #          print "    pushl " + instr[2]
                    #     else:
                    #         print "    pushl $" + instr[2]
                else:
                    if instr[2] in self.add_desc.keys():
                        print "    pushl " + self.add_desc[instr[2]]
                    else:
                        if instr[2] in self.variable_list:
                             print "    pushl " + instr[2]
                        else:
                            print "    pushl $" + instr[2]
                    print "    pushl $output_string"
                print "    call printf"
                print "    addl $8, %esp"

            elif instr[1] == 'scan':            # Handling scan statement using stdio.h library
                if self.reg['%eax'] != 0:       # Spilling registers eax,ecx and edx since their values will be overwritten in print call function
                    self.spillreg('%eax')
                if self.reg['%ecx'] != 0:
                    self.spillreg('%ecx')
                if self.reg['%edx'] != 0:
                    self.spillreg('%edx')
                if instr[2] in self.add_desc.keys():
                    reg = self.add_desc[instr[2]]
                    self.spillreg(reg)
                print "    pushl $scan"
                print "    call printf"
                print "    pushl $" + instr[2]
                print "    pushl $input_string"
                print "    call scanf"
                print "    addl $12, %esp"

            elif instr[1] == 'call':            # Function call
                if self.reg['%eax'] != 0:
                    self.spillreg('%eax')       # Spilling eax because return value will be stored in it
                self.context[instr[2]] = {}
                for reg,var in self.reg.iteritems():           # Storing the context before calling the function
                    if var != 0:
                        self.context[instr[2]][reg] = var
                    
            elif instr[1] == 'label':           # Start of a particular function
                print instr[2] + ":"

            elif instr[1] == 'ret':             # End of a functions
                # print "    subl $4, %ebp"
                # print "    movl %ebp, %esp"
                if self.reg['%eax'] != 0:       # Spilling eax because return value will be stored in it
                    self.spillreg('%eax')
                if (instr[0]+1) in self.leaders:
                    for reg,var in self.reg.iteritems():         # Putting all variables back into memory at the end of the function
                        if self.reg[reg] != 0:
                            print "    movl " + reg + ", " + var
                            self.reg[reg] = 0
                            try:
                                del self.add_desc[var]
                            except KeyError:
                            	pass
                if len(instr) > 2:              # Means the function has a return value, store it in eax
                    if instr[2] in self.variable_list:
                        if instr[2] in self.add_desc.keys():
                            print "    movl " + self.add_desc[instr[2]] + ", " + "%eax"
                            self.add_desc[instr[2]] = '%eax'
                            self.reg['%eax'] = instr[2]
                        #print "    movl " + instr[2] + ", " + "%eax"
                    else:
                        print "    movl " + "$" + instr[2] + ", " + "%eax"
                print "    ret"
                print

            elif instr[1] == 'ifgoto':          # First compare the operands, then put back all values in memory(since it marks the end of a basic block) and then jump to the corresponding label
                if instr[3] not in self.variable_list:
                    string = "    cmpl $" + instr[3] + ", "
                else:
                    if instr[3] in self.add_desc.keys():
                        string = "    cmpl " + self.add_desc[instr[3]] + ", "
                    else:
                        string = "    cmpl " + self.getreg(instr[3]) + ", "
                if instr[4] not in self.variable_list:      # Compare cannot be done with a constant, so assigning a register to it
                    for reg,taken in self.reg.items():
                        if taken == 0:
                            break
                    if taken != 0:
                        sorted_last_use = sorted(self.next_use[instr[0]], key=self.next_use[instr[0]].get)
                        for furthest_use in reversed(sorted_last_use):
                            if furthest_use in self.reg.values() and self.add_desc[furthest_use] != string[9:13]:
                                break
                        reg = self.add_desc[furthest_use]
                        self.spillreg(reg)
                    print "    movl $" + instr[4] + ", " + reg
                    print string + reg
                    self.reg[reg] = 0
                else:
                    if instr[4] in self.add_desc.keys():
                        print string + self.add_desc[instr[4]]
                    else:
                        print string + self.getreg(instr[4])
                
                for reg,var in self.reg.iteritems():         # Putting all variables back into memory at the end of a basic block
                    if self.reg[reg] != 0:
                        print "    movl " + reg + ", " + var
                        self.reg[reg] = 0
                        del self.add_desc[var]

                if instr[2] == 'leq':                       # Jumping to the corresponding label
                    print "    jge L" + str(self.label[int(instr[5])])
                elif instr[2] == 'lt':
                    print "    jg L" + str(self.label[int(instr[5])])
                elif instr[2] == 'geq':
                    print "    jle L" + str(self.label[int(instr[5])])
                elif instr[2] == 'gt':
                    print "    jl L" + str(self.label[int(instr[5])])
                elif instr[2] == 'eq':
                    print "    je L" + str(self.label[int(instr[5])])
                elif instr[2] == 'ne':
                    print "    jne L" + str(self.label[int(instr[5])])

            elif instr[1] == 'goto':
                for reg,var in self.reg.iteritems():         # Putting all variables back into memory at the end of a basic block
                    if self.reg[reg] != 0:
                        print "    movl " + reg + ", " + var
                        self.reg[reg] = 0
                        del self.add_desc[var]
                print "    jmp L" + str(self.label[int(instr[2])])      # Jumping to the corresponding label

            elif instr[1] == 'param':
                self.params += 1
                try:
                    instr[2] = self.add_desc[instr[2]]
                except KeyError:
                    instr[2] = '$' + instr[2]
            	print "    pushl " + instr[2]

            elif instr[1] == 'new':
                if self.reg['%eax'] != 0:
                    self.spillreg('%eax')
                print "    pushl $" + instr[2]
                print "    call malloc"
                print "    movl %eax," + instr[3]    #RETURN VALUE IN EAX NEEDS TO BE STORED IN var -> instr[3]
                print "    addl $4, %esp "

        if block[0][1] != 'label':
            for reg,var in self.reg.iteritems():         # Putting all variables back into memory at the end of a basic block
                if self.reg[reg] != 0:
                    print "    movl " + reg + ", " + var
                    self.reg[reg] = 0
                    try:
                        del self.add_desc[var]
                    except KeyError:
                        pass

        if block[-1][1] == 'call':                  # Just after the function returns, eax has the return value so storing its value in the assigned variable
            print "    movl %esp,%ebp"
            print "    pushl %ebp"
            print "    call " + block[-1][2]
            print "    popl %ebp"
            if self.reg['%ebx'] != 0:
                self.spillreg('%ebx')
            for i in range(self.params):
                print "    popl %ebx"
            self.params = 0
            try:
                print "    movl %eax, " + instr[3]
            except IndexError:
                pass
            for reg,var in self.context[block[-1][2]].iteritems():      # Getting back register contents from this function's context after it returns
                print "    movl " + var + ", " + reg

        if (instr[0]+1) in self.leaders:                # When next instruction is a leader, put all the values back to memory(since the basic block has ended)
            for reg,var in self.reg.iteritems():         # Putting all variables back into memory at the end of a basic block
                if self.reg[reg] != 0:
                    print "    movl " + reg + ", " + var
                    self.reg[reg] = 0
                    del self.add_desc[var]

mycodegen = AssCodeGen(sys.argv[1])
mycodegen.emit_code()