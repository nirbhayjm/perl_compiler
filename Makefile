.PHONY: all clean

all: out.s

out.ir:
	./src/parser.py test/struct.pl >out.ir

out.s:	out.ir
	./src/asgen.py out.ir >out.s

bin/out: out.s
	as --gstabs out.s -32 -o bin/out.o
	ld bin/out.o -m elf_i386 -o bin/out -lc -dynamic-linker /lib/ld-linux.so.2

out: bin/out
	./bin/out

clean:
	rm  -rf src/*.pyc src/parsetab.py src/parser.out bin/irgen out.s bin/out.o out.ir
