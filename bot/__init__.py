"""
Create a valhalla irc log bot.

Usage:

    python __init__.py [parameters]

Parameters
    <channel> - IRC channel name (without '#')
    <bot_nick> - IRC nickname for bot
    <valhalla_uri> - URI used for POSTing messages (do not include 'http://')
    <valhalla_user> - Username for valhalla basic authentication
    <valhalla_pass> - Password for valhalla basic authentication
"""
import binascii
import sys
import urllib2

from twisted.words.protocols import irc
from twisted.internet import protocol, reactor


class ValhallaBot(irc.IRCClient):
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
        self.join(self.factory.channel)
        print "Signed on as %s." % (self.nickname,)

    def joined(self, channel):
        print "Joined %s." % (channel,)

    def privmsg(self, user, channel, msg):
        """
        POST message to django-vallhalla API using basic authentication.
        """
#        post = urlencode()
#        urllib2.urlopen('http://' + self.uri, )
        self.msg(channel, msg)



class ValhallaBotFactory(protocol.ClientFactory):
    protocol = ValhallaBot

    def __init__(self, channel, nickname='valhalla_bot', uri, user, password):
        self.channel = channel
        self.nickname = nickname
        self.valhalla_uri = uri
        # set up basic authentication url opener
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, uri, user, password)
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)


if __name__ == "__main__":
    chan = sys.argv[1]
    nick = sys.argv[2]
    uri = sys.argv[3]
    user = sys.argv[4]
    password = sys.argv[5]
    reactor.connectTCP('irc.freenode.net', 6667, ValhallaBotFactory(
        '#' + chan, nick, uri, user, password))
    reactor.run()
