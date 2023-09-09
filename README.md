# Minecraft Runner

Python wrapper around a Minecraft server that performs periodic rolling backups, automatic restarts on crash, and contains some Easter eggs.

## Install + Configuration

1. Clone this repository to the machine or VM with your server
2. Run `python3 src/server_config.py` to create the default config file
3. Edit `config/config.json` for your server. Notable fields to update:
   - `server_path`: This is the path where your server jar is
   - `start_command`: Command to run inside of your server path to start the server
   - `backup_path`: Directory create backups in
4. Configure your system to run the server. See below. `systemd` is the recommended approach

## Running

### Manually

- Start the server with: `python3 src/main.py`
  - The server may also be conditionally started with `python3 src/check_alive.py` which will only run the server if it is not already running. A `crontab` entry could be used to ensure the server is running, although `systemd` is a better approach
- Stop the server with `Ctrl+C` or `python3 src/stop.py` if started in the background

### systemd

1. Update `config/galacticraft.service`:
   - `ExecStart`: `python3 {path-to-main.py}`
   - `User`: User to run the server as
   - `Group`: The group to run the server in
2. Install `config/galacticraft.service` to `etc/systemd/system`
3. Reload the systemd daemon: `sudo systemctl daemon-reload`
4. `systemctl` can now be used to manage the server:
   - Set to start on system start: `sudo systemctl enable galacticraft`
   - Start the server: `sudo systemctl start galacticraft`
   - Stop the server: `sudo systemctl stop galacticraft`
   - Restart the server: `sudo systemctl restart galacticraft`
   - Query server status: `sudo systemctl status galacticraft`
