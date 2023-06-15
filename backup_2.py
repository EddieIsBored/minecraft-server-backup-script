import logging
from logging.handlers import RotatingFileHandler 
import mctools
import time
import os
import tarfile
from datetime import datetime
import subprocess

backup_logger = logging.getLogger("backup_logger")
CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) 
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

def compress_and_backup_world(filepath):

    backups_folder = os.path.join(filepath, 'Backups')

    if not os.path.exists(backups_folder):
        os.makedirs(backups_folder)

    current_time_and_date = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

    output_filename =  os.path.join(backups_folder, current_time_and_date + '.tar.gz')
    source_filename = os.path.join(filepath, 'world')

    with tarfile.open(output_filename, "w:gz", compresslevel=6) as tar:
        try:
            tar.add(source_filename)
            backup_logger.info(f"Successfully compressed {source_filename}")
        except Exception as e:
            backup_logger.error(f"Failed to zip world file with error: {e}")
            exit(1)

def execute_rcon_commands(rcon):
    # Login to RCON:
    if rcon.login("bananarama"):
        # Send command to RCON - broadcast message to all players:
        rcon.command("say Server will shut down in 2 minutes")
        # Wait 2 mins
        time.sleep(120)
        # Stop the server!
        rcon.command('stop')

def delete_old_backups(filepath):
    backups_folder = os.path.join(filepath, 'Backups')

    # Get the current time
    now = datetime.now()

    # Loop through all the files in the directory
    for filename in os.listdir(backups_folder):

        # Get the creation time of the file
        filepath = os.path.join(backups_folder, filename)
        creation_time = datetime.fromtimestamp(os.path.getmtime(filepath))

        # Calculate the difference between the creation time and the current time
        time_difference = now - creation_time

        # If the file is older than 3 days, delete it
        if time_difference.days > 3:
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

def main():
    server_file_path = CURRENT_DIRECTORY

    # Attempt to connect to the server
    rcon = connect_to_server(HOST, PORT)
    
    # Stop the server
    execute_rcon_commands(rcon)

    # Back the world up
    compress_and_backup_world(server_file_path)

    # Start the server back up
    start_server()

    # Delete old backups
    delete_old_backups(server_file_path)


if __name__ == "__main__":
    init_logging("backup.log")
    # main()