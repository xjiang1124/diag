#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main (int argc, char**argv)
{
    FILE *in_file, *out_file;
    int data;
    int bytesRead;

    if ( argc != 3 ) {
        printf("Invalid input parameters\n");
	printf("   hex2bin inpufile outputfile\n");
	return -1;
    }

    in_file = fopen(argv[1], "r");
    if ( in_file == NULL ) {
        printf("input file does not exist\n");
	return -1;
    }
    out_file = fopen(argv[2], "wb");
    if ( out_file == NULL ) {
        printf("cannot open output file\n");
	return -1;
    }

    printf("CSR value to be sent in binary format\n");
    while ( fscanf(in_file, "%2x", &data)  == 1 ) {
        fwrite(&data, 1, 1, out_file);
	printf("%2.2x", data);
    };
    printf("\n");
    return 0;
}
