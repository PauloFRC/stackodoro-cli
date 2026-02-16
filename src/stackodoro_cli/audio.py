import miniaudio
import random
from pathlib import Path
from importlib import resources
import time

class AudioMixer:
    SOUND_FILES = {
        'session_complete': 'session_complete.mp3',
    }

    def __init__(self):
        self.device = miniaudio.PlaybackDevice()
        self.sound_effects = {}
        
        res_dir = resources.files('stackodoro_cli').joinpath('res')
        for key, filename in self.SOUND_FILES.items():
            try:
                file_path = res_dir.joinpath(filename)
                self.sound_effects[key] = str(file_path)
            except Exception as e:
                raise FileNotFoundError(f"Error: Could not load {filename}: {e}")

        self.playlist = []
        self.current_track_index = 0
        self.stream = None

    def play_session_complete(self):
        stream = miniaudio.stream_file(self.sound_effects['session_complete'])
        self.device.start(stream)

    def load_playlist(self, directory_path):
        path = Path(directory_path)
        if not path.is_dir(): return

        valid_exts = {'.mp3', '.wav', '.flac'}
        self.playlist = [str(f) for f in path.iterdir() if f.suffix.lower() in valid_exts]
        
        if self.playlist:
            random.shuffle(self.playlist)
            self.current_track_index = 0

    def play_playlist(self):
        if not self.playlist: return
        
        track = self.playlist[self.current_track_index]
        self.stream = miniaudio.stream_file(track)
        next(self.stream)
        self.device.start(self.stream)

    def stop(self):
        if self.device:
            self.device.stop()

    def next_track(self):
        self.stop()
        if self.playlist:
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
            self.play_playlist()

    def quit(self):
        if self.device:
            self.device.stop()
            self.device.close()
