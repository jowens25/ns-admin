from dataclasses import dataclass
from typing import Optional
from nicegui import ui

from ns2.lib.bridge import BusCall
from ns2.lib.systemd1 import ListUnits
from ns2.ui.control_panel import controlPanel


@dataclass
class SystemdUnit:
    PrimaryName: Optional[str] = None
    Description: Optional[str] = None
    LoadState: Optional[str] = None
    ActiveState: Optional[str] = None
    SubState: Optional[str] = None
    FollowedUnit: Optional[str] = None
    UnitPath: Optional[str] = None
    JobId: Optional[str] = None
    JobType: Optional[str] = None
    JobPath: Optional[str] = None


interesting_units = [
    "ns-serial-mux.service",
    "ns-admin.service",
    "ns.service",
    "snmpd.service",
    "ns-agent.service",
    "nginx.service",
    "firewalld.service",
    "NetworkManager.service",
]


async def GetLogs(since: str, priority: int, units: list) -> list:
    if units is None or len(units) < 1:
        return ["Must select a service"]
    rsp = await BusCall(
        destination="com.novus.ns",
        path="/com/novus/ns",
        interface="com.novus.ns.bridge",
        member="GetLogs",
        signature="sias",
        body=[since, priority, units],
    )
    if len(rsp.body) > 0:
        return rsp.body[0]


def GetUnits(servs):
    services = []
    for s in servs:
        if s[0].endswith(".service"):
            services.append(s[0])
    return sorted(services, key=str.lower)


SINCE_OPTIONS = {
    "1 hour ago": "1 hour ago",
    "8 hours ago": "8 hours ago",
    "24 hours ago": "24 hours ago",
    "3 days ago": "3 days ago",
    "7 days ago": "7 days ago",
}

PRIORITY_OPTIONS = {
    "Emergency (0)": 0,
    "Alert (1)": 1,
    "Critical (2)": 2,
    "Error (3)": 3,
    "Warning (4)": 4,
    "Notice (5)": 5,
    "Info (6)": 6,
    "Debug (7)": 7,
}

Units = None


async def LoadSystemUnits():
    global Units
    Units = await ListUnits()


async def serviceSelectionTable():
    global Units
    allServices = MakeServicesDict(Units)
    with ui.column().classes("w-full"):
        with ui.scroll_area().classes("w-full"):
            services_table = (
                ui.table(
                    rows=allServices,
                    column_defaults={
                        "align": "left",
                        "headerClasses": "uppercase text-primary",
                    },
                    row_key="Name",
                    selection="multiple",
                    # on_select=lambda e: log.info(f'selected: {e.selection}'),
                )
                .props("dense flat")
                .classes("w-full")
            )

            services_table.props(
                f'visible-columns=["Name", "Load State","Active State","Sub State"]'
            )
            services_table.add_slot(
                "header",
                r"""
                <q-tr :props="props">
                    <q-th auto-width />
                    <q-th auto-width />
                    <q-th v-for="col in props.cols" :key="col.name" :props="props"> {{ col.label }} </q-th>
                </q-tr>
            """,
            )

        services_table.add_slot(
            "body",
            r"""
        <q-tr :props="props">
            <q-td auto-width>
                <q-checkbox 
                    :model-value="props.selected" 
                    @update:model-value="props.selected = !props.selected"
                    color="accent"
                    dense 
                />
            </q-td>
            <q-td auto-width @click.stop="">
                <q-btn size="sm" color="accent" round dense 
                       @click="props.expand = !props.expand" 
                       :icon="props.expand ? 'remove' : 'add'" />
            </q-td>
            <q-td v-for="col in props.cols" :key="col.name" :props="props"
                  style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word; max-width: 200px;">
                <template v-if="col.name === 'Sub State'">
                    <q-badge
                        :color="({'running': 'green', 'dead': 'grey', 'exited': 'blue'}[col.value]) || 'red'"
                        :label="col.value"
                    />
                </template>
                <template v-else>
                    {{ col.value }}
                </template>
            </q-td>
        </q-tr>
        <q-tr v-show="props.expand" :props="props">
            <q-td colspan="100%" style="max-width: 0;">
                <div class="text-left"
                     style="word-wrap: break-word; overflow-wrap: break-word; white-space: normal;">
                    {{ props.row.Description }}
                </div>
            </q-td>
        </q-tr>
        """,
        )

        def clear_cb():
            services_table.selected.clear()
            services_table.update()

        with ui.row().classes("w-full justify-between"):
            ui.input("Search for services").bind_value(services_table, "filter").props(
                "dense"
            )
            ui.button("Clear selected", on_click=clear_cb).props("dense flat")

    return services_table


def MakeServicesDict(servs):
    services = []
    for s in servs:
        if s[0].endswith(".service"):
            services.append(
                {
                    "Name": s[0].strip(),
                    "Description": s[1],
                    "Load State": s[2],
                    "Active State": s[3],
                    "Sub State": s[4],
                }
            )
    return services


@ui.page("/system")
async def system_page():
    
    await controlPanel()
    
    #await fetch_logs_cb()

    #ui.label("Services").classes("text-h5")

    #serviceTable = await serviceSelectionTable()

    #ui.separator()
    ui.label("Logs").classes("text-h5")

    with ui.row().classes("items-end gap-4 w-full flex-wrap"):

        sinceSelector = (
            ui.select(
                options=list(SINCE_OPTIONS.keys()),
                value="24 hours ago",
                label="Since",
            )
            .classes("w-40")
            .props("dense")
        )

        prioritySelector = (
            ui.select(
                options=list(PRIORITY_OPTIONS.keys()),
                value="Debug (7)",
                label="Priority",
            )
            .classes("w-40")
            .props("dense")
        )

        ui.button("Fetch Logs", on_click=lambda: fetch_logs_cb()).props("dense flat")
        ui.button("Download", on_click=lambda: download_logs_cb()).props("dense flat")

    uilog = ui.log().classes("w-full h-96").props("dense")
    
    logs = await GetLogs(SINCE_OPTIONS["24 hours ago"], PRIORITY_OPTIONS["Debug (7)"], [s["Name"] for s in MakeServicesDict(Units)])
    
    
    for log in logs:
        uilog.push(log)
    

    async def GatherLogs():
        since = SINCE_OPTIONS[sinceSelector.value]
        priority = PRIORITY_OPTIONS[prioritySelector.value]
        selected_units = [s["Name"] for s in MakeServicesDict(Units)]

        return await GetLogs(since, priority, selected_units)

    async def download_logs_cb():
        logs = await GatherLogs()
        content = "\n".join(logs)
        ui.download.content(content, filename="logs.txt")

    async def fetch_logs_cb():
        uilog.clear()

        logs = await GatherLogs()

        if len(logs) < 1:
            logs.append("No logs found")

        for log in logs:
            uilog.push(log)
