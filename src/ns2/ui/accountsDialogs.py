import inspect
from typing import Optional

from nicegui import ui, binding

from ns2.lib.bridge import BridgeCall

from dbus_next.signature import Variant
from dbus_next import Message


from ns2.utils import log

from ns2.lib.accounts import ValidatePassword, UserExists


@binding.bindable_dataclass
class User:
    Username: Optional[str] = ""
    Password: Optional[str] = ""
    PasswordRules: Optional[str] = ""
    Group: Optional[str] = "admin"
    Login: Optional[str] = ""


async def editDeleteUserDialog(username):
    log.info("editDeleteUserDialog")
    rsp = await BridgeCall(
        "com.novus.ns",
        "/com/novus/ns",
        "com.novus.ns.accounts",
        "GetUserByUsername",
        "s",
        [username],
    )

    if len(rsp.body) == 0:
        return
    user = User(**rsp.body[0])
    with ui.dialog() as dialog, ui.card().classes("w-full").props("flat"):
        with ui.column().classes("w-full"):
            ui.label("Update password").classes("text-h5")
            ui.label("Note: Updating active account will trigger logout")
            # userfield = (
            #    ui.input("username")
            #    .bind_value(user, "Username")
            #    .classes("w-full")
            #    .props("dense")
            # )
            # userfield.disable()

            def mustMatch(v):
                if not v == p1.value:
                    return "passwords must match"
                else:
                    return None

            p1 = (
                ui.input(
                    "new password",
                    validation=validatePass,
                    password=True,
                    password_toggle_button=True,
                )
                .classes("w-full")
                .props("dense")
            )

            p2 = (
                ui.input(
                    "repeat password",
                    validation=mustMatch,
                    password=True,
                    password_toggle_button=True,
                )
                .bind_value_to(user, "Password")
                .classes("w-full")
                .props("dense")
            )

            # group = (
            #    ui.select(["admin", "user"])
            #    .bind_value(user, "Group")
            #    .classes("w-full")
            #    .props("dense")
            # )
            #
            # group.disable()

            with ui.row().classes("items-center justify-between gap-4 w-full"):

                async def on_save_cb():
                    if not all(await validate_group([p1, p2])):
                        ui.notify("Please correct the errors", type="negative")

                    else:
                        rsp = await EditUser(user)

                        if rsp.error_name is not None:
                            if "bridge" not in rsp.body[0]:
                                ui.notify(rsp.body[0])
                            else:
                                ui.notify("User will be logged out", type="warning")

                        dialog.close()

                async def on_delete_cb():
                    rsp = await BridgeCall(
                        "com.novus.ns",
                        "/com/novus/ns",
                        "com.novus.ns.accounts",
                        "Remove",
                        "s",
                        [username],
                    )
                    if rsp.error_name is not None:
                        ui.notify(rsp.body[0])
                    ui.notify(f"Deleted {username}", type="warning")

                with ui.row():
                    ui.button("save", on_click=on_save_cb).props("flat")
                    ui.button("cancel", on_click=dialog.close).props("flat")
                ui.button(icon="delete", on_click=on_delete_cb).props("flat").tooltip("Delete account")
    return dialog


passwordValidation = {
    "Max is limited to 24 or less characaters": lambda value: 24 >= int(value),
}


async def editPolicyDialog():

    policy = {}
    rsp = await BridgeCall(
        "com.novus.ns",
        "/com/novus/ns",
        "com.novus.ns.accounts",
        "GetPasswordPolicy",
        "",
        [],
    )

    if rsp.error_name is not None:
        ui.notify(rsp.error_name)
    else:
        for k, v in rsp.body[0].items():
            policy[k] = v.value

    with ui.dialog() as dialog:

        with ui.card().classes("w-full max-h-[90vh] overflow-y-auto"):
            ui.label("Edit Password Policy").classes("text-h5")

            def MaxGreaterThanMin(v):
                if v == "":
                    return "min must not be 0"
                if max.value == "":
                    return "max must not be 0"
                if int(v) < 5:
                    return "min must be great than 5"
                if int(max.value) < int(v):
                    return "max must be greater than min"
                else:
                    return None

            max = (
                ui.input("max length", validation=passwordValidation)
                .bind_value(policy, "max")
                .props("dense")
            )
            min = (
                ui.input("min length", validation=MaxGreaterThanMin)
                .bind_value(policy, "min")
                .props("dense")
            )

            ui.checkbox("require upper").bind_value(policy, "upper").props("dense")
            ui.checkbox("require lower").bind_value(policy, "lower").props("dense")
            ui.checkbox("require symbol").bind_value(policy, "symbol").props("dense")
            ui.checkbox("require digit").bind_value(policy, "digit").props("dense")

            async def on_save_cb():
                if all(await validate_group([min, max])):
                    newPolicy = {
                        "max": Variant("u", int(policy["max"])),
                        "min": Variant("u", int(policy["min"])),
                        "upper": Variant("b", policy["upper"]),
                        "lower": Variant("b", policy["lower"]),
                        "symbol": Variant("b", policy["symbol"]),
                        "digit": Variant("b", policy["digit"]),
                    }
                    rsp = await BridgeCall(
                        "com.novus.ns",
                        "/com/novus/ns",
                        "com.novus.ns.accounts",
                        "SetPasswordPolicy",
                        "a{sv}",
                        [newPolicy],
                    )
                    if rsp.error_name is not None:
                        ui.notify(rsp.body[0])

                dialog.close()

            with ui.row():
                ui.button("save", on_click=on_save_cb)
                ui.button("close", on_click=dialog.close)

    return dialog


# usernameValidation = {
#    "Username must be at least 5 characters": lambda value: len(value) >= 5,
#    "Username must be 24 or less characaters": lambda value: 24 >= len(value),
# }


async def validatePass(value):
    rsp = await ValidatePassword(value)
    if rsp.error_name is not None:
        return rsp.body[0]
    else:
        return None


async def validateUser(value):

    if len(value) < 5:
        return "Username must be at least 5 characters"

    if 24 < len(value):
        return "Username must be 24 or less characters"

    rsp = await UserExists(value)
    if rsp.error_name is not None:
        return rsp.body[0]

    return None


async def AddUser(u: User) -> Message:

    if u.Group == "admin":

        return await BridgeCall(
            "com.novus.ns",
            "/com/novus/ns",
            "com.novus.ns.accounts",
            "AddAdmin",
            "ss",
            [u.Username, u.Password],
        )

    else:
        return await BridgeCall(
            "com.novus.ns",
            "/com/novus/ns",
            "com.novus.ns.accounts",
            "AddUser",
            "ss",
            [u.Username, u.Password],
        )


async def EditUser(u: User) -> Message:
    return await BridgeCall(
        "com.novus.ns",
        "/com/novus/ns",
        "com.novus.ns.accounts",
        "UpdatePassword",
        "ss",
        [u.Username, u.Password],
    )


# async def validate_group(group: list):
#    return [x.validate(return_result=False) for x in group]


async def validate_group(group: list):
    results = []
    for x in group:
        if inspect.iscoroutinefunction(x.validation):
            x.validate(return_result=False)  # triggers UI error display
            error = await x.validation(x.value)  # get actual result
            results.append(error is None)
        else:
            results.append(x.validate())
    return results


async def addUserDialog():
    newUser = User()
    with ui.dialog() as dialog:
        with ui.card().classes("w-full max-h-[90vh] overflow-y-auto"):
            ui.label("Add user").classes("text-h5")

            user = (
                ui.input("username", validation=validateUser)
                .bind_value(newUser, "Username")
                .classes("w-full")
                .props("dense")
            )

            def mustMatch(v):
                if not v == p1.value:
                    return "passwords must match"
                else:
                    return None

            p1 = (
                ui.input(
                    "password",
                    validation=validatePass,
                    password=True,
                    password_toggle_button=True,
                )
                .classes("w-full")
                .props("dense")
            )

            p2 = (
                ui.input(
                    "repeat password",
                    validation=mustMatch,
                    password=True,
                    password_toggle_button=True,
                )
                .bind_value_to(newUser, "Password")
                .classes("w-full")
                .props("dense")
            )

            ui.select(["admin", "user"]).bind_value(newUser, "Group").classes(
                "w-full"
            ).props("dense")

            async def on_save_cb():
                if all(await validate_group([p1, p2, user])):

                    rsp = await AddUser(newUser)

                    if rsp.error_name is not None:
                        ui.notify(rsp.body[0])
                    else:
                        ui.notify(rsp.body[0], type="positive")
                        dialog.close()

                else:
                    ui.notify("Please correct the errors", type="negative")

            with ui.row():
                ui.button("Add", on_click=on_save_cb)
                ui.button("Cancel", on_click=dialog.close)

    return dialog
