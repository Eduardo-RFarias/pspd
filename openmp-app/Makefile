# Makefile para Jogo da Vida
CC=gcc
CFLAGS=-Wall -O3 -march=native
OPENMP_FLAGS=-fopenmp
LIBS=-lm

# Targets
all: jogodavida_openmp

# Versão com OpenMP
jogodavida_openmp: jogodavida_openmp.c
	$(CC) $(CFLAGS) $(OPENMP_FLAGS) -o jogodavida_openmp jogodavida_openmp.c $(LIBS)

# Limpeza
clean:
	rm -f jogodavida_openmp

.PHONY: all clean