class ThreeAddressCode:

	def __init__(self):
		self.code = []
		self.nextQuad = 1
		self.patchMap = {}
		self.labelCount = -1
		self.labelPrefix = "L"
		self.DEBUG = False

	def emit(self,op,dst,src1,src2,src3=''):
		self.code.append([op,dst,src1,src2,src3])
		self.nextQuad += 1

	def addPatchList(self,targetLabel):
		if str(targetLabel)[:len(self.labelPrefix)] != self.labelPrefix:
			if self.DEBUG:
				print "TAC: Skipping addPatchList for already defined label at line number ",targetLabel
			return 
		if targetLabel in self.patchMap:
			self.patchMap[targetLabel].append(self.nextQuad)
		else:
			self.patchMap[targetLabel] = [self.nextQuad]

	#--- This function places a label (virtually) by back patching all targets to it
	def placeLabel(self,targetLabel):
		if targetLabel not in self.patchMap:
			# print "Nothing to patch this label to!"
			return
		for quad in self.patchMap[targetLabel]:
			assert(quad-1 < self.nextQuad)
			if self.code[quad-1][0] == 'goto':
				self.code[quad-1][1] = self.nextQuad
			elif self.code[quad-1][0] == 'ifgoto':
				self.code[quad-1][4] = self.nextQuad

	def getNextQuad(self):
		return self.nextQuad

	def printCode(self,intitialQuad):
		for quad in range(len(self.code)):
			#assert(quad-1 < self.nextQuad)
			if self.code[quad][0] == 'goto':
				self.code[quad][1] += intitialQuad-1
			elif self.code[quad][0] == 'ifgoto':
				self.code[quad][4] += intitialQuad-1
		i=0        
		for i,instr in enumerate(self.code):
			print str(i+intitialQuad) + ', ' + ', '.join(str(e) for e in instr if e != '')
		# print "\nPatch label map:"
		# print self.patchMap
		return intitialQuad+i+1

	def makeLabel(self):
		self.labelCount += 1
		return self.labelPrefix + str(self.labelCount)