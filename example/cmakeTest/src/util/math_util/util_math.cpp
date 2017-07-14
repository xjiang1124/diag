#include <stdlib.h>
#include <stdio.h>

#include "my_abs.h"
#include "my_multi.h"

int main(int argc, char *argv[])
{
    int input = -1;
    int output;
    output = my_abs(input);

    printf("input = %d, output = %d\n", input, output);

    output = my_multi(input, 5);
    printf("multi: input = %d, output = %d\n", input, output);

    return 0;
}
