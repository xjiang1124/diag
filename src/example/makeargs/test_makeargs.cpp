#include <stdlib.h>
#include <stdio.h>

extern int makeargs(char *args, int *argc, char ***aa);

int main(void) {
    char **myargs;
    int argc;

    int numargs = makeargs("Hello world, this is a test", &argc, &myargs);
    while (numargs) {
        printf("%s\r\n", myargs[argc - numargs--]);
    };

	free(myargs);

    return (EXIT_SUCCESS);
}
