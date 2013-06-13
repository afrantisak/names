##nds
network dictionary service

####Status: [![Build Status](https://travis-ci.org/afrantisak/names.png?branch=master)](https://travis-ci.org/afrantisak/names/builds)

The dictionary is essentially a multimap of string to strings.  Each entry(key) can have multiple definitions(values).  The networking is modeled after the ZeroMQ "[Brutal Shotgun Massacre](http://zguide.zeromq.org/page:all#toc110)" pattern, in that the client sends out identical requests to all servers.  The first server to respond wins, and all subsequent responses are ignored.

* Use cases:
    1. Client requests definitions for an entry.  Server returns all definitions for that entry. 
    1. Client pushes a new definition for an entry.  Server returns all definitions for that entry (plus the new definition).
    1. Client removes a definition for an entry.  Server returns all definitions for that entry (minus the one that was removed)
    1. Client requests all definitions for all entries.  Server returns all definitions for all entries.  This happens on server startup to handle server late-join or restart scenarios.  The server in this case acts like a client and requests the dictionary dump from its peers.
