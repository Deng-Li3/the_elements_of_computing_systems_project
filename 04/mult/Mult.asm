// This file is part of the materials accompanying the book
// "The Elements of Computing Systems" by Nisan and Schocken,
// MIT Press. Book site: www.idc.ac.il/tecs
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[3], respectively.)

// Put your code here.
	@2
	M=0
(CHECK_SEG)
	@1
	M=M-1
	D=M
	@ADD_SEG
	D;JGE
	@INFINITE_LOOP
	D;JLT
(ADD_SEG)
	@0
	D=M
	@2
	M=M+D
	@CHECK_SEG
	0;JMP
(INFINITE_LOOP)
	@INFINITE_LOOP
	0;JMP