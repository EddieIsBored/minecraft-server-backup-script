import logging
from logging.handlers import RotatingFileHandler
import mctools  # Import the RCONClient
import time
import os
import tarfile
from datetime import datetime
import subprocess
backup_logger = logging.getLogger("backup_logger")

SERVER_FILE_PATH = os.path.dirname(os.path.realpath(__file__))
HOST = '127.0.0.1'  # Hostname of the Minecraft server
PORT = 25575  # Port number of the RCON server

def init_logging(path):
    # Create handler
    backup_logger.setLevel(logging.INFO)
    rot_handler = RotatingFileHandler(path, maxBytes=2*1024*1024, backupCount=5)
    formatter =  logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add handler to the logger
    rot_handler.setFormatter(formatter)
    backup_logger.addHandler(rot_handler)

def make_tarfile(filepath):
    
    output_filename = f"{filepath}/Backups/Backup_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.tar.gz"
    source_filename = f"{filepath}/world"

    with tarfile.open(output_filename, "w:gz") as tar:
        try:
            tar.add(source_filename, arcname=os.path.basename(source_filename))
            backup_logger.info(f"Successfully zipped {source_filename}")
        except Exception as e:
            backup_logger.error(f"Failed to zip world file with error: {e}")
            exit(1)

def execute_rcon_commands(rcon):
    # Login to RCON:
    if rcon.login("bananarama"):
        # Send command to RCON - broadcast message to all players:
        rcon.command("say Server will shut down in 2 minutes")
        # Wait 2 mins
        time.sleep(10)
        # Stop the server!
        rcon.command('stop')

def delete_old_backups(filepath):
    backup_directory = f"{filepath}/Backups/"

    # Get the current time
    now = datetime.now()

    # Loop through all the files in the directory
    for filename in os.listdir(backup_directory):

        # Get the creation time of the file
        filepath = os.path.join(backup_directory, filename)
        creation_time = datetime.fromtimestamp(os.path.getmtime(filepath))

        # Calculate the difference between the creation time and the current time
        time_difference = now - creation_time

        # If the file is older than 3 days, delete it
        if time_difference.days > 3:
            os.remove(filepath)

def main():

    # Create the RCONClient:
    try:
        rcon = mctools.RCONClient(HOST, port=PORT)
    except Exception as e:
        backup_logger.error(f"Failed to connect to RCON with error: {e}")
        exit(1)

    # Stop the server
    execute_rcon_commands(rcon)

    # Back it up
    make_tarfile(SERVER_FILE_PATH)

    # Probably should have 2 minutes before turning it back on, allowing the world to fully backup.
    time.sleep(30)

    # Start the server back up
    try: 
        command = "screen -S minecraft -p 0 -X stuff 'sh startserver.sh\n'"
        subprocess.run(command, shell=True) 
        backup_logger.info(f"Successfully launched server")
    except Exception as e:
        backup_logger.error(f"Failed to launch server with error: {e}")

    delete_old_backups(SERVER_FILE_PATH)


if __name__ == "__main__":
    init_logging("backup.log")
    #main()