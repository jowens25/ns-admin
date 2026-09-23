#!/usr/bin/env python3
import asyncio

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui

from ns2.ui.control_panel import LoadTimeZones
from ns2.utils import ASSETS_DIR, log

from ns2.ui.login import login_page
from ns2.ui.status_page import root_status_page
from ns2.ui.system_page import system_page
from ns2.ui.networking_page import network_page
from ns2.ui.snmp_page import snmp_page
from ns2.ui.accounts_page import accounts_page
from ns2.ui.terminal import terminal_page


from multiprocessing import freeze_support
from ns2.lib.systemd1 import isActive
from ns2.ui.system_page import LoadSystemUnits
from ns2.ui.firewalld_page import LoadFirewalldServiceInfo


unrestricted_page_routes = {
    "/login",
    "/favicon.ico",
}


#'''
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """This middleware restricts access to all NiceGUI pages.
    It redirects the user to the login page if they are not authenticated."""

    path = request.url.path

    bid = app.storage.browser.get("id")
    activeId = app.storage.general.get("activeId", None)
    if activeId is not None and bid == activeId:
        return await call_next(request)

    # Allow unrestricted routes
    if path in unrestricted_page_routes:
        # log.info("unrestricted")
        return await call_next(request)

    # Allow static assets
    if path.startswith("/_nicegui/") or path.startswith("/static/"):

        return await call_next(request)

    return RedirectResponse("/login")


production = True

async def LoadStatic():
    active = await isActive("firewalld.service")
    if active["state"]:
        await LoadFirewalldServiceInfo()
    await LoadSystemUnits()
    await LoadTimeZones()
    app.storage.general.update({"activeUser": None, "activeId": None, "ts":0})


# app.on_startup(LoadStatic)


def main():
    freeze_support()
    log.info("app starting")

    asyncio.run(LoadStatic())

    ui.run(
        port=8000,
        reload=False,
        storage_secret="your-secret-key",
        title="Novus Configuration Tool",
        favicon=str(ASSETS_DIR / "favicon.png"),
    )


if __name__ == "__main__" and production:
    main()
else:
     ui.run(
         port=8000,
         reload=True,
         storage_secret="your-secret-key",
         title="Novus Configuration Tool",
         favicon=str(ASSETS_DIR / "favicon.png"),
     )
