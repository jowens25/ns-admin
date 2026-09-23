import asyncio

from nicegui import app, ui
from dbus_next import Message
from ns2.ui.control_panel import controlPanel
from ns2.utils import log, make_col_of, make_action_col

from ns2.lib.accounts import GetUsers
from ns2.lib.bridge import GetBridge, BridgeCall, IsUserAdmin
from ns2.ui.accountsDialogs import (
    addUserDialog,
    editDeleteUserDialog,
    editPolicyDialog,
)


async def handleNotifications():
    await asyncio.sleep(0.25)
    accounts_table.refresh()


def notification_handler(msg: Message):
    if msg.interface == "com.novus.ns.accounts" and msg.member == "Changed":
        log.info(msg.body)
        asyncio.ensure_future(handleNotifications())
        return True


async def SetupNotifications():
    await BridgeCall(
        destination="org.freedesktop.DBus",
        path="/org/freedesktop/DBus",
        interface="org.freedesktop.DBus",
        member="AddMatch",
        signature="s",
        body=["type='signal',member='Changed',interface='com.novus.ns.accounts'"],
    )

    bridge = GetBridge()

    bridge.add_message_handler(notification_handler)


@ui.refreshable
async def accounts_table():

    addDialog = await addUserDialog()
    policyDialog = await editPolicyDialog()

    rsp = await GetUsers()
    print(rsp.body)

    if rsp.error_name is not None:
        ui.notify(rsp.error_name)
        ui.label(rsp.error_name)
        return
    tab = (
        ui.table(
            title="Accounts",
            columns=[
                make_col_of("Username"),
                make_col_of("Group"),
                make_col_of("Login", label="Remote Login"),
                make_action_col(),
            ],
            rows=rsp.body[0],
            column_defaults={
                "align": "left",
                "headerClasses": "uppercase text-primary",
            },
        )
        .classes("w-full")
        .props("flat dense")
    )

    with tab.add_slot("body-cell-Group"):
        with tab.cell("Group"):
            ui.badge().props("""
                :color="props.value == 'admin' ? 'green' : 'grey'"
                :label="props.value"
            """)

    with tab.add_slot("top-right"):
        with ui.row():
            ui.input("Search").bind_value(tab, "filter").props("dense")

            ui.button(icon="add", on_click=addDialog.open).props("flat dense")

    with tab.add_slot("bottom"):
        with ui.row().classes("w-full justify-end"):
            ui.button("Password Policy", on_click=policyDialog.open).props("dense flat")

    async def on_delete_cb(e):
        username: str = e.args
        dialog = await editDeleteUserDialog(username)
        activeUser = app.storage.general.get("activeUser", "error")

        rsp = await IsUserAdmin(activeUser)
        if rsp.error_name is not None:
            ui.notify(rsp.body[0])
            return
        callerIsAdmin = rsp.body[0]

        rsp = await IsUserAdmin(username)
        if rsp.error_name is not None:
            ui.notify(rsp.body[0])
            return
        targetIsAdmin = rsp.body[0]

        if username == activeUser:
            dialog.open()
        if callerIsAdmin:
            dialog.open()
        else:
            ui.notify(f"not allowed to edit {username}'s password")
            return

    tab.on("delete-account", on_delete_cb)

    with tab.add_slot("body-cell-action"):
        with tab.cell().props("align=right"):
            ui.button(icon="more_vert").props("flat").on(
                "click",
                js_handler="() => emit(props.row.Username)",
                handler=on_delete_cb,
            ).props("dense align=right")


@ui.page("/accounts")
async def accounts_page():
    """user page content"""
    await controlPanel()
    await SetupNotifications()
    await accounts_table()
