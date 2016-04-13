class SymbolTable:

    def __init__(self,debug=''):
        self.table = {
            'main': {
                'name'        : 'main',
                'type'        : 'main',
                'parent'      : None,
                'identifiers' : {},
                'places'      : {},
                'subroutines' : {},
                'label'       : 'main'
            }
        }

        self.currentScope = 'main'
        self.classes = []

        #--- Temporaries
        self.tempCount = -1
        self.tempPrefix = "t"
        self.subCount = 0
        self.subPrefix = "Subroutine"

        #--- Debugging switches
        self.DEBUG = list(debug)

    def createTemp(self):
        self.tempCount += 1
        return self.tempPrefix + str(self.tempCount)

    def createSubName(self):
        self.subCount += 1
        return self.subPrefix + str(self.subCount)

    def insertIdentifier(self,idName,place,type_scope='main',idType='NoType', size = 4):
        if type_scope == 'my':
            setScope = self.currentScope
        else:
            setScope = 'main'

        if idType == 'scalar':
            size = 4
        elif idType == 'array':
            size = 400
        elif idType == 'hash' :
            size = 400
        elif idType == 'struct' :
            size = size            
            
        self.table[setScope]['identifiers'][idName] = {
            'place' : place,
            'type' : idType,
            'size' : size
        }
        self.table[setScope]['places'][place] = idName

        if 'i' in self.DEBUG:
            print "ST: Inserted new identifier :",idName,"-->",place

    def getAttribute(self,idName,atrribute):
        scope = self.lookupScope(idName)
        if scope is not None:
            # The python get() function of dictionaries returns the value with key = attribute
            return self.table[scope]['identifiers'][idName].get(atrribute)
        else:
            return None

    def declareSub(self,subName):
        fullName = self.currentScope + '/' + subName
        self.table[fullName] = {
            'name'          : subName,
            'type'          : 'subroutine',
            'parent'        : self.currentScope,
            'identifiers'   : {},
            'places'        : {},
            'subroutines'   : {},
            'label'         : self.createSubName()
        }

        self.table[self.currentScope]['subroutines'][subName] = {
            'fullName' : fullName
        }

        self.currentScope = fullName

    def endDeclareSub(self):
        self.currentScope = self.table[self.currentScope]['parent']

    def getSubLabel(self):
        assert( self.table[self.currentScope]['type'] == 'subroutine' )
        return self.table[self.currentScope]['label']

    def lookupSub(self,subName):
        scope = self.currentScope
        while scope is not None:
            if subName in self.table[scope]['subroutines']:
                fullName = self.table[scope]['subroutines'][subName]['fullName']
                return self.table[fullName]['label']
            scope = self.table[scope]['parent']
        return None

    def declareClass(self,className):
        # Classes can only be declared in main scope for now
        assert(self.currentScope == 'main') 
        self.table[className] = {
            'name'          : className,
            'type'          : 'class',
            'parent'        : self.currentScope,
            'identifiers'   : {},
            'places'        : {},
            'subroutines'   : {},
        }
        self.classes.append(className)
        self.currentScope = className

    def endDeclareClass(self):
        self.currentScope = 'main'

    def lookupClass(self,className):
        return className in self.table['main']['classes']

    def lookupScope(self,idName):
        scope = self.currentScope
        while scope is not None:
            if idName in self.table[scope]['identifiers']:
                return scope
            scope = self.table[scope]['parent']
        return None

    def lookupIdentifier(self,idName):
        return self.lookupScope(idName) != None