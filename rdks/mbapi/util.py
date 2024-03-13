"""smol tools that should have existed but just don't"""
import copy
import email.message
from requests_toolbelt.utils.dump import dump_response

__all__ = ['parse_mime_header', 'format_request']

# implementation of
# https://docs.python.org/3/library/cgi.html#cgi.parse_header
def parse_mime_header(header):
    """Split a MIME Content-Type string into main value and a
    dict of parameters, as the depreacted cgi.parse_header would.
    """
    msg = email.message.EmailMessage()
    msg['Content-Type'] = header
    return msg.get_content_type(), msg['Content-Type'].params

def format_request(r):
    """Wrapper of requests_toolbelt.utils.dump.dump_response().
    Return HTTP headers of the request, the response, and
    the content as a tuple of three bytearrays.
    """
    # we want to dispose proxy information in 'connection' so that
    # requests_toolbelt actually uses the correct HTTP verb
    # instead of the utterly uninformative verb CONNECT
    # (it should be in r.request.method, by the way)
    #
    # a shallow copy is good enough since we only want to
    # forge r.connection without altering the original really
    rc = copy.copy(r)
    # oh yeah, turns out Request doesn't let the connection dict
    # or the raw urllib3 request copied in __setstate__, so
    # we have to add them back to this copy....
    # (i guess it's understandable; these guys might not be picklable.)
    rc.connection = {}
    rc.raw = r.raw
    b = dump_response(rc, request_prefix=b'>', response_prefix=b'<')
    s = b.decode('utf-8')

    send = bytearray()
    back = bytearray()
    content = bytearray()

    lines = iter(b.split(b'\r\n'))
    for line in lines:
        if line == b'>':
            break
        send.extend(line[1:])
        send.extend(b'\r\n')

    line = next(lines)
    assert not line

    for line in lines:
        if line == b'<':
            break
        back.extend(line[1:])
        back.extend(b'\r\n')

    for line in lines:
        content.extend(line)
        content.extend(b'\r\n')

    return send, back, content
