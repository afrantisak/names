##nds
network dictionary service

####Status: [![Build Status](https://travis-ci.org/afrantisak/names.png?branch=master)](https://travis-ci.org/afrantisak/names/builds)

Modeled after the "[Brutal Shotgun Massacre](http://zguide.zeromq.org/page:all#toc110)" pattern.
* Client sends out identical requests to all servers.  The first server to respond wins, and all subsequent responses are ignored.
* Examples:
    1. Client requests definitions for a key.  Server returns all known definitions for that key. 
    1. Client pushes new definition for a key.  Server returns all known definitions for that key (plus the new definition).
    1. Client removes definition for a key.  Server returns all known definition for that key (minus the one that was removed)
    1. Server requests definitions for all keys from a peer.  Peer server returns all known definitions for all keys.  This happens on server startup to handle server late-join scenarios.
* Multiple keys and definitions can be requested, pushed and removed all in the same message from clients.  Multiple keys and definitions can be returned all in the same message from servers.
