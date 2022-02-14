#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <string>
#include <iostream>


using namespace std;

string retrieveString( char* buf, size_t max ) {

    size_t len = 0;
    while( (len < max) && (buf[ len ] != '\0') ) {
        len++;
    }

    return std::string( buf, len );
}

void usage (void) {
    printf("Usage: test_mmap <r/w> <phys_addr> [value]\n");
    return;
}

int main(int argc, char *argv[]) {
    size_t buffSize = 4096;
    string offsetStr;
    off_t offset;
    uint32_t data;

    string option;
	option = retrieveString(argv[1], 1);
    offsetStr = retrieveString(argv[2], 16);
    //cout << "option: " << option << "; offset: " << offsetStr << endl;

    if (option.compare("r") == 0) {
        //cout << "read" << endl;
    } else if (option.compare("w") == 0) {
        //cout << "write" << endl;
        data = strtoul(argv[3], NULL, 0);
    } else {
        cout << "Wrong input" << endl;
        usage();
        return 0;
    }

    offset = stol(offsetStr ,nullptr, 0);
    //printf("offset: 0x%lx\n", offset);

    // Truncate offset to a multiple of the page size, or mmap will fail.
    size_t pagesize = sysconf(_SC_PAGE_SIZE);
    off_t page_base = (offset / pagesize) * pagesize;
    off_t page_offset = offset - page_base;
    //printf("page_size 0x%lx; page_base 0x%lx; offset 0x%lx; page_offset 0x%lx\n", pagesize, page_base, offset, page_offset);

    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    unsigned char *mem = (unsigned char *) mmap(NULL, buffSize, PROT_READ | PROT_WRITE, MAP_SHARED, fd, page_base);
    if (mem == MAP_FAILED) {
        perror("Can't map memory");
        return -1;
    }

    if (option.compare("r") == 0) {
        data = *((uint32_t *) (mem+page_offset));
        printf("Read from offset 0x%lx; read data: 0x%x\n", offset, data);
    } else {
        *((uint32_t *) (mem+page_offset)) = data;
        printf("Write to offset 0x%lx; write data: 0x%x\n", offset, data);
    }
    return 0;
}
