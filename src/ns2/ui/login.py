from nicegui import ui, app
from ns2.ui.theme import init_colors
from ns2.utils import ASSETS_DIR
from ns2.lib.bridge import BusCall, CallPamAuthenticate
from ns2.lib.bridge import SetupBridge, CleanupBridge
from ns2.utils import log
import time

async def logout_cb():
    app.storage.general.update({"activeUser": None, "activeId": None, "ts":0})
    await CleanupBridge()
    ui.navigate.reload()
    ui.navigate.to("/login")


async def try_login(_username: str, _password: str) -> None:

    rsp = await CallPamAuthenticate(_username, _password)

    if rsp.error_name is not None:
        ui.notify(rsp.body[0])
        auth = False
    else:
        auth = rsp

    if auth:
        activeUser = await SetupBridge(_username)
        if activeUser != _username:
            ui.notify("active != _user")
            return
        print(activeUser)

        bid = app.storage.browser.get("id", None)
        if bid is None:
            log.info("browser error")
            return
        log.info("try login general store updated")
        app.storage.general.update({"activeUser": activeUser, "activeId": bid, "ts": time.monotonic()})

        print(activeUser)
        print(bid)
        ui.navigate.to("/")

    else:
        ui.notify("Invalid username or password", color="negative")


def are_you_sure_you_want_to(action_message: str) -> bool:
    with ui.dialog() as dialog, ui.card().props("flat"):
        ui.label(f"Are you sure you want to {action_message}")

        with ui.row():
            ui.button("Yes", on_click=lambda: dialog.submit(True)).props("flat")
            ui.button("No", on_click=lambda: dialog.submit(False)).props("flat")
    return dialog


# @ui.page("/{_:path}")
@ui.page("/login")
async def login_page():
    # log.info("LOGIN PAGE LOADED")

    async def reset_cb():

        result = await are_you_sure_you_want_to("reset the default account?")
        if result:
            rsp = await BusCall(
                destination="com.novus.ns",
                path="/com/novus/ns",
                interface="com.novus.ns.accounts",
                member="SetupDefaultUser",
                signature="",
                body=[],
            )

            if rsp.error_name is not None:
                ui.notify(rsp.body[0], type="warning")
            elif len(rsp.body) > 0:
                ui.notify(rsp.body[0], type="positive")
            support_dialog.close()
        else:
            support_dialog.close()

    init_colors()
    with ui.dialog() as support_dialog, ui.card().props("flat"):
        ui.label("Novus Power Products").classes("text-h5")
        ui.label("novuspower.com")
        ui.label("(816) 836-7446")
        ui.label("support@novuspower.com")
        with ui.row():
            ui.button("Close", on_click=support_dialog.close).classes("bg-secondary")
            ui.button("Reset Default Account", on_click=reset_cb).classes(
                "bg-secondary"
            )

    with ui.column(align_items="center").classes("absolute-center gap-16"):
        ui.image(str(ASSETS_DIR / "NOVUS_LOGO.svg")).classes("w-128 max-w-128")

        with ui.card().props("flat"):
            username = ui.input("Username")
            password = ui.input("Password", password=True, password_toggle_button=True)

            async def on_login():
                await try_login(username.value, password.value)

            username.on("keydown.enter", on_login)
            password.on("keydown.enter", on_login)

            with ui.row():
                ui.button("Log in", on_click=on_login).classes("bg-secondary")
                ui.button(
                    "Support",
                    on_click=support_dialog.open,
                ).classes("bg-secondary")
