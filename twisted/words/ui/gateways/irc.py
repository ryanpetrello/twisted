# Twisted, the Framework of Your Internet
# Copyright (C) 2001 Matthew W. Lefkowitz
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of version 2.1 of the GNU Lesser General Public
# License as published by the Free Software Foundation.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from twisted.protocols import irc
from twisted.words.ui import gateway
from twisted.internet import tcp
import string

shortName="IRC"
longName="Internet Relay Chat"

loginOptions=[["Nickname","username","my_nickname"],
	      ["Real Name","realname","Twisted User"],
              ["Password (optional)","password",""],
              ["Server","server","localhost"],
              ["Port #","port","6667"]]

def makeConnection(im,server=None,port=None,**kw):
    c=apply(IRCGateway,(),kw)
    im.attachGateway(c)
    try:
        port=int(port)
    except:
        pass
    tcp.Client(server,port,c)

class IRCGateway(irc.IRCClient,gateway.Gateway):

    protocol=shortName 
    
    def __init__(self,username=None,password="",realname=""):
        self._namreplies={}
        self.logonUsername=username
        self.name="%s (%s)"%(username,self.protocol)
        self.password=password
        self.realname=realname
    
    def connectionMade(self):
	irc.IRCClient.connectionMade(self)
	if self.password: self.sendLine("PASS :%s"%self.password)
        self.setNick(self.logonUsername)
        self.sendLine("USER %s foo bar :%s"%(self.nickname,self.realname))

    def loseConnection(self):
	self.transport.loseConnection()

    def setNick(self,nick):
	self.username=nick
	irc.IRCClient.setNick(self,nick)

    def addContact(self,contact):
        pass

    def removeContact(self,contact):
       pass
    
    def changeStatus(self, newStatus):
        pass 

    def joinGroup(self,group):
        self.sendLine("JOIN #%s"%group)

    def leaveGroup(self,group):
        self.sendLine("PART #%s"%group)
        del self._namreplies[group]

    def getGroupMembers(self,group):
        pass # this gets automatically done

    def directMessage(self,recipientName,message):
        self.sendLine("PRIVMSG %s :%s"%(recipientName,message))

    def groupMessage(self,groupName,message):
        self.sendLine("PRIVMSG #%s :%s"%(groupName,message))

    def irc_353(self,prefix,params):
	"""
	RPL_NAMREPLY
	>> NAMES #bnl
	<< :Arlington.VA.US.Undernet.Org 353 z3p = #bnl :pSwede Dan-- SkOyg AG
	"""
	channel=params[2][1:]
	users=string.split(params[3])
	for ui in range(len(users)):
	    while users[ui][0] in ["@","+"]: # channel modes
		users[ui]=users[ui][1:]
	if not self._namreplies.has_key(channel):
	    self._namreplies[channel]=[]
	self._namreplies[channel].extend(users)

    def irc_366(self,prefix,params):
	group=params[1][1:]
	self.receiveGroupMembers(self._namreplies[group],group)

    def irc_NICK(self,prefix,params):
	oldname=string.split(prefix,"!")[0]
	self.notifyNameChanged(oldname,params[0])

    def irc_JOIN(self,prefix,params):
	nickname=string.split(prefix,"!")[0]
	if nickname!=self.nickname:
	    self.memberJoined(nickname,params[0][1:])

    def irc_PART(self,prefix,params):
	nickname=string.split(prefix,"!")[0]
	if nickname!=self.nickname:
	    self.memberLeft(nickname,params[0][1:])

    def irc_PRIVMSG(self,prefix,params):
	nickname=string.split(prefix,"!")[0]
	message=params[1]
	if params[0][0]=="#": # channel
	    self.receiveGroupMessage(nickname,params[0][1:],message)
	else:
	    if message[0]=="\001":
		if message[1:5]=="PING":
		    self.directMessage(nickname,"\001PONG %s\001"%message[6:])
		    return
	    self.receiveDirectMessage(nickname,message)

    irc_NOTICE=irc_PRIVMSG
