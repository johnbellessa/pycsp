
import ctypes

# Bit patters for selecting types
PROCESS_CMD = 1<<11
CHANNEL_CMD = 1<<10
HAS_PAYLOAD = 1<<9
REQ_REPLY   = 1<<8
IS_REPLY    = 1<<7
IGN_UNKNOWN = 1<<6

ERROR_CMD = 0


"""
PROCESS_CMD and CHANNEL_CMD encodes the destination.
HAS_PAYLOAD tells the receiver, that it must read N bytes containing a payload message
REQ_REPLY informs that if the destination is not available and an error must be returned, such that the sender does not deadlock by waiting eternally for a reply
IS_REPLY informs which queue to post the incoming message to.
IGN_UNKNOWN informs that it is ok to drop this message, if the destination is not found
"""

#  CMDs for processes
LOCKTHREAD_ACQUIRE_LOCK   = PROCESS_CMD | 0 | REQ_REPLY
LOCKTHREAD_ACCEPT_LOCK    = CHANNEL_CMD | 1 | IS_REPLY
LOCKTHREAD_UNAVAILABLE    = CHANNEL_CMD | 2 | IS_REPLY 

LOCKTHREAD_NOTIFY_SUCCESS = PROCESS_CMD | 3 | IS_REPLY | HAS_PAYLOAD 
LOCKTHREAD_POISON         = PROCESS_CMD | 4 | IS_REPLY
LOCKTHREAD_RETIRE         = PROCESS_CMD | 5 | IS_REPLY
LOCKTHREAD_RELEASE_LOCK   = PROCESS_CMD | 6 | IS_REPLY | IGN_UNKNOWN
SOCKETTHREAD_SHUTDOWN     = PROCESS_CMD | 7

# CMDs for channels
CHANTHREAD_JOIN_READER    = CHANNEL_CMD | 0
CHANTHREAD_JOIN_WRITER    = CHANNEL_CMD | 1
CHANTHREAD_LEAVE_READER   = CHANNEL_CMD | 2
CHANTHREAD_LEAVE_WRITER   = CHANNEL_CMD | 3
CHANTHREAD_RETIRE_READER  = CHANNEL_CMD | 4
CHANTHREAD_RETIRE_WRITER  = CHANNEL_CMD | 5
CHANTHREAD_POISON_READER  = CHANNEL_CMD | 6
CHANTHREAD_POISON_WRITER  = CHANNEL_CMD | 7
CHANTHREAD_REGISTER       = CHANNEL_CMD | 8
CHANTHREAD_DEREGISTER     = CHANNEL_CMD | 9
CHANTHREAD_POST_READ      = CHANNEL_CMD | 10 | HAS_PAYLOAD
CHANTHREAD_POST_WRITE     = CHANNEL_CMD | 11 | HAS_PAYLOAD


def cmd2str(cmd):
"""
Translate command IDs to their string representation

Use for debugging and error messages
"""
    D = {
        ERROR_CMD:"ERROR_CMD",
        LOCKTHREAD_ACQUIRE_LOCK  :"LOCKTHREAD_ACQUIRE_LOCK",
        LOCKTHREAD_ACCEPT_LOCK   :"LOCKTHREAD_ACCEPT_LOCK",
        LOCKTHREAD_UNAVAILABLE   :"LOCKTHREAD_UNAVAILABLE",
        LOCKTHREAD_NOTIFY_SUCCESS:"LOCKTHREAD_NOTIFY_SUCCESS",
        LOCKTHREAD_POISON        :"LOCKTHREAD_POISON",
        LOCKTHREAD_RETIRE        :"LOCKTHREAD_RETIRE",
        LOCKTHREAD_RELEASE_LOCK  :"LOCKTHREAD_RELEASE_LOCK",
        SOCKETTHREAD_SHUTDOWN    :"SOCKETTHREAD_SHUTDOWN",
        CHANTHREAD_JOIN_READER   :"CHANTHREAD_JOIN_READER",
        CHANTHREAD_JOIN_WRITER   :"CHANTHREAD_JOIN_WRITER",
        CHANTHREAD_LEAVE_READER  :"CHANTHREAD_LEAVE_READER",
        CHANTHREAD_LEAVE_WRITER  :"CHANTHREAD_LEAVE_WRITER",
        CHANTHREAD_RETIRE_READER :"CHANTHREAD_RETIRE_READER",
        CHANTHREAD_RETIRE_WRITER :"CHANTHREAD_RETIRE_WRITER",
        CHANTHREAD_POISON_READER :"CHANTHREAD_POISON_READER",
        CHANTHREAD_POISON_WRITER :"CHANTHREAD_POISON_WRITER",
        CHANTHREAD_REGISTER      :"CHANTHREAD_REGISTER",
        CHANTHREAD_DEREGISTER    :"CHANTHREAD_DEREGISTER",
        CHANTHREAD_POST_READ     :"CHANTHREAD_POST_READ",
        CHANTHREAD_POST_WRITE    :"CHANTHREAD_POST_WRITE"
        }

    return D[cmd]


class Header(ctypes.Structure):
    """
    cmd : type of package
    id : string, uuid1 in bytes format
    seq_number : sequence number used for ignoring channel requests, that was left behind.
    arg : may contain the payload size following this header or a payload of a single value (long)
    _source_host,_source_port,_source_id enables the receiver to reply to a message
    """
    _fields_ = [
        ("cmd", ctypes.c_short),
        ("id", ctypes.c_char * 32),
        ("seq_number", ctypes.c_long),
        ("arg", ctypes.c_long),
        ("_source_host", ctypes.c_char * 16),
        ("_source_port", ctypes.c_int),
        ("_source_id", ctypes.c_char * 32)
        ]


