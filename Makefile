.PHONY: all clean

all: src/parser.py
	@if [ ! -d "bin" ]; then mkdir bin; fi
	@rm -rf bin/irgen
	@echo "#!/bin/sh" >bin/irgen
	@printf '\npython src/parser.py $$1 $$2\n' >>bin/irgen
	@chmod +x bin/irgen
	@echo "Make completed."

out.s:
	./src/asgen.py test/test1.ir >out.s

bin/out: out.s
	as --gstabs out.s -32 -o bin/out.o
	ld bin/out.o -m elf_i386 -o bin/out -lc -dynamic-linker /lib/ld-linux.so.2

run: bin/out
	./bin/out

clean:
	rm  -rf src/*.pyc src/parsetab.py src/parser.out bin/irgen out.s bin/out.o
