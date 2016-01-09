from datetime import datetime

from sp_map_cycle.db import connect
from sp_map_cycle.db import select

from core import echo_console


class SPMCCommand:
    def __init__(self, name, parent=None):
        self.registered_commands = {}
        if parent is not None:
            parent.registered_commands[name] = self

    def callback(self, *args):
        raise NotImplementedError


class SPMCCommandHelp(SPMCCommand):
    def callback(self, args):
        echo_console("""spmc help:
> spmc help
Shows this help message

> spmc reload-mapcycle
Reloads mapcycle.json

> spmc rebuild-mapcycle
Creates new mapcycle.json based on mapcycle.txt (mapcycle_default.txt)

> spmc db show
Prints contents of database.sqlite3

> spmc db save
Saves current maps list from memory to the database

> spmc db load
Reloads data from the database into memory

> spmc unset-new-flag <map filename>
Marks the given map as old (no NEW! postfix)

> spmc unset-new-flag-all
Marks all known maps as old (no NEW! postfix)

> spmc restore-new-flag <map filename>
Restores 'new' flag for the given map based on its detection date.
The flag may not be restored if the map is actually old, but you can make
database forget such map by typing 'spmc forget-map <map filename>'.

> spmc forget-map <map filename>
Removes the given map from the database, doesn't remove the map from the mapcycle.
Map will be added to the database again if it's still in mapcycle.

> spmc scan-maps-folder [<map prefix> ...]
Scans contents of ../maps folder and puts scanned maps in mapcycle.txt.
You can then convert that mapcycle.txt to mapcycle.json by typing 'spmc rebuild-mapcycle'.
If map prefixes are given, only maps that start with that prefix will be added to the list.
Example:
spmc scan-maps-folder de_ cs_ gg_
""")


class SPMCCommandReloadMapCycle(SPMCCommand):
    def callback(self, args):
        from sp_map_cycle.sp_map_cycle import load_maps_from_db
        from sp_map_cycle.sp_map_cycle import reload_mapcycle_json
        from sp_map_cycle.sp_map_cycle import reload_map_list
        try:
            reload_mapcycle_json()
            echo_console("Loaded JSON from mapcycle.json")
        except FileNotFoundError:
            echo_console("Error: Missing mapcycle.json, please rebuild it first")
        else:
            reload_map_list()
            echo_console("Reloaded maps list from JSON")

            if load_maps_from_db():
                echo_console("Data from the database was reloaded")


class SPMCCommandRebuildMapCycle(SPMCCommand):
    def callback(self, args):
        from sp_map_cycle.sp_map_cycle import build_json_from_mapcycle_txt
        try:
            build_json_from_mapcycle_txt()
        except FileNotFoundError:
            echo_console("""Error: No mapcycle.txt nor mapcycle_default.txt found in cfg directory.
You can create one automatically by typing 'spmc scan-maps-folder'.""")


class SPMCCommandDB(SPMCCommand):
    def callback(self, args):
        echo_console("Not enough parameters, type 'spmc help' to get help")


class SPMCCommandDumpDatabase(SPMCCommand):
    def callback(self, args):
        conn = connect()
        if conn is None:
            echo_console("Could not connect to the database")
            return

        echo_console("+--------------------------------+----------+-------+-------+----------+")
        echo_console("| Map File Name (w/o .bsp)       | Detected | Old?* | Likes | Dislikes |")
        echo_console("+--------------------------------+----------+-------+-------+----------+")

        for row in select(conn, 'maps', ('filename', 'detected', 'force_old', 'likes')):
            echo_console("| {}| {}| {}| {}| {}|".format(
                row['filename'].ljust(31)[:31],
                datetime.fromtimestamp(row['detected']).strftime('%x').ljust(9)[:9],
                "YES".ljust(6) if row['force_old'] else "NO".ljust(6),
                str(row['likes']).ljust(6)[:6],
                str(row['dislikes']).ljust(9)[:9],
            ))

        echo_console("+--------------------------------+----------+-------+-------+----------+")
        echo_console("* Only shows if the map was marked old via 'spmc unset-new-flag' command")

        conn.close()


class SPMCCommandSaveToDatabase(SPMCCommand):
    def callback(self, args):
        from sp_map_cycle.sp_map_cycle import save_maps_to_db
        if save_maps_to_db():
            echo_console("Data was saved to the database")


class SPMCCommandLoadFromDatabase(SPMCCommand):
    def callback(self, args):
        from sp_map_cycle.sp_map_cycle import load_maps_from_db
        if load_maps_from_db():
            echo_console("Data from the database was reloaded")


spmc_commands = {}
spmc_commands['spmc'] = SPMCCommand('spmc')
spmc_commands['help'] = SPMCCommandHelp('help', spmc_commands['spmc'])
spmc_commands['db'] = SPMCCommandDB('db', spmc_commands['spmc'])
spmc_commands['db show'] = SPMCCommandDumpDatabase('show', spmc_commands['db'])
spmc_commands['db save'] = SPMCCommandSaveToDatabase('save', spmc_commands['db'])
spmc_commands['db load'] = SPMCCommandLoadFromDatabase('load', spmc_commands['db'])
spmc_commands['reload-mapcycle'] = SPMCCommandReloadMapCycle('reload-mapcycle', spmc_commands['spmc'])
spmc_commands['rebuild-mapcycle'] = SPMCCommandRebuildMapCycle('rebuild-mapcycle', spmc_commands['spmc'])