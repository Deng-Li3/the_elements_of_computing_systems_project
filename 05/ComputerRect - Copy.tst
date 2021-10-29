// This file is part of the materials accompanying the book 
// "The Elements of Computing Systems" by Nisan and Schocken, 
// MIT Press. Book site: www.idc.ac.il/tecs
// File name: projects/05/ComputerRect.tst

load Computer.hdl,

// Load a program written in the Hack machine language.
// The program draws a rectangle of width 16 pixels and 
// length RAM[0] at the top left of the screen.
ROM32K load Rect.hack,

echo "Before you run this script, select the 'Screen' option from the 'View' menu";

echo "A small rectangle should be drawn at the top left of the screen (the 'Screen' option of the 'View' menu should be selected.)";

// Draws a rectangle 16 pixels wide and 4 pixels long
// set RAM16K[0] 4,

repeat 63 {
    tick, tock;
}

