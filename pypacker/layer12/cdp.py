"""Cisco Discovery Protocol."""

import struct
from pypacker import pypacker, checksum

CDP_DEVID		= 1	# string
CDP_ADDRESS		= 2
CDP_PORTID		= 3	# string
CDP_CAPABILITIES	= 4	# 32-bit bitmask
CDP_VERSION		= 5	# string
CDP_PLATFORM		= 6	# string
CDP_IPPREFIX		= 7

CDP_VTP_MGMT_DOMAIN	= 9	# string
CDP_NATIVE_VLAN		= 10	# 16-bit integer
CDP_DUPLEX		= 11	# 8-bit boolean
CDP_TRUST_BITMAP	= 18	# 8-bit bitmask0x13
CDP_UNTRUST_COS		= 19	# 8-bit port
CDP_SYSTEM_NAME		= 20	# string
CDP_SYSTEM_OID		= 21	# 10-byte binary string
CDP_MGMT_ADDRESS	= 22	# 32-bit number of addrs, Addresses
CDP_LOCATION		= 23	# string


class CDP(pypacker.Packet):
	__hdr__ = (
	("version", "B", 2),
	("ttl", "B", 180),
	("sum", "H", 0)
	)

	class Address(pypacker.Packet):
		# XXX - only handle NLPID/IP for now
		__hdr__ = (
			("ptype", "B", 1),	# protocol type (NLPID)
			("plen", "B", 1),	# protocol length
			("p", "B", 0xcc),	# IP
			("alen", "H", 4)	# address length
			)

		def _dissect(self, buf):
			self.data = self.data[struct.unpack(">H", buf[3:5])[0]:]

	class TLV(pypacker.Packet):
		__hdr__ = (
		("type", "H", 0),
		("len", "H", 4)
		)

		def _dissect(self, buf):
			pypacker.Packet._unpack(self, buf)
			self.data = self.data[:self.len - 4]
			if self.type == CDP_ADDRESS:
				n = struct.unpack(">I", self.data[:4])[0]
				buf = self.data[4:]
				l = []
				for i in range(n):
					a = CDP.Address(buf)
					l.append(a)
					buf = buf[len(a):]
				self.data = l

		def __len__(self):
			if self.type == CDP_ADDRESS:
				n = 4 + sum(map(len, self.data))
			else:
				n = len(self.data)
			return self._hdr_len + n

		def __str__(self):
			self.len = len(self)
			if self.type == CDP_ADDRESS:
				s = struct.pack(">I", len(self.data)) + \
					"".join(map(str, self.data))
			else:
				s = self.data
			return self.pack_hdr() + s

	def _dissect(self, buf):
		pypacker.Packet._unpack(self, buf)
		buf = self.data
		l = []
		while buf:
			tlv = self.TLV(buf)
			l.append(tlv)
			buf = buf[len(tlv):]
		self.data = l

	def __len__(self):
		return self._hdr_len + sum(map(len, self.data))

	def __str__(self):
		data = "".join(map(str, self.data))
		if not self.sum:
			self.sum = checksum.in_cksum(self.pack_hdr() + data)
		return self.pack_hdr() + data
