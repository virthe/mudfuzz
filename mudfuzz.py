#!/usr/bin/env python3

from telnetlib import Telnet

def main ():
	print ( "MUD Fuzz" )

	with Telnet ( 'localhost', 8000 ) as tn:
		tn.interact ()

if __name__ == "__main__":
	main ();
