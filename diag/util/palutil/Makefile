.PHONY: all
CFLAGS= -g -Wall
LDFLAGS=-li2csim

all: palutil

palutil.o: palutil.c
	@echo $(CC)
	$(CC) $(CFLAGS) -c *palutil.c

palutil: palutil.o
	 $(CC) palutil.o $(LDFLAGS) -o palutil

clean:
	rm -f *.o palutil
