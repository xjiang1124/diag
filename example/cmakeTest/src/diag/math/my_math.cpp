#include <stdlib.h>
#include <stdio.h>

#include "my_abs.h"

int main(int argc, char *argv[])
{
    int input = -1;
    int output;
    output = my_abs(input);

    printf("input = %d, output = %d\n", input, output);
}
