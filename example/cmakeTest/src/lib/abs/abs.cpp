/**
 * abs.cpp
 * 
 * library file to calculate absolute value 
 *
 */

int my_abs(int input)
{
    int rc;

    if (input > 0)
    {
        rc = input;
    }
    else
    {
        rc = input * (-1);
    }

    return rc;
}

