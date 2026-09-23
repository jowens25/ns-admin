from importlib.metadata import version
import time

from nicegui import app, ui

from ns2.lib.bridge import GetBridge
from ns2.utils import ASSETS_DIR, log
from ns2.lib.timedate1 import CallListTimezones, CallGetTimezone, CallSetTimezone
from ns2.ui.login import logout_cb
from ns2.ui.theme import init_colors
from datetime import datetime
from zoneinfo import ZoneInfo

session_duration_seconds = 24 * 60 * 60 # 1 day

async def bridge_check():
    # log.info("bridge check")
    b = GetBridge()
    if b is None:
        app.storage.general.update({"activeUser": None, "activeId": None, "ts":0})
        ui.navigate.reload()


async def check_auth():
    # log.info("check auth")
    bid = app.storage.browser.get("id", None)
    ts = app.storage.general.get("ts", None)
    # log.info(bid)
    if bid is None:
        log.info("bid error")
        ui.navigate.to("/login")
        return
    
    if time.monotonic() >= ts + session_duration_seconds and ts != 0:
        log.info("session expired 60 seconds ")
        app.storage.general.update({"activeUser": None, "activeId": None, "ts":0})
        ui.navigate.to("/login")
        return

    activeId = app.storage.general.get("activeId", None)
    if activeId is None:
        log.info("active id is none")
        ui.navigate.to("/login")
        return

    if activeId != bid:
        log.info("active id != bid")
        ui.navigate.to("/login")
        return
    
    



@ui.refreshable
def dateLabel():
    tz = app.storage.general.get("tz", "UTC")
    tzObj = ZoneInfo(tz)
    ui.label(datetime.now().astimezone(tzObj).strftime("%m-%d-%Y %H:%M:%S")).classes(
        "font-bold"
    )


SelectableTimeZones = None


async def LoadTimeZones():
    global SelectableTimeZones
    if not SelectableTimeZones:
        SelectableTimeZones = await CallListTimezones()


async def Clock():
    global SelectableTimeZones

    dateLabel()

    async def SetTimeCb(e):
        log.info(f"timezone change -> {e.value}")
        await CallSetTimezone(e.value)
        app.storage.general.update({"tz": e.value})

    await LoadTimeZones()
    current_tz = await CallGetTimezone()

    ui.select(
        SelectableTimeZones, with_input=True, value=current_tz, on_change=SetTimeCb
    ).props("dense")


async def controlPanel():

    # current_tz = await CallGetTimezone()

    # app.storage.general.update({"tz": current_tz})

    ui.timer(1.0, check_auth)
    ui.timer(2.0, bridge_check)
    ui.timer(1.0, dateLabel.refresh)

    init_colors()
    with ui.header().classes("items-center justify-between").classes("bg-dark"):
        ui.button(on_click=lambda: left_drawer.toggle(), icon="menu").props(
            "flat color=white"
        )
        ui.image(str(ASSETS_DIR / "NOVUS_LOGO.svg")).classes("w-48")
        ui.label(f"Welcome {app.storage.general.get("activeUser","error")}!")
        with ui.row().classes("items-center no-wrap"):
            await Clock()

    with ui.left_drawer(bordered=True).classes("bg-dark") as left_drawer:

        def nav(p):
            ui.navigate.to(p)
            # left_drawer.hide()

        ui.separator()
        btnps = "flat color=white align=left"
        c = "w-full"
        ui.button("Status", on_click=lambda: nav("/")).props(btnps).classes(c)
        ui.button("System", on_click=lambda: nav("/system")).props(btnps).classes(c)
        ui.button("Network", on_click=lambda: nav("/network")).props(btnps).classes(c)
        ui.button("SNMP", on_click=lambda: nav("/snmp")).props(btnps).classes(c)
        ui.button("Accounts", on_click=lambda: nav("/accounts")).props(btnps).classes(c)
        ui.button("Terminal", on_click=lambda: nav("/terminal")).props(btnps).classes(c)

        ui.separator()

        ui.button(
            "Logout",
            on_click=logout_cb,
        ).props(
            "flat color=negative align=left"
        ).classes("full-width")
    # Footer
    with ui.footer().classes("bg-dark"):
        ui.label(version("ns2"))
