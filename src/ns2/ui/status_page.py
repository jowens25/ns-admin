import asyncio
from datetime import datetime
import time
from ns2.utils import log
from nicegui import ui
from ns2.ui.control_panel import controlPanel

LastSeen = "last"
Visible = "visible"
Time = "Time (UTC)"
Date = "Date"
GPS1 = "GPS1 Lock"
GPS2 = "GPS2 Lock"
Sats1 = "Sats1 In View"
Sats2 = "Sats2 In View"
Channel = "Channel Faults"
Power = "Power Supply Faults"
Error = "Error Message"
Antenna1 = "Antenna1 Status"
Antenna2 = "Antenna2 Status"


string1Map = {
    LastSeen: 0,
    Visible: False,
    Time: "",
    Date: "",
    GPS1: "",
    GPS2: "",
    Sats1: "",
    Sats2: "",
    Channel: "",
    Power: "",
    Error: "",
    Antenna1: "",
    Antenna2: "",
}


Ch1Vrms = "Ch1 Vrms"
Ch2Vrms = "Ch2 Vrms"
Ch3Vrms = "Ch3 Vrms"
Ch4Vrms = "Ch4 Vrms"
Ch5Vrms = "Ch5 Vrms"
Ch6Vrms = "Ch6 Vrms"
Ch7Vrms = "Ch7 Vrms"
Ch8Vrms = "Ch8 Vrms"


string2Map = {
    LastSeen: 0,
    Visible: False,
    Time: "",
    Date: "",
    Ch1Vrms: "",
    Ch2Vrms: "",
    Ch3Vrms: "",
    Ch4Vrms: "",
    Ch5Vrms: "",
    Ch6Vrms: "",
    Ch7Vrms: "",
    Ch8Vrms: "",
}


Ps1 = "Ps1 V"
Ps2 = "Ps2 V"
Ps3 = "Ps3 V"
Ps4 = "Ps4 V"
Ps5 = "Ps5 V"
Ps6 = "Ps6 V"
Ps7 = "Ps7 V"
Ps8 = "Ps8 V"
BIT = "BIT"

Temperature = "Temperature (C)"
string3Map = {
    LastSeen: 0,
    Visible: False,
    Time: "",
    Date: "",
    Ps1: "",
    Ps2: "",
    Ps3: "",
    Ps4: "",
    Ps5: "",
    Ps6: "",
    Ps7: "",
    Ps8: "",
    BIT: "",
    Temperature: "",
}


Ch9Vrms = "Ch9 Vrms"
Ch10Vrms = "Ch10 Vrms"
Ch11Vrms = "Ch11 Vrms"
Ch12Vrms = "Ch12 Vrms"
Ch13Vrms = "Ch13 Vrms"
Ch14Vrms = "Ch14 Vrms"
Ch15Vrms = "Ch15 Vrms"
Ch16Vrms = "Ch16 Vrms"

string4Map = {
    LastSeen: 0,
    Visible: False,
    Time: "",
    Date: "",
    Ch9Vrms: "",
    Ch10Vrms: "",
    Ch11Vrms: "",
    Ch12Vrms: "",
    Ch13Vrms: "",
    Ch14Vrms: "",
    Ch15Vrms: "",
    Ch16Vrms: "",
}

Pot = "Potentiometer"
FanPwm = "Fan PWM %"

string5Map = {
    LastSeen: 0,
    Visible: False,
    Time: "",
    Date: "",
    Pot: "",
    FanPwm: "",
    Temperature: "",
}


ActivePCBAssembly = "Active PCB Assembly"
GNSSLock = "GNSS Lock"
InputError = "Input Error"
ChannelStatusWord = "Channel Status Word"
PrimaryPSStatus = "Primary PS Status"
SecondaryPSStatus = "Secondary PS Status"
ActivePCBStatus = "Active PCB Status"
ChecksumStatus = "Checksum Status"
ChannelFaultBin = "Channel Fault Bin"
PrimaryPCBAmpStatus = "Primary PCB Amp Status"
BackupPCBAmpStatus = "Backup PCB Amp Status"


SatsInView = "Satelites In View"
ErrorByte = "Error Byte"
FreqDiff = "Frequency Difference"
PPSDiff = "PPS Difference"
FreqCorrectionSlice = "Frequency Correction Slice"
DACValue = "DAC Value"


string6Map = {
    LastSeen: 0,
    Visible: False,
    ActivePCBAssembly: "",
    GNSSLock: "",
    InputError: "",
    ChannelStatusWord: "",
    PrimaryPSStatus: "",
    SecondaryPSStatus: "",
    ActivePCBStatus: "",
    ChecksumStatus: "",
    ChannelFaultBin: "",
    PrimaryPCBAmpStatus: "",
    BackupPCBAmpStatus: "",
}

string7Map = {
    LastSeen: 0,
    Visible: False,
    Time: "",
    Date: "",
    GNSSLock: "",
    SatsInView: "",
    ErrorByte: "",
    FreqDiff: "",
    PPSDiff: "",
    FreqCorrectionSlice: "",
    DACValue: "",
    Ps1: "",
    Ps2: "",
}


def parseGps(string: str):
    if string == "A":
        return "Valid"
    elif string == "V":
        return "Not Valid"
    else:
        return string


def parseTime(string: str):

    if string == "" or string == "":
        return string

    try:
        time_str = f"{int(string):06d}"
        dt_obj = datetime.strptime(time_str, "%H%M%S")
        return dt_obj.time()

    except Exception as e:
        log.info(e)
        return string


def parseDate(string: str):

    if string == "" or string == "":
        return string
    try:
        dt_object = datetime.strptime(string, "%m%d%y")
        return dt_object.date()
    except Exception as e:
        log.info(e)
        return string


def parseSats(string: str):
    if string == "N":
        return "N/A"
    else:
        return string


def parseAnt(string: str):
    if string == "0":
        return "Ok"
    elif string == "1":
        return "Error"
    else:
        return string


def parseBit(string: str):
    if string == "0":
        return "Ok"
    elif string == "1":
        return "Fail"
    else:
        return string


def parseGpsOther(string: str):
    if string == "A":
        return "Locked"
    elif string == "V":
        return "Unlocked"
    else:
        return string


def parseInputError(string: str):
    if string == "0":
        return "Ok"
    elif string == "1":
        return "A Error"
    elif string == "2":
        return "B Error"
    else:
        return string


def parseString1(string: str):
    string1Map[LastSeen] = time.monotonic()
    string = string.split("*")[0]
    fields = string.split(",")
    if len(fields) == 13:
        string1Map[Visible] = True
        string1Map[Time] = parseTime(fields[2])
        string1Map[Date] = parseDate(fields[3])
        string1Map[GPS1] = parseGps(fields[4])
        string1Map[GPS2] = parseGps(fields[5])
        string1Map[Sats1] = parseSats(fields[6])
        string1Map[Sats2] = parseSats(fields[7])
        string1Map[Channel] = fields[8]
        string1Map[Power] = fields[9]
        string1Map[Error] = fields[10]
        string1Map[Antenna1] = parseAnt(fields[11])
        string1Map[Antenna2] = parseAnt(fields[12])


def parseString2(string: str):
    string2Map[LastSeen] = time.monotonic()
    string = string.split("*")[0]
    fields = string.split(",")
    if len(fields) == 13:
        string2Map[Visible] = True
        string2Map[Time] = parseTime(fields[2])
        string2Map[Date] = parseDate(fields[3])
        string2Map[Ch1Vrms] = fields[4]
        string2Map[Ch2Vrms] = fields[5]
        string2Map[Ch3Vrms] = fields[6]
        string2Map[Ch4Vrms] = fields[7]
        string2Map[Ch5Vrms] = fields[8]
        string2Map[Ch6Vrms] = fields[9]
        string2Map[Ch7Vrms] = fields[10]
        string2Map[Ch8Vrms] = fields[11]


def parseString3(string: str):
    string3Map[LastSeen] = time.monotonic()
    string = string.split("*")[0]
    fields = string.split(",")
    if len(fields) == 15:
        string3Map[Visible] = True
        string3Map[Time] = parseTime(fields[2])
        string3Map[Date] = parseDate(fields[3])
        string3Map[Ps1] = fields[4]
        string3Map[Ps2] = fields[5]
        string3Map[Ps3] = fields[6]
        string3Map[Ps4] = fields[7]
        string3Map[Ps5] = fields[8]
        string3Map[Ps6] = fields[9]
        string3Map[Ps7] = fields[10]
        string3Map[Ps8] = fields[11]
        string3Map[BIT] = parseBit(fields[12])
        string3Map[Temperature] = fields[13]


def parseString4(string: str):
    string4Map[LastSeen] = time.monotonic()
    string = string.split("*")[0]
    fields = string.split(",")
    if len(fields) == 13:
        string4Map[Visible] = True
        string4Map[Time] = parseTime(fields[2])
        string4Map[Date] = parseDate(fields[3])
        string4Map[Ch9Vrms] = fields[4]
        string4Map[Ch10Vrms] = fields[5]
        string4Map[Ch11Vrms] = fields[6]
        string4Map[Ch12Vrms] = fields[7]
        string4Map[Ch13Vrms] = fields[8]
        string4Map[Ch14Vrms] = fields[9]
        string4Map[Ch15Vrms] = fields[10]
        string4Map[Ch16Vrms] = fields[11]


def parseString5(string: str):
    string5Map[LastSeen] = time.monotonic()
    string = string.split("*")[0]
    fields = string.split(",")
    if len(fields) >= 7:
        string5Map[Visible] = True
        string5Map[Time] = parseTime(fields[2])
        string5Map[Date] = parseDate(fields[3])
        string5Map[Pot] = fields[4]
        string5Map[FanPwm] = fields[5]
        string5Map[Temperature] = fields[7]


def parseString6(string: str):
    string6Map[LastSeen] = time.monotonic()
    string = string.split("*")[0]
    fields = string.split(",")
    if len(fields) >= 10:
        string6Map[Visible] = True
        string6Map[ActivePCBAssembly] = fields[2]
        string6Map[GNSSLock] = parseGpsOther(fields[3])
        string6Map[InputError] = parseInputError(fields[4])
        string6Map[ChannelStatusWord] = fields[5]
        string6Map[PrimaryPSStatus] = fields[6]
        string6Map[SecondaryPSStatus] = fields[7]
        string6Map[ActivePCBStatus] = fields[8]
        string6Map[ChecksumStatus] = fields[9]
        string6Map[ChannelFaultBin] = fields[10]
        string6Map[PrimaryPCBAmpStatus] = fields[11]
        string6Map[BackupPCBAmpStatus] = fields[12]


def parseString7(string: str):
    string7Map[LastSeen] = time.monotonic()
    string = string.split("*")[0]
    fields = string.split(",")

    if len(fields) >= 13:
        string7Map[Visible] = True
        string7Map[Time] = parseTime(fields[2])
        string7Map[Date] = parseDate(fields[3])
        string7Map[GNSSLock] = parseGps(fields[4])
        string7Map[SatsInView] = parseSats(fields[5])
        string7Map[ErrorByte] = fields[6]
        string7Map[FreqDiff] = fields[7]
        string7Map[PPSDiff] = fields[8]
        string7Map[FreqCorrectionSlice] = fields[9]
        string7Map[DACValue] = fields[10]
        string7Map[Ps1] = fields[11]
        string7Map[Ps2] = fields[12]


def StringViewer(label: str, data: dict):

    # print(data)
    with ui.card().props("flat").bind_visibility_from(data, "visible"):

        with ui.row().props("dense"):
            for key, val in data.items():
                if key in ["last", "visible"]:
                    continue
                with (
                    ui.column(align_items="start")
                    .classes("gap-0")
                    .props("dense") as col
                ):
                    ui.label(f"{key}:").classes("font-bold").props("dense")
                    ui.label().bind_text_from(data, key).props("dense")

                col.bind_visibility_from(data, key, backward=lambda v: v != "")


def ProcessStrings(string: str):

    if string.startswith("$GPNVS,1,"):
        parseString1(string)
    if string.startswith("$GPNVS,2,"):
        parseString2(string)
    if string.startswith("$GPNVS,3,"):
        parseString3(string)
    if string.startswith("$GPNVS,4,"):
        parseString4(string)
    if string.startswith("$GPNVS,5,"):
        parseString5(string)
    if string.startswith("$GPNVS,6,"):
        parseString6(string)
    if string.startswith("$GPNVS,7,"):
        # print(string)
        parseString7(string)

    if string1Map[LastSeen] + 5.0 <= time.monotonic():
        string1Map[Visible] = False

    if string2Map[LastSeen] + 5.0 <= time.monotonic():
        string2Map[Visible] = False

    if string3Map[LastSeen] + 5.0 <= time.monotonic():
        string3Map[Visible] = False

    if string4Map[LastSeen] + 5.0 <= time.monotonic():
        string4Map[Visible] = False

    if string5Map[LastSeen] + 5.0 <= time.monotonic():
        string5Map[Visible] = False

    if string6Map[LastSeen] + 5.0 <= time.monotonic():
        string6Map[Visible] = False

    if string7Map[LastSeen] + 5.0 <= time.monotonic():
        string7Map[Visible] = False


async def read_socket():
    writer = None
    try:
        log.debug("opening serial.sock")
        reader, writer = await asyncio.open_unix_connection("/var/lib/ns/serial.sock")
        #reader, writer = await asyncio.open_connection(host="10.1.10.201", port="8080")
        while True:
            data = await reader.readline()
            if not data:
                break
            ProcessStrings(data.decode("utf-8", errors="ignore"))

    except FileNotFoundError:
        log.debug("File Not Found Error: Serial socket not found.")
        raise
    except ConnectionRefusedError:
        log.debug("ConnectionRefused Error - read_socket")
        pass
    except Exception as e:
        log.debug(f"general exception: {e}")
        raise

    finally:

        if writer:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
                writer = None

            log.debug("cleaned up writer")
        log.debug("cleaned up serial socket task")


SerialTask = None


@ui.page("/")
async def root_status_page():
    global SerialTask

    await controlPanel()

    # init page load, if reading task, cancel and start one.
    if SerialTask and not SerialTask.done():
        SerialTask.cancel()

    SerialTask = asyncio.create_task(read_socket())

    ui.label("Status Strings").classes("text-h5")
    # ui.label("string 7:")
    # ui.label().bind_text_from(string7, "value")
    with ui.tabs().classes("w-full").props("align=left") as tabs:
        ch1 = ui.tab("Channels 1-8").bind_visibility_from(string2Map, "visible")
        ch2 = ui.tab("Channels 9-16").bind_visibility_from(string4Map, "visible")
        fb = ui.tab("Fault Bytes").bind_visibility_from(string1Map, "visible")
        ps = ui.tab("Power Supplies").bind_visibility_from(string3Map, "visible")
        sen = ui.tab("Sensors").bind_visibility_from(string5Map, "visible")
        stat = ui.tab("Status Bytes, Standard").bind_visibility_from(
            string6Map, "visible"
        )
        statBytes = ui.tab("Status Bytes").bind_visibility_from(string7Map, "visible")
    with ui.tab_panels(tabs, value=statBytes).classes("w-full"):

        with ui.tab_panel(ch1):
            StringViewer("Channels 1-8", string2Map)
        with ui.tab_panel(ch2):
            StringViewer("Channels 9-16", string4Map)
        with ui.tab_panel(fb):
            StringViewer("Fault Bytes", string1Map)
        with ui.tab_panel(ps):
            StringViewer("Power Supplies", string3Map)
        with ui.tab_panel(sen):
            StringViewer("Sensors", string5Map)
        with ui.tab_panel(stat):
            StringViewer("Status Bytes, Standard", string6Map)
        with ui.tab_panel(statBytes):
            StringViewer("Status Bytes", string7Map)

    def serial_connect_cb():
        global SerialTask
        if SerialTask is None or SerialTask.done():
            #log.info("created new reader")
            SerialTask = asyncio.create_task(read_socket())

    ui.timer(2.0, serial_connect_cb)
