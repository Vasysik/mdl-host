from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import threading
import time
import os
import shutil
from config import DOWNLOAD_DIR, TASK_CLEANUP_TIME, MAX_WORKERS
from src.json_utils import load_tasks, save_tasks
import src.yt_handler as yt_handler
import src.sp_handler as sp_handler

executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

def cleanup_task(task_id):
    tasks = load_tasks()
    download_path = os.path.join(DOWNLOAD_DIR, task_id)
    if os.path.exists(download_path):
        shutil.rmtree(download_path, ignore_errors=True)
    if task_id in tasks:
        del tasks[task_id]
        save_tasks(tasks)

def cleanup_orphaned_folders():
    tasks = load_tasks()
    task_ids = set(tasks.keys())
    
    for folder in os.listdir(DOWNLOAD_DIR):
        folder_path = os.path.join(DOWNLOAD_DIR, folder)
        if os.path.isdir(folder_path) and folder not in task_ids:
            shutil.rmtree(folder_path, ignore_errors=True)
            print(f"Removed orphaned folder: {folder_path}")

def cleanup_processing_tasks():
    tasks = load_tasks()
    for task_id, task in list(tasks.items()):
        if task['status'] == 'processing':
            task['status'] = 'error'
            task['error'] = 'Task was interrupted during processing'
            task['completed_time'] = datetime.now().isoformat()
    save_tasks(tasks)

def process_tasks():
    while True:
        tasks = load_tasks()
        current_time = datetime.now()
        for task_id, task in list(tasks.items()):
            if task['status'] == 'waiting':
                if task['task_type'].startswith('yt_'):
                    yt_handler.handle_task(executor, task_id, task)
                elif task['task_type'].startswith('sp_'):
                    sp_handler.handle_task(executor, task_id, task)
            elif task['status'] in ['completed', 'error']:
                completed_time = datetime.fromisoformat(task['completed_time'])
                if current_time - completed_time > timedelta(minutes=TASK_CLEANUP_TIME):
                    cleanup_task(task_id)
        if current_time.minute % 5 == 0 and current_time.second == 0:
            cleanup_orphaned_folders()
        time.sleep(1)

cleanup_processing_tasks()
cleanup_orphaned_folders()
thread = threading.Thread(target=process_tasks, daemon=True)
thread.start()
