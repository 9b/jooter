from jooter import Jooter
import sys

def main():
	if len(sys.argv) < 4:
		sys.exit('Usage (3 arguments): %s "%s" %s %s' % (sys.argv[0],"http://www.joomlasite.com/administrator/","<user list>","<password list>"))
	else:
		DEBUG = False

		url = sys.argv[1]
		ulist = sys.argv[2]
		plist = sys.argv[3]
		if DEBUG:
			j = Jooter(url,ulist,plist,"DEBUG")		
		else:
			j = Jooter(url,ulist,plist)

		output = j.scan()
		if output != None:
		    print output

if __name__ == '__main__':
	main()
