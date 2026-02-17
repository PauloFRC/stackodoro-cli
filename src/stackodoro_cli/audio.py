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

        self.dir = None
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
        self.dir = directory_path
        path = Path(directory_path)
        if not path.is_dir(): 
            return

        valid_exts = {'.mp3', '.wav', '.flac', '.ogg'}
        self.playlist = [str(f) for f in path.iterdir() if f.suffix.lower() in valid_exts]
        if self.playlist:
            random.shuffle(self.playlist)
            self.current_track_index = 0

    def _play_thread(self, track):
        try:
            data, samplerate = sf.read(track, dtype='float32', always_2d=True)
            scaled = data * self.volume
            sd.play(scaled, samplerate, device=sd.default.device['output'])
            while sd.get_stream().active:
                if not self.playing:
                    sd.stop()
                    return
                sd.sleep(100)
        except Exception as e:
            print(f"Error playing {track}: {e}")
        finally:
            self.playing = False

    # TODO: volume handling while playing
    def play_playlist(self):
        if not self.playlist:
            return

        self.stop()
        self.playing = True
        track = self.playlist[self.current_track_index]

        thread = threading.Thread(target=self._play_thread, args=(track,), daemon=True)
        thread.start()

    def stop(self):
        self.playing = False
        self.paused = False
        sd.stop()
        self.current_stream = None

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
