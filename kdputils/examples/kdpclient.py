#!/usr/bin/env python
import argparse
import socket

import kdputils.protocol
import kdputils.requests
from kdputils.protocol import KDPRequest


class KDPClient:
    def __init__(self, kdpserver_host):
        self.sock_reply = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_reply.bind(("0.0.0.0", 0))
        _, self.req_reply_port = self.sock_reply.getsockname()

        self.sock_exc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_exc.bind(("0.0.0.0", 0))
        _, self.exc_note_port = self.sock_exc.getsockname()

        self.kdpserver_host = kdpserver_host
        self.seqid = 0
        self.sesskey = 0x1337

    def __enter__(self):
        self._reattach()
        self._connect()
        return self

    def __exit__(self, *exc):
        self._reattach()

    def send_req_and_recv_reply(self, reqpkt):
        kdputils.protocol.send(
            self.sock_reply,
            (self.kdpserver_host, kdputils.protocol.KDP_REMOTE_PORT),
            reqpkt,
            self.seqid,
            self.sesskey,
        )
        replypkt, _ = kdputils.protocol.recv(self.sock_reply)
        return replypkt

    def _reattach(self):
        self.seqid = 0
        replypkt = self.send_req_and_recv_reply(
            kdputils.requests.kdp_reattach(self.req_reply_port)
        )
        assert replypkt["is_reply"] and replypkt["request"] == KDPRequest.KDP_REATTACH

    def _connect(self):
        replypkt = self.send_req_and_recv_reply(
            kdputils.requests.kdp_connect(
                self.req_reply_port, self.exc_note_port, b"<o/"
            )
        )
        self.seqid += 1
        assert replypkt["is_reply"] and replypkt["request"] == KDPRequest.KDP_CONNECT

    def get_kernelversion(self):
        replypkt = self.send_req_and_recv_reply(kdputils.requests.kdp_kernelversion())
        assert (
            replypkt["is_reply"] and replypkt["request"] == KDPRequest.KDP_KERNELVERSION
        )
        self.seqid += 1
        return replypkt["version"].decode("ascii")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("host")
    args = parser.parse_args()

    with KDPClient(args.host) as kdpclient:
        kernelversion = kdpclient.get_kernelversion()
        print(kernelversion)
