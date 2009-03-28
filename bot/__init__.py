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
from datetime import datetime
import sys
import urllib2

from twisted.words.protocols import irc
from twisted.internet import protocol, reactor
from django.utils import simplejson


def install_opener(uri, user, password):
    """
    Set up basic authentication url opener
    """
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, uri, user, password)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler)
    return opener


class ValhallaBot(irc.IRCClient):
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
        self.join(self.factory.channel)
        print "Signed on as %s." % (self.nickname,)

    def joined(self, channel):
        print "Joined %s." % (channel,)

    def _msg_to_deed_json(self, user, msg):
        deed, msg = self._process_commands(msg)
        if not msg: return None
        speaker = user.split("!", 1)[0]
        deed_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        # deed must be a list of one
        deed.update({'pk': 1,
                'model': 'valhalla.deed',
                'fields': {
                    'text': msg,
                    'deed_date': deed_date,
                    'speaker': speaker,
                    'user': 1
                 }
               })
        return simplejson.dumps([deed])

    def _process_commands(self, msg):
        if msg.startswith('twitter:'):
            return {'dispatch': ['twitter']}, msg[8:].strip()
        elif msg.startswith('otr:'):
            return {}, None
        return {}, msg

    def privmsg(self, user, channel, msg):
        """
        POST message to django-vallhalla API using basic authentication.
        """
        if user and user.rfind('!') > 0:
            deed_json = self._msg_to_deed_json(user, msg)
            if not deed_json: return None
            request = urllib2.Request('http://' + self.valhalla_uri, deed_json)
            request.add_header('Content-Type', 'application/json')
            try:
                self.opener.open(request)
            except urllib2.HTTPError, e:
                print e.msg
                pass


class ValhallaBotFactory(protocol.ClientFactory):
    protocol = ValhallaBot

    def __init__(self, channel, nickname, uri, user, password):
        self.channel = channel
        self.nickname = nickname
        self.valhalla_uri = uri
        self.opener = install_opener('http://' + uri, user, password)

    def buildProtocol(self, addr):
        """
        Overridden to add our valhalla uri to the ValhallaBot.
        """
        p = self.protocol()
        p.factory = self
        p.valhalla_uri = self.valhalla_uri
        p.opener = self.opener
        return p

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)


if __name__ == "__main__":
    # get commandline args
    chan = sys.argv[1]
    nick = sys.argv[2]
    uri = sys.argv[3]
    user = sys.argv[4]
    password = sys.argv[5]

    # calls to urllib2.urlopen will use the installed opener
    install_opener(uri, user, password)

    # start bot
    reactor.connectTCP('irc.freenode.net', 6667, ValhallaBotFactory(
        '#' + chan, nick, uri, user, password))
    reactor.run()
