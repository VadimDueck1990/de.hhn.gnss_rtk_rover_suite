"""
The MIT License (MIT)
Copyright © 2018 Jean-Christophe Bos & HC² (www.hc2.fr)

Modified to run asynchronous on 28 Nov 2022
:author: vdueck
"""

from   hashlib     import sha1
from   binascii    import b2a_base64
from   struct      import pack
from   _thread     import start_new_thread, allocate_lock
import gc

import uasyncio


class MicroWebSocket :

    # ============================================================================
    # ===( Constants )============================================================
    # ============================================================================

    _handshakeSign = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    _opContFrame   = 0x0
    _opTextFrame   = 0x1
    _opBinFrame    = 0x2
    _opCloseFrame  = 0x8
    _opPingFrame   = 0x9
    _opPongFrame   = 0xA
    
    _msgTypeText   = 1
    _msgTypeBin    = 2

    # ============================================================================
    # ===( Utils  )===============================================================
    # ============================================================================

    @staticmethod
    def _tryAllocByteArray(size) :
        for x in range(10) :
            try :
                gc.collect()
                return bytearray(size)
            except :
                pass
        return None

    # ----------------------------------------------------------------------------

    @staticmethod
    def _tryStartThread(func, args=()) :
        for x in range(10) :
            try :
                gc.collect()
                start_new_thread(func, args)
                return True
            except :
                global _mws_thread_id
                try :
                    _mws_thread_id += 1
                except :
                    _mws_thread_id = 0
                try :
                    start_new_thread('MWS_THREAD_%s' % _mws_thread_id, func, args)
                    return True
                except :
                    pass
        return False

    # ============================================================================
    # ===( Constructor )==========================================================
    # ============================================================================

    def __init__(self) :
        self._sreader           = None
        self._swriter           = None
        self._httpCli           = None
        self._closed            = True
        self._lock              = None
        self.RecvTextCallback   = None
        self.RecvBinaryCallback = None
        self.ClosedCallback     = None


    async def run(self, sreader: uasyncio.StreamReader, swriter: uasyncio.StreamWriter, httpClient, httpResponse, maxRecvLen, acceptCallback) :
        self._sreader           = sreader
        self._swriter           = swriter
        self._httpCli           = httpClient
        self._closed            = True
        self._lock              = allocate_lock()
        self.RecvTextCallback   = None
        self.RecvBinaryCallback = None
        self.ClosedCallback     = None

        print("inside websocket.run(): starting ws task")
        if await self._handshake(httpResponse) :
            self._ctrlBuf = MicroWebSocket._tryAllocByteArray(0x7D)
            self._msgBuf  = MicroWebSocket._tryAllocByteArray(maxRecvLen)
            if self._ctrlBuf and self._msgBuf :
                self._msgType = None
                self._msgLen  = 0
                await self._wsProcess(acceptCallback)
                return
            print("MicroWebSocket : Out of memory on new WebSocket connection.")
        try :
            await self._sreader.wait_closed()
            await self._swriter.wait_closed()
        except :
            pass

    # ============================================================================
    # ===( Functions )============================================================
    # ============================================================================

    async def _handshake(self, httpResponse) :
        try :
            key = self._httpCli.GetRequestHeaders().get('sec-websocket-key', None)
            if key :
                key += self._handshakeSign
                r = sha1(key.encode()).digest()
                r = b2a_base64(r).decode().strip()
                await httpResponse.WriteSwitchProto("websocket", { "Sec-WebSocket-Accept" : r })
                return True
        except :
            pass
        return False

    # ----------------------------------------------------------------------------

    async def _wsProcess(self, acceptCallback) :
        self._closed = False
        # try :
        await acceptCallback(self, self._httpCli)
        # except Exception as ex :
        #     print("MicroWebSocket : Error on accept callback (%s)." % str(ex))
        while not self._closed :
            result = await self._receiveFrame()
            if not result :
                await uasyncio.sleep(1)
                await self.Close()
        if self.ClosedCallback :
            # try :
            await self.ClosedCallback(self)
            # except Exception as ex :
            #     print("MicroWebSocket : Error on closed callback (%s)." % str(ex))

    # ----------------------------------------------------------------------------

    async def _receiveFrame(self) :
        try :
            b = await self._sreader.read(2)
            if not b or len(b) != 2 :
                return False

            fin    = b[0] & 0x80 > 0
            opcode = b[0] & 0x0F
            masked = b[1] & 0x80 > 0
            length = b[1] & 0x7F

            if opcode == self._opContFrame and not self._msgType :
                return False
            elif opcode == self._opTextFrame :
                self._msgType = self._msgTypeText
            elif opcode == self._opBinFrame :
                self._msgType = self._msgTypeBin

            if length == 0x7E :
                b = await self._sreader.read(2)
                if not b or len(b) != 2 :
                    return False
                length = (b[0] << 8) + b[1]
            elif length == 0x7F :
                return False
            mask = await self._sreader.read(4) if masked else None
            if masked and (not mask or len(mask) != 4) :
                return False
            if opcode == self._opContFrame or \
               opcode == self._opTextFrame or \
               opcode == self._opBinFrame :
                if length > 0 :
                    buf = memoryview(self._msgBuf)[self._msgLen:]
                    if length > len(buf) :
                        return False
                    x = await self._sreader.readinto(buf[0:length])
                    if x != length :
                        return False
                    if masked :
                        for i in range(length) :
                            idx = self._msgLen + i
                            self._msgBuf[idx] ^= mask[i%4]
                    self._msgLen += length
                    if fin :
                        b = bytes(memoryview(self._msgBuf)[:self._msgLen])
                        if self._msgType == self._msgTypeText :
                            if self.RecvTextCallback :
                                try :
                                    await self.RecvTextCallback(self, b.decode())
                                except Exception as ex :
                                    print("MicroWebSocket : Error on recv text callback (%s)." % str(ex))
                        else :
                            if self.RecvBinaryCallback :
                                try :
                                    await self.RecvBinaryCallback(self, b)
                                except Exception as ex :
                                    print("MicroWebSocket : Error on recv binary callback (%s)." % str(ex))
                        self._msgType = None
                        self._msgLen  = 0
                else :
                    return False

            elif opcode == self._opPingFrame :

                if length > len(self._ctrlBuf) :
                    return False
                if length > 0 :
                    x = await self._sreader.readinto(self._ctrlBuf[0:length])
                    if x != length :
                        return False
                    pingData = memoryview(self._ctrlBuf)[:length]
                else :
                    pingData = None
                await self._sendFrame(self._opPongFrame, pingData)

            elif opcode == self._opCloseFrame :
                await self.Close()

        except :
            return False

        print("inside websocket._receiveFrame(): SUCCESS")
        return True

    # ----------------------------------------------------------------------------

    async def _sendFrame(self, opcode, data=None, fin=True) :
        if not self._closed and opcode >= 0x00 and opcode <= 0x0F :
            dataLen = 0 if not data else len(data)
            if dataLen <= 0xFFFF :
                b1 = (0x80 | opcode) if fin else opcode
                b2 = 0x7E if dataLen >= 0x7E else dataLen
                # try :
                msg = pack('>BB', b1, b2)
                self._swriter.write(msg)
                await self._swriter.drain()
                if dataLen > 0 :
                    if dataLen >= 0x7E :
                        self._swriter.write(pack('>H', dataLen))
                        await self._swriter.drain()
                    self._swriter.write(data)
                    await self._swriter.drain()
                    ret = True
                else:
                    ret = True
                return ret
        return False

    # ----------------------------------------------------------------------------

    async def SendText(self, msg) :
        return await self._sendFrame(self._opTextFrame, msg.encode())

    # ----------------------------------------------------------------------------

    async def SendBinary(self, data) :
        return await self._sendFrame(self._opBinFrame, data)

    # ----------------------------------------------------------------------------

    def IsClosed(self) :
        return self._closed

    # ----------------------------------------------------------------------------

    async def Close(self) :
        print("closing websocket")
        if not self._closed :
            try :
                self._closed = True
                await self._sendFrame(self._opCloseFrame)
                await self._sreader.wait_closed()
                await self._swriter.wait_closed()
            except :
                pass

    # ============================================================================
    # ============================================================================
    # ============================================================================

