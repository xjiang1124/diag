all: test_mmap

CFLAGS=-Wall -I -c

test_mmap test_mmap.cc:
	gcc test_mmap.cc -lstdc++ -o test_mmap $(CFLAGS)
	
clean:
	-rm -f *.o *.a test_mmap dump*

