#include "../../include/cType.h"

int ReadId(unsigned char* bp);

int CpldRd(unsigned char addr, unsigned char* value);

int CpldWr(unsigned char addr, unsigned char value);
