import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path 
import mctools
import time
import os
import tarfile
from datetime import datetime
import subprocess
import argparse

backup_logger = logging.getLogger("backup_logger")
CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) 
HOST = '127.0.0.1'  # Hostname of the Minecraft server
PORT = 25575  # Port number of the RCON server

def init_logging(args):
    log_path = Path(args.log_path, args.logname)
    # Create handler
    backup_logger.setLevel(logging.INFO)
    rot_handler = RotatingFileHandler(log_path, maxBytes=args.logsize*1024*1024, backupCount=args.logfiles)
    formatter =  logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Add handler to the logger
    rot_handler.setFormatter(formatter)
    backup_logger.addHandler(rot_handler)

def compress_and_backup_world(args):

    backup_filepath = args.backup_location
    world_filepath = args.world_location

    backups_folder = Path(backup_filepath, args.backup_name)

    if not Path.exists(backups_folder):
        os.makedirs(backups_folder)

    current_time_and_date = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

    output_filename =  Path(backups_folder, current_time_and_date + '.tar.gz')
    source_filename = Path(world_filepath, args.world_name)

    with tarfile.open(output_filename, "w:gz", compresslevel=args.compresslevel) as tar:
        try:
            tar.add(source_filename)
            backup_logger.info(f"Successfully compressed {source_filename}")
        except Exception as e:
            backup_logger.error(f"Failed to zip world file with error: {e}")
            exit(1)

def execute_rcon_commands(rcon, password):
    # Login to RCON:
    if rcon.login(password):
        # Send command to RCON - broadcast message to all players:
        rcon.command("say Server will shut down in 2 minutes")
        # Wait 2 mins
        time.sleep(120)
        # Stop the server!
        rcon.command('stop')

def delete_old_backups(args):
    backups_folder = Path(args.backup_location, args.backup_name)

    # Get the current time
    now = datetime.now()

    # Loop through all the files in the directory
    for filename in os.listdir(backups_folder):

        # Get the creation time of the file
        filepath = Path(backups_folder, filename)
        creation_time = datetime.fromtimestamp(os.path.getmtime(filepath))

        time_difference = now - creation_time

        # If the file is older than args.max date days, delete it
        if time_difference.days > args.maxdays:
            os.remove(filepath)

def connect_to_server(host, port):
    # Create the RCONClient:
    try:
        return mctools.RCONClient(host, port=port)
    except Exception as e:
        backup_logger.error(f"Failed to connect to RCON with error: {e}")
        exit(1)

def start_server():
    try: 
        command = "screen -S minecraft -p 0 -X stuff 'sh startserver.sh\n'"
        subprocess.run(command, shell=True) 
        backup_logger.info(f"Successfully launched server")
    except Exception as e:
        backup_logger.error(f"Failed to launch server with error: {e}")

def main(args):
    # Attempt to connect to the server
    rcon = connect_to_server(args.host, args.port)

    # Stop the server
    execute_rcon_commands(rcon, args.password)

    # Back the world up
    compress_and_backup_world(args)

    # Start the server back up
    start_server()

    # Delete old backups
    delete_old_backups(args)

def arg_setup():

    class CustomHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
        def add_argument(self, action):
            if action.metavar is None:
                action.metavar = ''
            super(CustomHelpFormatter, self).add_argument(action)
    
    parser = argparse.ArgumentParser(
        formatter_class=CustomHelpFormatter,
    )
    parser.add_argument("-pw", "--password", type=str, help="The RCON password of the server", default="bananarama")
    parser.add_argument("--host", type=str, help="The host of the server", default=HOST)
    parser.add_argument("--port", type=int, help="The port of the server", default=PORT)
    parser.add_argument("-bl", "--backup-path", type=str, help="Location of where to store backups", default=CURRENT_DIRECTORY)
    parser.add_argument("-bn", "--backup-name", type=str, help="Location of where to store backups", default=CURRENT_DIRECTORY)
    parser.add_argument("-wl", "--world-path", type=str, help="Location of where to store backups", default=CURRENT_DIRECTORY)
    parser.add_argument("-wn", "--world-name", type=str, help="Name of the world", default='world')
    parser.add_argument("-cl", "--compresslevel", type=int, help="Level of compression", default=6)
    parser.add_argument("-md", "--maxdays", type=int, help="Max days a backup should be kept", default=7)
    parser.add_argument("-ll", "--log-path", type=str, help="Location of where to store log files", default=CURRENT_DIRECTORY)
    parser.add_argument("-ln", "--logname", type=str, help="Name of log file", default="backup.log")
    parser.add_argument("-ls", "--logsize", type=int, help ="Max size of logfiles (in MB)", default=200)
    parser.add_argument("-lf", "--logfiles", type=int, help ="Max number of logfiles to rotate", default=5)
    
    args = parser.parse_args()

    if args.compresslevel > 9:
        args.compresslevel = 9
    return args

if __name__ == "__main__":
    args = arg_setup()
    init_logging(args)
    main(args)