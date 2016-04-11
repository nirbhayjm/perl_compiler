.PHONY: all clean

all: src/parser.py
	@if [ ! -d "bin" ]; then mkdir bin; fi
	@rm -rf bin/irgen
	@echo "#!/bin/sh" >bin/irgen
	@printf '\npython src/parser.py $$1 $$2\n' >>bin/irgen
	@chmod +x bin/irgen
	@echo "Make completed."

clean:
	rm  -rf src/*.pyc src/parsetab.py src/parser.out bin/irgen
