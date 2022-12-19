"""
Main UBX Message Protocol Class.

Created on 4 Sep 2022
:author: vdueck

Based on:
:author: semuadmin
:copyright: SEMU Consulting © 2020
:license: BSD 3-Clause
"""

import gc
from collections import OrderedDict
gc.collect()
import gnss.msg_dictionaries.exceptions as ube
import gnss.msg_dictionaries.ubxtypes_core as ubt
import gnss.msg_dictionaries.ubxtypes_get as ubg
import gnss.msg_dictionaries.ubxtypes_set as ubs
import gnss.msg_dictionaries.ubxtypes_poll as ubp
gc.collect()
from gnss.msg_dictionaries.ubxhelpers import (
    calc_checksum,
    attsiz,
    gnss2str,
    msgclass2bytes,
    msgstr2bytes,
    val2bytes,
    bytes2val,
    nomval,
    cfgkey2name,
    cfgname2key,
)
gc.collect()

class UBXMessage:
    """UBX Message Class."""

    def __init__(self, ubxclass, ubxid, msgmode: int, **kwargs):
        """Constructor.
        If no keyword parms are passed, the payload is taken to be empty.
        If 'payload' is passed as a keyword parm, this is taken to contain the complete
        payload as a sequence of bytes; any other keyword parms are ignored.
        Otherwise, any named attributes will be assigned the value given, all others will
        be assigned a nominal value according to type.
        :param object msgClass: message class as str, int or byte
        :param object msgID: message ID as str, int or byte
        :param int msgmode: message mode (0=GET, 1=SET, 2=POLL)
        :param bool parsebitfield: (kwarg) parse bitfields ('X' type attributes) Y/N
        :param bool scaling: (kwarg) apply scale factors Y/N
        :param kwargs: optional payload key/value pairs
        :raises: UBXMessageError
        """
        # object is mutable during initialisation only
        super().__setattr__("_immutable", False)
        self._mode = msgmode
        self._payload = b""
        self._length = b""
        self._checksum = b""

        self._parsebf = kwargs.get("parsebitfield", True)  # parsing bitfields Y/N?
        self._scaling = kwargs.get("scaling", True)  # apply scale factors Y/N?

        if msgmode not in (0, 1, 2):
            raise ube.UBXMessageError(f"Invalid msgmode {msgmode} - must be 0, 1 or 2.")

        # accommodate different formats of msgClass and msgID
        if isinstance(ubxclass, str) and isinstance(
            ubxid, str
        ):  # string e.g. 'CFG', 'CFG-PRT'
            (self._ubxClass, self._ubxID) = msgstr2bytes(ubxclass, ubxid)
        elif isinstance(ubxclass, int) and isinstance(ubxid, int):  # int e.g. 6, 1
            (self._ubxClass, self._ubxID) = msgclass2bytes(ubxclass, ubxid)
        else:  # bytes e.g. b'\x06', b'\x01'
            self._ubxClass = ubxclass
            self._ubxID = ubxid

        self._do_attributes(**kwargs)

        self._immutable = True  # once initialised, object is immutable
        gc.collect()

    def _do_attributes(self, **kwargs):
        """
        Populate UBXMessage from named attribute keywords.
        Where a named attribute is absent, set to a nominal value (zeros or blanks).
        :param kwargs: optional payload key/value pairs
        :raises: UBXTypeError
        """
        offset = 0  # payload offset in bytes
        index = []  # array of (nested) group indices

        try:

            if len(kwargs) == 0:  # if no kwargs, assume null payload
                self._payload = None
            else:
                self._payload = kwargs.get("payload", b"")
                pdict = self._get_dict()  # get appropriate payload dict
                for key in pdict:  # process each attribute in dict
                    (offset, index) = self._set_attribute(
                        offset, pdict, key, index, **kwargs
                    )
            self._do_len_checksum()
        except (
            AttributeError,
            TypeError,
            ValueError,
        ) as err:
            raise ube.UBXTypeError(
                (
                    "Incorrect type for attribute '{}' in {} message. class {}". format(key, self._mode, self.identity)
                )
            ) from err
        except (OverflowError,) as err:
            raise ube.UBXTypeError(
                (
                    "Overflow error for attribute '{}' in {} message. class {}".format(key, self._mode, self.identity)
                )
            ) from err

    def _set_attribute(
        self, offset: int, pdict: OrderedDict, key: str, index: list, **kwargs
    ) -> tuple:
        """
        Recursive routine to set individual or grouped payload attributes.
        :param int offset: payload offset in bytes
        :param OderedDict pdict: dict representing payload definition
        :param str key: attribute keyword
        :param list index: repeating group index array
        :param kwargs: optional payload key/value pairs
        :return: (offset, index[])
        :rtype: tuple
        """
        att = pdict[key]  # get attribute type
        if isinstance(
            att, tuple
        ):  # repeating group of attributes or subdefined bitfield
            numr, _ = att
            if numr in (ubt.X1, ubt.X2, ubt.X4, ubt.X6, ubt.X8, ubt.X24):  # bitfield
                if self._parsebf:  # if we're parsing bitfields
                    (offset, index) = self._set_attribute_bitfield(
                        att, offset, index, **kwargs
                    )
                else:  # treat bitfield as a single byte array
                    offset = self._set_attribute_single(
                        numr, offset, key, index, **kwargs
                    )
            else:  # repeating group of attributes
                (offset, index) = self._set_attribute_group(
                    att, offset, index, **kwargs
                )
        else:  # single attribute
            offset = self._set_attribute_single(att, offset, key, index, **kwargs)
        return offset, index

    def _set_attribute_group(
        self, att: tuple, offset: int, index: list, **kwargs
    ) -> tuple:
        """
        Process (nested) group of attributes.
        :param tuple att: attribute group - tuple of (num repeats, attribute dict)
        :param int offset: payload offset in bytes
        :param list index: repeating group index array
        :param kwargs: optional payload key/value pairs
        :return: (offset, index[])
        :rtype: tuple
        """
        index.append(0)  # add a (nested) group index
        numr, attd = att  # number of repeats, attribute dictionary
        # if CFG-VALGET message, use dedicated method to
        # parse as configuration key value pairs
        if (
            self._ubxClass == b"\x06"
            and self._ubxID == b"\x8b"
            and self._mode == ubt.GET
        ):
            self._set_attribute_cfgval(offset, **kwargs)
        else:
            # derive or retrieve number of items in group
            if isinstance(numr, int):  # fixed number of repeats
                rng = numr
            elif numr == "None":  # number of repeats 'variable by size'
                rng = self._calc_num_repeats(attd, self._payload, offset, 0)
            else:  # number of repeats is defined in named attribute
                rng = getattr(self, numr)
                # special handling for ESF-MEAS message types
                if (
                    self._ubxClass == b"\x10"
                    and self._ubxID == b"\x02"
                    and self._mode == ubt.SET
                ):
                    if getattr(self, "calibTtagValid", 0):
                        rng += 1
            # recursively process each group attribute,
            # incrementing the payload offset and index as we go
            for i in range(rng):
                index[-1] = i + 1
                for key1 in attd:
                    (offset, index) = self._set_attribute(
                        offset, attd, key1, index, **kwargs
                    )

        index.pop()  # remove this (nested) group index
        return offset, index

    def _set_attribute_single(
        self, att: object, offset: int, key: str, index: list, **kwargs
    ) -> int:
        """
        Set individual attribute value, applying scaling where appropriate.
        EITHER
        :param str att: attribute type string e.g. 'U002'
        OR
        :param list att: if scaled, list of [attribute type string, scaling factor float]
        :param int offset: payload offset in bytes
        :param str key: attribute keyword
        :param list index: repeating group index array
        :param kwargs: optional payload key/value pairs
        :return: offset
        :rtype: int
        """
        # if attribute is scaled
        scale = 1
        if isinstance(att, list) and self._scaling:
            scale = att[1]
            att = att[0]

        # if attribute is part of a (nested) repeating group, suffix name with index
        keyr = key
        for i in index:  # one index for each nested level
            if i > 0:
                keyr += f"_{i:02d}"

        # determine attribute size (bytes)
        if att == ubt.CH:  # variable length string
            atts = len(self._payload)
        else:
            atts = attsiz(att)

        # if payload keyword has been provided,
        # use the appropriate offset of the payload
        if "payload" in kwargs:
            valb = self._payload[offset : offset + atts]
            if scale == 1:
                val = bytes2val(valb, att)
            else:
                val = round(bytes2val(valb, att) * scale, ubt.SCALROUND)
        else:
            # if individual keyword has been provided,
            # set to provided value, else set to
            # nominal value
            val = kwargs.get(keyr, nomval(att))
            if scale == 1:
                valb = val2bytes(val, att)
            else:
                valb = val2bytes(int(val / scale), att)
            self._payload += valb

        setattr(self, keyr, val)
        offset += atts
        return offset

    def _set_attribute_bitfield(
        self, att: str, offset: int, index: list, **kwargs
    ) -> tuple:
        """
        Parse bitfield attribute (type 'X').
        :param str att: attribute type e.g. 'X002'
        :param int offset: payload offset in bytes
        :param str key: attribute key name
        :param list index: repeating group index array
        :param kwargs: optional payload key/value pairs
        :return: (offset, index[])
        :rtype: tuple
        """

        bft, bfd = att  # type of bitfield, bitfield dictionary
        bfs = attsiz(bft)  # size of bitfield in bytes
        bfoffset = 0

        # if payload keyword has been provided,
        # use the appropriate offset of the payload
        if "payload" in kwargs:
            bitfield = int.from_bytes(self._payload[offset: offset + bfs], "little")
        else:
            bitfield = 0

        # process each flag in bitfield
        for key, keyt in bfd.items():
            (bitfield, bfoffset) = self._set_attribute_bits(
                bitfield, bfoffset, key, keyt, index, **kwargs
            )

        # update payload
        offset += bfs
        if "payload" not in kwargs:
            self._payload += bitfield.to_bytes(bfs, "little")

        return offset, index

    def _set_attribute_bits(
        self,
        bitfield: int,
        bfoffset: int,
        key: str,
        keyt: str,
        index: list,
        **kwargs,
    ) -> tuple:
        """
        Set individual bit flag from bitfield.

        :param int bitfield: bitfield
        :param int bfoffset: bitfield offset in bits
        :param str key: attribute key name
        :param str keyt: key type e.g. 'U001'
        :param list index: repeating group index array
        :param kwargs: optional payload key/value pairs
        :return: (bitfield, bfoffset)
        :rtype: tuple

        """

        # if attribute is part of a (nested) repeating group, suffix name with index
        keyr = key
        for i in index:  # one index for each nested level
            if i > 0:
                keyr += f"_{i:02d}"

        atts = attsiz(keyt)  # determine flag size in bits

        if "payload" in kwargs:
            mask = pow(2, atts) - 1
            val = (bitfield >> bfoffset) & mask
        else:
            val = kwargs.get(keyr, 0)
            bitfield = bitfield | (val << bfoffset)
        if key[0:8] != "reserved":  # don't bother to set reserved bits
            setattr(self, keyr, val)
        bfoffset += atts
        return bitfield, bfoffset

    def _set_attribute_cfgval(self, offset: int, **kwargs):
        """
        Parse CFG-VALGET payload to set of configuration
        key value pairs.
        :param int offset: payload offset
        :param **kwargs:  optional payload key/value pairs
        :raises: UBXMessageError

        """

        key_len = 4
        if "payload" in kwargs:
            self._payload = kwargs["payload"]
        else:
            raise ube.UBXMessageError(
                "CFG-VALGET message definitions must include payload keyword"
            )
        cfglen = len(self._payload[offset:])

        i = 0
        while offset < cfglen:
            if i == key_len:
                key = int.from_bytes(
                    self._payload[offset: offset + key_len], "little", False
                )
                (keyname, att) = cfgkey2name(key)
                atts = attsiz(att)
                valb = self._payload[offset + key_len : offset + key_len + atts]
                val = bytes2val(valb, att)
                setattr(self, keyname, val)
                i = 0
                offset += key_len + atts

            else:
                i += 1

    def _do_len_checksum(self):
        """
        Calculate and format payload length and checksum as bytes."""

        if self._payload is None:
            self._length = val2bytes(0, ubt.U2)
            self._checksum = calc_checksum(self._ubxClass + self._ubxID + self._length)
        else:
            self._length = val2bytes(len(self._payload), ubt.U2)
            self._checksum = calc_checksum(
                self._ubxClass + self._ubxID + self._length + self._payload
            )

    def _get_dict(self) -> OrderedDict:
        """
        Get payload dictionary corresponding to message mode (GET/SET/POLL)
        Certain message types need special handling as alternate payload
        definitions exist for the same ubxClass/ubxID.

        :param kwargs: optional payload key/value pairs
        :return: dictionary representing payload definition
        :rtype: dict

        """

        try:
            if self._mode == ubt.POLL:
                pdict = ubp.UBX_PAYLOADS_POLL[self.identity]
            elif self._mode == ubt.SET:
                pdict = ubs.UBX_PAYLOADS_SET[self.identity]
            else:
                # # CFG-NMEA GET
                if self._ubxClass == b"\x06" and self._ubxID == b"\x17":
                    pdict = ubg.UBX_PAYLOADS_GET["CFG-NMEA"]
                elif self.identity[-7:] == "NOMINAL":
                    pdict = ubg.UBX_PAYLOADS_GET["UBX-NOMINAL"]
                else:
                    pdict = ubg.UBX_PAYLOADS_GET[self.identity]
            return pdict
        except KeyError as err:
            raise KeyError(
                f"{err} - Check 'msgmode' keyword argument is appropriate for message category"
            )

    def _calc_num_repeats(
        self, attd: dict, payload: bytes, offset: int, offsetend: int = 0
    ) -> int:
        """
        Deduce number of items in 'variable by size' repeating group by
        dividing length of remaining payload by length of group.
        This is predicated on there being only one such repeating group
        per message payload, which is true for all currently supported types.
        :param dict attd: grouped attribute dictionary
        :param bytes payload : raw payload
        :param int offset: number of bytes in payload before repeating group
        :param int offsetend: number of bytes in payload after repeating group
        :return: number of repeats
        :rtype: int
        """

        lenpayload = len(payload) - offset - offsetend
        lengroup = 0
        for _, val in attd.items():
            if isinstance(val, tuple):
                val, _ = val
            lengroup += attsiz(val)
        return int(lenpayload / lengroup)

    def __str__(self) -> str:
        """
        Human-readable representation.
        :return: human readable representation
        :rtype: str
        """

        clsid = None
        msgid = None

        umsg_name = self.identity
        if self.payload is None:
            return f"<UBX({umsg_name})>"

        varcount = 0
        for i, att in enumerate(self.__dict__):
            if att[0] != "_":
                varcount = varcount + 1

        stg = f"<UBX({umsg_name}, "
        for i, att in enumerate(self.__dict__):
            if att[0] != "_":  # only show public attributes
                val = self.__dict__[att]
                if att[0:6] == "gnssId":  # attribute is a GNSS ID
                    val = gnss2str(val)  # get string representation e.g. 'GPS'
                if att == "iTOW":  # attribute is a GPS Time of Week
                    val = str(val)  # show time in UTC format
                # if it's an ACK, we show what it's acknowledging in plain text
                # if it's a CFG-MSG, we show what message class/id it refers to in plain text
                if self._ubxClass == b"\x05" or (
                    self._ubxClass == b"\x06" and self._ubxID == b"\x01"
                ):
                    if att in ["clsID", "msgClass"]:
                        clsid = val2bytes(val, ubt.U1)
                        val = ubt.UBX_CLASSES.get(clsid, clsid)
                    if att == "msgID" and clsid:
                        msgid = val2bytes(val, ubt.U1)
                        val = ubt.UBX_MSGIDS.get(clsid + msgid, clsid + msgid)
                stg += att + "=" + str(val)
                varcount = varcount - 1
                if varcount > 0:
                    stg += ", "
        stg += ")>"
        return stg

    def __repr__(self) -> str:
        """
        Machine readable representation.
        eval(repr(obj)) = obj
        :return: machine readable representation
        :rtype: str
        """

        if self._payload is None:
            return f"UBXMessage({self._ubxClass}, {self._ubxID}, {self._mode})"
        return f"UBXMessage({self._ubxClass}, {self._ubxID}, {self._mode}, payload={self._payload})"

    def __setattr__(self, name, value):
        """
        Override setattr to make object immutable after instantiation.
        :param str name: attribute name
        :param object value: attribute value
        :raises: UBXMessageError
        """
        if self._immutable:
            raise ube.UBXMessageError(
                f"Object is immutable. Updates to {name} not permitted after initialisation."
            )

        super().__setattr__(name, value)

    def serialize(self) -> bytes:
        """
        Serialize message.
        :return: serialized output
        :rtype: bytes
        """
        output = ubt.UBX_HDR + self._ubxClass + self._ubxID + self._length
        output += (
            self._checksum if self._payload is None else self._payload + self._checksum
        )
        return output

    @property
    def identity(self) -> str:
        """
        Returns message identity in plain text form.
        If the message is unrecognised, the message is parsed
        to a nominal payload definition UBX-NOMINAL and
        the term 'NOMINAL' is appended to the identity.
        :return: message identity e.g. 'CFG-MSG'
        :rtype: str
        """
        try:
            # all MGA messages except MGA-DBD need to be identified by the
            # 'type' attribute - the first byte of the payload
            if self._ubxClass == b"\x13" and self._ubxID != b"\x80":
                umsg_name = ubt.UBX_MSGIDS[
                    self._ubxClass + self._ubxID + self._payload[0:1]
                ]
            else:
                umsg_name = ubt.UBX_MSGIDS[self._ubxClass + self._ubxID]
        except KeyError as err:
            # unrecognised u-blox message, parsed to UBX-NOMINAL definition
            if self._ubxClass in ubt.UBX_CLASSES:  # known class
                cls = ubt.UBX_CLASSES[self._ubxClass]
            else:  # unknown class
                cls = "UNKNOWN"
            umsg_name = (
                f"{cls}-{int.from_bytes(self._ubxClass, 'little'):02x}"
                + f"{int.from_bytes(self._ubxID, 'little'):02x}-NOMINAL"
            )
        return umsg_name

    @property
    def msg_cls(self) -> bytes:
        """
        Class id getter.
        :return: message class as bytes
        :rtype: bytes
        """
        return self._ubxClass

    @property
    def msg_id(self) -> bytes:
        """
        Message id getter.
        :return: message id as bytes
        :rtype: bytes
        """
        return self._ubxID

    @property
    def length(self) -> int:
        """
        Payload length getter.
        :return: payload length as integer
        :rtype: int
        """
        return bytes2val(self._length, ubt.U2)

    @property
    def payload(self) -> bytes:
        """
        Payload getter - returns the raw payload bytes.
        :return: raw payload as bytes
        :rtype: bytes
        """
        return self._payload

    @property
    def msgmode(self) -> int:
        """
        Message mode getter.
        :return: msgmode as integer
        :rtype: int
        """
        return self._mode

    @staticmethod
    def config_set(layers: int, transaction: int, cfg_data: list) -> object:
        """
        Construct CFG-VALSET message from an array of
        configuration database (key, value) tuples. Keys
        can be in int (keyID) or str (keyname) format.

        :param int layers: memory layer(s) (1=RAM, 2=BBR, 4=Flash)
        :param int transaction: 0=no txn, 1=start txn, 2=continue txn, 3=apply txn
        :param list cfg_data: list of up to 64 tuples (key, value)
        :return: UBXMessage CFG-VALSET
        :rtype: UBXMessage
        :raises: UBXMessageError
        """

        num = len(cfg_data)
        if num > 64:
            raise ube.UBXMessageError(
                f"Number of configuration tuples {num} exceeds maximum of 64"
            )

        version = val2bytes(0 if transaction == 0 else 1, ubt.U1)
        layers = val2bytes(layers, ubt.U1)
        transaction = val2bytes(transaction, ubt.U1)
        payload = version + layers + transaction + b"\x00"
        lis = b""

        for cfgItem in cfg_data:
            att = ""
            (key, val) = cfgItem
            if isinstance(key, str):  # if key is a string (keyname)
                (key, att) = cfgname2key(key)  # lookup keyID & attribute type
            else:
                (_, att) = cfgkey2name(key)  # lookup attribute type
            keyb = val2bytes(key, ubt.U4)
            valb = val2bytes(val, att)
            lis = lis + keyb + valb

        return UBXMessage("CFG", "CFG-VALSET", ubt.SET, payload=payload + lis)

    @staticmethod
    def config_del(layers: int, transaction: int, keys: list) -> object:
        """
        Construct CFG-VALDEL message from an array of
        configuration database keys, which can be in int (keyID)
        or str (keyname) format.
        :param int layers: memory layer(s) (2=BBR, 4=Flash)
        :param int transaction: 0=no txn, 1=start txn, 2=continue txn, 3=apply txn
        :param list keys: array of up to 64 keys as int (keyID) or string (keyname)
        :return: UBXMessage CFG-VALDEL
        :rtype: UBXMessage
        :raises: UBXMessageError
        """

        num = len(keys)
        if num > 64:
            raise ube.UBXMessageError(
                f"Number of configuration keys {num} exceeds maximum of 64"
            )

        version = val2bytes(0 if transaction == 0 else 1, ubt.U1)
        layers = val2bytes(layers, ubt.U1)
        transaction = val2bytes(transaction, ubt.U1)
        payload = version + layers + transaction + b"\x00"
        lis = b""

        for key in keys:
            if isinstance(key, str):  # if keyname as a string
                (key, _) = cfgname2key(key)  # lookup keyID
            keyb = val2bytes(key, ubt.U4)
            lis = lis + keyb

        return UBXMessage("CFG", "CFG-VALDEL", ubt.SET, payload=payload + lis)

    @staticmethod
    def config_poll(layer: int, position: int, keys: list) -> object:
        """
        Construct CFG-VALGET message from an array of
        configuration database keys, which can be in int (keyID)
        or str (keyname) format.

        :param int layer: memory layer (0=RAM, 1=BBR, 2=Flash, 7 = Default)
        :param int position: number of keys to skip before returning result
        :param list keys: array of up to 64 keys as int (keyID) or str (keyname)
        :return: UBXMessage CFG-VALGET
        :rtype: UBXMessage
        :raises: UBXMessageError

        """

        num = len(keys)
        if num > 64:
            raise ube.UBXMessageError(
                f"Number of configuration keys {num} exceeds maximum of 64"
            )

        version = val2bytes(0, ubt.U1)
        layer = val2bytes(layer, ubt.U1)
        position = val2bytes(position, ubt.U2)
        payload = version + layer + position
        lis = b""

        for key in keys:
            if isinstance(key, str):  # if keyname as a string
                (key, _) = cfgname2key(key)  # lookup keyID
            keyb = val2bytes(key, ubt.U4)
            lis = lis + keyb

        return UBXMessage("CFG", "CFG-VALGET", ubt.POLL, payload=payload + lis)
