// This file is part of the materials accompanying the book
// "The Elements of Computing Systems" by Nisan and Schocken,
// MIT Press. Book site: www.idc.ac.il/tecs
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed,
// the screen should be cleared.

// The memory mapped for screen starts at address 16384(0x4000) and end at 14576(0x6000)
// Put your code here.
    @24575
    D=A
    @R2
    M=D // Store screen end in R2
(BEGIN)
    @SCREEN
    D=A
    @R1
    M=D // Store screen start in R1
(LOOP)
    @KBD
    D=M
    @KEY_PRESSED
    D;JGT
    @KEY_NOT_PRESSED
    D;JLE
(KEY_PRESSED)
    @R1
    A=M
    M=-1
    @DONE_PAINT
    0;JMP
(KEY_NOT_PRESSED)
    @R1
    A=M
    M=0
    @DONE_PAINT
    0;JMP
(DONE_PAINT)
    @R1
    D=M+1
    M=D
    @R2
    D=D-M
    @BEGIN
    D;JGT
    @LOOP
    0;JMP
