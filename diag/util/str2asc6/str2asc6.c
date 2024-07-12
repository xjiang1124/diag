#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define STR_MAX_SIZE 20 // 20 byte

// Function to convert a character to its 6-bit ASCII representation
int charTo6BitAscii(char c) {
    // ASCII values start from 32 (space) to 95 ('_')
    // printf("%X\n", c);
    if (c >= 0x20 && c <= 0x5F) {
        return c - 0x20;
    } else {
        printf("Character \'%c\' is outside the printable ASCII range (0x20 to 0x5F)", c);
        printf("and does not have a valid 6-bit ASCII representation.\n");
        return -1; 
    }
}

// Function to pack a string into 6-bit ASCII representation
int pack6BitAscii(const char *input, unsigned char *output) {
    int j = 0;
    int bitCount = 0;
    unsigned char currentByte = 0;

    for (int i = 0; i < strlen(input); i++) {
        int asciiVal = charTo6BitAscii(input[i]);
        if (asciiVal == -1) return -1;

        currentByte |= (asciiVal << bitCount);
        bitCount += 6;

        // Update current byte if it is full (8 bits)
        if (bitCount >= 8) {
            output[j++] = currentByte; 
            bitCount -= 8; 
            currentByte = asciiVal >> (6 - bitCount);
        }
    }

    // Flush the last byte if there are remaining bits
    if (bitCount > 0 && j < STR_MAX_SIZE) {
        output[j++] = currentByte;
    }

    return 0;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <input_string>\n", argv[0]);
        return 1;
    }

    // Packs a string input as its 6-bit ASCII representation in little endian
    const char *input_string = argv[1];

    unsigned char packedOutput[STR_MAX_SIZE] = {0}; // 20 byte array initialized to 0

    // Check input length
    if (strlen(input_string) > STR_MAX_SIZE) {
        printf("Error: Input string exceeds maximum length of 20 bytes.\n");
        return 1;
    }

    if (pack6BitAscii(input_string, packedOutput) == -1) return -1;

    printf("Original string: %s\n", input_string);
    printf("Packed 6-bit ASCII representation: \n");


    printf("Binary: ");
    for (int i = STR_MAX_SIZE-1; i >= 0 ; i--) {
        for (int j = 7; j >= 0; j--) {
            printf("%d", (packedOutput[i] >> j) & 1);
        }
        printf(" ");
    }
    printf("\n");


    printf("Hex:    ");
    for (int i = STR_MAX_SIZE-1; i >= 0; i--) {
        printf("%02X ", packedOutput[i]);
    }
    printf("\n");

    return 0;
}

