import socket
import time

class Client(object):
    def __init__(self, host="127.0.0.1", port=5555):
        self._host = host
        self._port = port
        keys=['æ','Æ','œ','Œ','̀','́','à','á','è','é','ì','í','ò','ó','ù','ú','À','Á','È','É','Ì','Í','Ò','Ó','Ù','Ú',
            '̄','̆','ā','ă','ē','ĕ','ī','ĭ','ō','ŏ','ū','ŭ','Ā','Ă','Ē','Ĕ','Ī','Ĭ','Ō','Ŏ','Ū','Ŭ']
        vals = ['ae','Ae','oe','Oe','','','a','a','e','e','i','i','o','o','u','u','A','A','E','E','I','I','O','O','U','U',
            '','','a','a','e','e','i','i','o','o','u','u','A','A','E','E','I','I','O','O','U','U']
        d = dict(zip(keys,vals))
        self._accent_trans = str.maketrans(d)

    def _run_remote_command(self, cmd):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((self._host, self._port))
            sock.sendall((cmd).encode('utf8'))
            chunks = []
            while True:
                try:
                    chunk = sock.recv(4096)
                    chunks.append(chunk)
                except socket.timeout:
                    # the only time this should happen is if the server sends
                    # precisely 4096 bytes of data. We'd then try to recv again
                    # and block forever.
                    break
                if len(chunk) < 4096:
                    break
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()

            out = b''.join(chunks).decode('utf-8')
            return out

    def _handle_command(self, cmd_str, strip_accents):
        count = 5
        results = []
        while count > 0:
            out = self._run_remote_command(cmd_str)
            if strip_accents:
                out = out.translate(self._accent_trans)
            results = [l.split('\t') for l in out.split('\n')]
            if not all(len(tag) >= 4 for tag in results):
                count -= 1
                time.sleep(1)
                continue
            else:
                return results
        return results

    def tag_best(self, latin_string, strip_accents=True):
        return self._handle_command(('-P2 "{}"').format(latin_string), strip_accents)

    def tag(self, latin_string, strip_accents=True):
        return self._handle_command(('-P3 "{}"').format(latin_string), strip_accents)

