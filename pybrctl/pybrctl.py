import subprocess

class Bridge(object):
	def __init__(self, name):
		""" Initialize a bridge object. """
		self.name = name

	def __str__(self):
		""" Return a string of the bridge name. """
		return self.name

	def __repr__(self):
		""" Return a representaion of a bridge object. """
		return "<Bridge: %s>" % self.name

	def addif(self, iname):
		""" Add an interface to the bridge """
		try:
			_runshell([brctl_exec_path, 'addif', self.name, iname])
		except SubProcessException as e:
			raise AddFailedException(e, iname, self.name)

	def delif(self, iname):
		""" Delete an interface from the bridge. """
		try:
			_runshell([brctl_exec_path, 'delif', self.name, iname])
		except SubProcessException as e:
			raise DeleteFailedException(e, iname, self.name)

	def hairpin(self, port, val=True):
		""" Turn hairpin on/off on a port. """
		try:
			if val: state = 'on'
			else: state = 'off'
			_runshell([brctl_exec_path, 'hairpin', self.name, port, state])
		except SubProcessException as e:
			raise SetHairpinException(e, port, self.name)

	def stp(self, val=True):
		""" Turn STP protocol on/off. """
		try:
			if val: state = 'on'
			else: state = 'off'
			_runshell([brctl_exec_path, 'stp', self.name, state])
		except SubProcessException as e:
			raise SetSTPException(e, self.name)

	def setageing(self, time):
		""" Set bridge ageing time. """
		try:
			_runshell([brctl_exec_path, 'setageing', self.name, str(time)])
		except SubProcessException as e:
			raise SetAgeingException(e, self.name)

	def setbridgeprio(self, prio):
		""" Set bridge priority value. """
		try:
			_runshell([brctl_exec_path, 'setbridgeprio', self.name, str(prio)])
		except SubProcessException as e:
			raise SetBridgePriorityException(e, self.name)

	def setfd(self, time):
		""" Set bridge forward delay time value. """
		try:
			_runshell([brctl_exec_path, 'setfd', self.name, str(time)])
		except SubProcessException as e:
			raise SetForwardDelayException(e, self.name)

	def sethello(self, time):
		""" Set bridge hello time value. """
		try:
			_runshell([brctl_exec_path, 'sethello', self.name, str(time)])
		except SubProcessException as e:
			raise SetHelloTimeException(e, self.name)

	def setmaxage(self, time):
		""" Set bridge max message age time. """
		try:
			_runshell([brctl_exec_path, 'setmaxage', self.name, str(time)])
		except SubProcessException as e:
			raise SetMaxAgeException(e, self.name)

	def setpathcost(self, port, cost):
		""" Set port path cost value for STP protocol. """
		try:
			_runshell([brctl_exec_path, 'setpathcost', self.name, port, str(cost)])
		except SubProcessException as e:
			raise SetPathCostException(e, port, self.name)

	def setportprio(self, port, prio):
		""" Set port priority value. """
		try:
			_runshell([brctl_exec_path, 'setportprio', self.name, port, str(prio)])
		except SubProcessException as e:
			raise SetPortPriorityException(e, port, self.name)

	def _show(self):
		""" Return a list of unsorted bridge details. """
		try:
			p = _runshell([brctl_exec_path, 'show', self.name])
			return p.stdout.read().split()[7:]
		except SubProcessException as e:
			raise ShowDetailsException(e, self.name)

	def getid(self):
		""" Return the bridge id value. """
		return self._show()[1]

	def getifs(self):
		""" Return a list of bridge interfaces. """
		return self._show()[3:]

	def getstp(self):
		""" Return if STP protocol is enabled. """
		return self._show()[2] == 'yes'

	def showmacs(self):
		""" Return a list of mac addresses. """
		raise NotImplementedError()

	def showstp(self):
		""" Return STP information. """
		raise NotImplementedError()

	def link_up(self):
		try:
			_runshell([ip_exec_path, 'link', 'set', 'dev', self.name, 'up'])
		except SubProcessException as e:
			raise SetLinkUpException(e, self.name)

	def link_down(self):
		try:
			_runshell([ip_exec_path, 'link', 'set', 'dev', self.name, 'down'])
		except SubProcessException as e:
			raise SetLinkDownException(e, self.name)

	def _create(self):
		try:
			_runshell([brctl_exec_path, 'addbr', self.name])
		except SubProcessException as e:
			raise CreateBridgeException(e, self.name)

	def _remove(self):
		try:
			_runshell([brctl_exec_path, 'delbr', self.name])
		except SubProcessException as e:
			raise DeleteBridgeException(e, self.name)

class BridgeController(object):
	@staticmethod
	def addbr(name):
		""" Create a bridge and set the device up. """
		ret = Bridge(name)
		ret._create()
		ret.link_up()
		return ret

	@classmethod
	def delbr(cls, name):
		""" Set the device down and delete the bridge. """
		bridge = cls.getbr(name) # Check if exists
		if bridge:
			bridge.link_down()
			bridge._remove()
		else:
			return False

	@staticmethod
	def showall():
		""" Return a list of all available bridges. """
		try:
			p = _runshell([brctl_exec_path, 'show'])
			wlist = p.stdout.read().splitlines()[1:]
			brlist = [line.split("\t")[0] for line in wlist]
			return map(Bridge, brlist)
		except SubProcessException as e:
			raise ShowBridgesException(e)

	@classmethod
	def getbr(cls, name):
		""" Return a bridge object."""
		for br in cls.showall():
			if br.name == name:
				return br
		return None

class SubProcessException(Exception):
	def __init__(self, return_code):
		self.return_code = return_code

	def message(self):
		return "Subprocess returned error code {}".format(self.return_code)

class BridgeException(Exception):
	msg_template = ""

	def __init__(self, inner_exception, *args):
		if inner_exception:
			self.inner_exception = inner_exception
		else:
			self.inner_exception = None
		self.msg_args = args
		print self.message()

	def message(self):
		ret = self.msg_template.format(self.msg_args)
		if self.inner_exception:
			ret += " " + self.inner_exception.message()
		return ret

class AddFailedException(BridgeException):
	msg_template = "Could not add interface {} to {}."

class DeleteFailedException(BridgeException):
	msg_template = "Could not delete interface {} from {}."

class SetHairpinException(BridgeException):
	msg_template = "Could not delete interface {} from {}."

class SetSTPException(BridgeException):
	msg_template = "Could not set stp on {}."

class SetAgeingException(BridgeException):
	msg_template = "Could not set ageing time on {}."

class SetBridgePriorityException(BridgeException):
	msg_template = "Could not set ageing time on {}."

class SetForwardDelayException(BridgeException):
	msg_template = "Could not set forward delay on {}."

class SetHelloTimeException(BridgeException):
	msg_template = "Could not set hello time on {}."

class SetMaxAgeException(BridgeException):
	msg_template = "Could not set max message age on {}."

class SetPathCostException(BridgeException):
	msg_template = "Could not set path cost on port {} in {}."

class SetPortPriorityException(BridgeException):
	msg_template = "Could not set priority on port {} in {}."

class ShowDetailsException(BridgeException):
	msg_template = "Could not show {}."

class CreateBridgeException(BridgeException):
	msg_template = "Could not create bridge {}."

class DeleteBridgeException(BridgeException):
	msg_template = "Could not create bridge {}."

class SetLinkUpException(BridgeException):
	msg_template = "Could not set link up on {}."

class SetLinkDownException(BridgeException):
	msg_template = "Could not set link down on {}."

class NoSuchBridgeException(BridgeException):
	msg_template = "Bridge {} does not exist."

class ShowBridgesException(BridgeException):
	msg_template = "Could not show bridges."

def _runshell(cmd):
	""" Run a shell command. if fails, raise a proper exception. """
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	return_code = p.wait()
	if return_code != 0:
		raise SubProcessException(return_code)
	return p

def _get_path(executable_name):
	try:
		return _runshell(['/usr/bin/which', executable_name]).stdout.read()[:-1]
	except:
		print "executable path not found"

ip_exec_path = _get_path("ip")
brctl_exec_path = _get_path("brctl")
