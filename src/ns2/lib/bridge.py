import asyncio

from dbus_next import Message
from dbus_next.constants import BusType
from dbus_next.aio import MessageBus
from dbus_next.errors import InvalidBusNameError
from ns2.utils import log

# app bus is a dbus connection over tcp via localhost:3000 called a bridge
BRIDGE: MessageBus = None


async def SetupBridge(_username: str) -> str:
    """on new user session create new bridge, cancel old one?, returns connected instance"""
    # 1. get ref, clean it up
    # 2. new ref, build it for user
    # 3. connect, check connection
    # 4. if its good return name, else false...?
    currentBridge = GetBridge()
    if currentBridge is not None:
        await CleanupBridge()

    rsp = await CallMakeBridge(_username)
    if rsp.error_name is not None:
        return rsp.body[0]
    await asyncio.sleep(0.25)
    bus = MessageBus(bus_address="tcp:host=localhost,port=3000")
    await bus.connect()

    if bus.connected:
        log.info("new bridge connected")
        SetBridge(bus)
        await CallMakeTerminal(_username)

        return await GetActiveUser()
    else:
        return False


async def CleanupBridge():
    global BRIDGE
    try:
        if BRIDGE:
            term = await GetTerminalPid()
            if term > 0:
                await CallCloseTerminal()
            BRIDGE.disconnect()
            await BRIDGE.wait_for_disconnect()
            await CallCloseBridge()

    except EOFError as e:
        log.info(e)

    finally:
        BRIDGE = None


def GetBridge() -> MessageBus:
    global BRIDGE
    return BRIDGE


def SetBridge(bus: MessageBus):
    global BRIDGE
    BRIDGE = bus


async def GetActiveUser() -> str:

    rsp = await BridgeCall(
        destination="com.novus.ns",
        path="/com/novus/ns",
        interface="com.novus.ns.bridge",
        member="GetActiveUser",
        signature="",
        body=[],
    )

    return rsp.body[0]


async def CheckBridge(username: str) -> bool:
    """Checks if user matches bridge"""
    return username == await GetActiveUser()


async def CanOpenDialog(username) -> Message:

    return await BridgeCall(
        destination="com.novus.ns",
        path="/com/novus/ns",
        interface="com.novus.ns.bridge",
        member="IsUserAdmin",
        signature="s",
        body=[username],
    )


async def IsUserAdmin(username) -> Message:
    return await BridgeCall(
        destination="com.novus.ns",
        path="/com/novus/ns",
        interface="com.novus.ns.bridge",
        member="IsUserAdmin",
        signature="s",
        body=[username],
    )


async def BridgeCall(
    destination: str, path: str, interface: str, member: str, signature: str, body
) -> Message:
    """Connect to proxy bus, make call return response"""
    b = GetBridge()
    try:
        msg = Message(
            destination=destination,
            path=path,
            interface=interface,
            member=member,
            signature=signature,
            body=body,
        )
        rsp = await b.call(msg)

        return rsp
    except EOFError as e:
        log.info(f"EOFError: Bridge closed: {e}")

        await CleanupBridge()

        err = Message.new_error(
            msg, error_name=interface, error_text="no bridge response"
        )
        log.info(msg)
        log.info(err.interface)
        log.info(err.member)
        return err
    
    except InvalidBusNameError as e:
        err = Message.new_error(
            msg, error_name=interface, error_text="missing serivce?"
        )
        log.info(msg)
        log.info(err.interface)
        log.info(err.member)
        return err


async def BusCall(
    destination: str, path: str, interface: str, member: str, signature: str, body
) -> Message:
    """Connect to system bus, no proxy, make a call, return reponse, disconnect"""
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    rsp = await bus.call(
        Message(
            destination=destination,
            path=path,
            interface=interface,
            member=member,
            signature=signature,
            body=body,
        )
    )
    bus.disconnect()
    return rsp


async def CallPamAuthenticate(username, password) -> Message:

    return await BusCall(
        destination="com.novus.ns",
        path="/com/novus/ns",
        interface="com.novus.ns.pam",
        member="Authenticate",
        signature="ss",
        body=[username, password],
    )


async def GetBridgePid():
    rsp = await BusCall(
        destination="com.novus.ns",
        path="/com/novus/ns",
        interface="org.freedesktop.DBus.Properties",
        member="Get",
        signature="ss",
        body=["com.novus.ns.bridge", "pid"],
    )

    return rsp.body[0].value


async def GetTerminalPid():
    rsp = await BusCall(
        destination="com.novus.ns",
        path="/com/novus/ns",
        interface="org.freedesktop.DBus.Properties",
        member="Get",
        signature="ss",
        body=["com.novus.ns.bridge", "term"],
    )

    return rsp.body[0].value


async def CallCloseBridge():
    rsp = await BusCall(
        destination="com.novus.ns",
        path="/com/novus/ns",
        interface="com.novus.ns.bridge",
        member="Close",
        signature="",
        body=[],
    )

    return rsp


async def CallCloseTerminal():
    rsp = await BusCall(
        destination="com.novus.ns",
        path="/com/novus/ns",
        interface="com.novus.ns.bridge",
        member="CloseTerminal",
        signature="",
        body=[],
    )
    return rsp


async def CallMakeBridge(username: str) -> Message:
    """returns pid of bridge"""

    rsp = await BusCall(
        destination="com.novus.ns",
        path="/com/novus/ns",
        interface="com.novus.ns.bridge",
        member="Make",
        signature="s",
        body=[username],
    )

    if rsp.error_name is not None:
        log.info("failed to make bridge for: " + username)

    return rsp


async def CallMakeTerminal(username: str) -> int:
    """returns pid of 'terminal' session"""

    rsp = await BridgeCall(
        "com.novus.ns",
        "/com/novus/ns",
        "com.novus.ns.bridge",
        "Terminal",
        "s",
        [username],
    )

    log.info(rsp.body)

    if rsp.error_name is not None:
        log.info(rsp.error_name)
        return rsp.error_name

    return int(rsp.body[0])
