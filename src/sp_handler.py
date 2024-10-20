from datetime import datetime
from config import DOWNLOAD_DIR, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from src.json_utils import load_tasks, save_tasks
from savify import Savify
from savify.types import Type, Format, Quality
from savify.utils import PathHolder
import os
import json
import traceback

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

        s = Savify(api_credentials=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
                    quality=Quality.BEST,
                    download_format=Format.MP3,
                    path_holder=PathHolder(download_path))

        file_path = s.download(url)

        tasks = load_tasks()
        tasks[task_id].update(status='completed')
        tasks[task_id]['completed_time'] = datetime.now().isoformat()
        tasks[task_id]['file'] = f'/files/{task_id}/{os.path.basename(file_path)}'
        save_tasks(tasks)
    except Exception as e:
        error_message = f"Error in get_track: {str(e)}\n{traceback.format_exc()}"
        handle_task_error(task_id, error_message)

def get_info(task_id, url):
    try:
        tasks = load_tasks()
        tasks[task_id].update(status='processing')
        save_tasks(tasks)

        s = Savify(api_credentials=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET))
        track = s.get_track_info(url)

        if track is None:
            raise ValueError("Failed to retrieve track information")

        info = {
            "track_name": track.name,
            "artist": track.artists[0].name,
            "duration": track.duration_ms / 1000,  # Convert to seconds
            "url": url
        }

        info_file = os.path.join(DOWNLOAD_DIR, task_id, 'info.json')
        os.makedirs(os.path.dirname(info_file), exist_ok=True)
        with open(info_file, 'w') as f:
            json.dump(info, f)

        tasks = load_tasks()
        tasks[task_id].update(status='completed')
        tasks[task_id]['completed_time'] = datetime.now().isoformat()
        tasks[task_id]['file'] = f'/files/{task_id}/info.json'
        save_tasks(tasks)
    except Exception as e:
        error_message = f"Error in get_info: {str(e)}\n{traceback.format_exc()}"
        handle_task_error(task_id, error_message)

def handle_task_error(task_id, error):
    tasks = load_tasks()
    tasks[task_id].update(status='error', error=error, completed_time=datetime.now().isoformat())
    save_tasks(tasks)
    print(f"Error in task {task_id}: {error}")