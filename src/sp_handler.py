from datetime import datetime
from config import DOWNLOAD_DIR, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from src.json_utils import load_tasks, save_tasks
from spotdl import Spotdl
import os

def handle_task(executor, task_id, task):
    if task['task_type'] == 'sp_get_track':
        executor.submit(get_track, task_id, task['url'])
    elif task['task_type'] == 'sp_get_info':
        executor.submit(get_info, task_id, task['url'])

def get_track(task_id, url):
    try:
        tasks = load_tasks()
        tasks[task_id].update(status='processing')
        save_tasks(tasks)

        download_path = os.path.join(DOWNLOAD_DIR, task_id)
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        spotdl = Spotdl(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
        song = spotdl.search([url])[0]
        file_path = spotdl.download(song, output=download_path)

        tasks = load_tasks()
        tasks[task_id].update(status='completed')
        tasks[task_id]['completed_time'] = datetime.now().isoformat()
        tasks[task_id]['file'] = f'/files/{task_id}/{os.path.basename(file_path)}'
        save_tasks(tasks)
    except Exception as e:
        handle_task_error(task_id, e)

def get_info(task_id, url):
    try:
        tasks = load_tasks()
        tasks[task_id].update(status='processing')
        save_tasks(tasks)

        spotdl = Spotdl(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
        info = spotdl.search([url])[0]

        tasks = load_tasks()
        tasks[task_id].update(status='completed')
        tasks[task_id]['completed_time'] = datetime.now().isoformat()
        tasks[task_id]['info'] = info
        save_tasks(tasks)
    except Exception as e:
        handle_task_error(task_id, e)

def handle_task_error(task_id, error):
    tasks = load_tasks()
    tasks[task_id].update(status='error', error=str(error), completed_time=datetime.now().isoformat())
    save_tasks(tasks)
    print(f"Error in task {task_id}: {str(error)}")
