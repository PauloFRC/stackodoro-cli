import sounddevice as sd
import soundfile as sf
import numpy as np
import random
from pathlib import Path
from importlib import resources
import threading

class AudioMixer:
    SOUND_FILES = {
        'session_complete': 'session_complete.mp3',
        'shelf_complete': 'shelf_complete.mp3'
    }

    def __init__(self, initial_volume):
        self.sound_effects = {}
        self.volume = initial_volume
        
        res_dir = resources.files('stackodoro_cli').joinpath('res')
        for key, filename in self.SOUND_FILES.items():
            try:
                file_path = res_dir.joinpath(filename)
                data, samplerate = sf.read(str(file_path))
                self.sound_effects[key] = (data, samplerate)
            except Exception as e:
                raise FileNotFoundError(f"Error: Could not load {filename}: {e}")

        self.playlist = []
        self.current_track_index = 0
        self.playing = False
        self.paused = False
        self.current_stream = None

    def play_session_complete(self):
        data, samplerate = self.sound_effects['session_complete']
        self._play_audio(data * self.volume, samplerate)
    
    def play_shelf_complete(self):
        data, samplerate = self.sound_effects['shelf_complete']
        self._play_audio(data * self.volume, samplerate)

    def _play_audio(self, data, samplerate):
        sd.play(data, samplerate)

    def set_volume(self, volume_level: float):
        self.volume = max(0.0, min(1.0, volume_level))

    def load_playlist(self, directory_path):
        path = Path(directory_path)
        if not path.is_dir(): 
            return

        valid_exts = {'.mp3', '.wav', '.flac', '.ogg'}
        self.playlist = [str(f) for f in path.iterdir() if f.suffix.lower() in valid_exts]
        if self.playlist:
            random.shuffle(self.playlist)
            self.current_track_index = 0

    # TODO: volume handling while playing
    def play_playlist(self):
        if not self.playlist: 
            return
        
        self.stop()
        track = self.playlist[self.current_track_index]
        
        def play_thread():
            try:
                data, samplerate = sf.read(track)
                self.playing = True
                self._play_audio(data * self.volume, samplerate)
                sd.wait()
                self.playing = False
            except Exception as e:
                raise RuntimeError(f"Error playing {track}: {e}")
                self.playing = False
        
        thread = threading.Thread(target=play_thread, daemon=True)
        thread.start()

    def stop(self):
        sd.stop()
        self.playing = False
        self.paused = False

    def next_track(self):
        if self.playlist:
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
            self.play_playlist()

    def previous_track(self):
        if self.playlist:
            self.current_track_index = (self.current_track_index - 1) % len(self.playlist)
            self.play_playlist()

    def is_playing(self):
        return self.playing

    def quit(self):
        self.stop()
