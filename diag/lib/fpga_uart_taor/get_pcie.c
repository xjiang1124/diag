#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

int main ()
{
    FILE *fileptr = fopen("/proc/bus/pci/devices", "r");
    char line[512];
    char delim[] = "\t";
    char *ptr = NULL;
    int len;
    unsigned long long int address = 0;

    while ( fgets(line, sizeof(line), fileptr) ) {
        ptr = strtok(line, delim);
        while ( ptr != NULL ) {
           if ( strcmp(ptr, "1dd8000a") == 0 ) {
               ptr = strtok(NULL, delim);
               ptr = strtok(NULL, delim);
               len = strlen(ptr);
               ptr[len - 1] = '0';
               address = strtoll(ptr, NULL, 16);
               break;
           } else
               ptr = strtok(NULL, delim);
        }
        if ( address != 0 ) {
            printf("PCIE BAR = 0x%llx\n", address);
            fclose(fileptr);
            return 0;
        }
    }
    if ( address != 0 ) {
        printf("pcie BAR = 0x%llx\n", address);
        return 0;
    }
    fclose(fileptr);
    return 0;
}
