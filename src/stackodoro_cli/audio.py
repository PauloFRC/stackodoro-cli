import sounddevice as sd
import soundfile as sf
import numpy as np
import random
from pathlib import Path
from importlib import resources
import threading
from dataclasses import dataclass

@dataclass(frozen=True)
class Stopped:
    pass

@dataclass(frozen=True)
class Paused:
    track: str

@dataclass(frozen=True)
class Playing:
    track: str

@dataclass(frozen=True)
class Quitting:
    pass

AudioState = Stopped | Paused | Playing | Quitting

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

        self.dir: str | None = None
        self.playlist = []
        self.current_track_index = 0

        self.state: AudioState = Stopped()
        self.current_stream = None

        self._play_lock = threading.Lock()
        self._current_thread: threading.Thread | None = None

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
        with self._play_lock:
            music_done = False
            try:
                data, samplerate = sf.read(track, dtype='float32', always_2d=True)
                position = [0]
                def callback(outdata, frames, time, status):
                    start = position[0]
                    end = start + frames
                    chunk = data[start:end]

                    if len(chunk) < frames:
                        outdata[:len(chunk)] = chunk * self.volume
                        outdata[len(chunk):] = 0
                        raise sd.CallbackStop()
                    else:
                        outdata[:] = chunk * self.volume

                    position[0] = end

                with sd.OutputStream(
                    samplerate=samplerate,
                    channels=data.shape[1],
                    dtype='float32',
                    callback=callback,
                    latency='high'
                ) as stream:
                    
                    self.current_stream = stream
                    while stream.active and isinstance(self.state, Playing):
                        sd.sleep(100)
                    if not isinstance(self.state, Playing):
                        stream.abort()
                        return
                    
                    music_done = True

            except Exception as e:
                if not isinstance(self.state, Quitting):
                    raise RuntimeError(f"Error playing {track}: {e}")
            finally:
                self.current_stream = None
        
            if music_done:
                self._next_track(from_play_thread=True)

    def _abort_current_stream(self):
        if self.current_stream is not None:
            self.current_stream.abort()
            self.current_stream = None

    def play_playlist(self, from_play_thread=False):
        if not self.playlist:
            raise RuntimeError("Playlist not loaded")

        self._abort_current_stream()
        sd.stop()

        # if this was called from the play thread, we don't want to join it (would cause deadlock)
        if not from_play_thread and self._current_thread and self._current_thread.is_alive():
            self._current_thread.join(timeout=1.0)

        track = self.playlist[self.current_track_index]
        self.state = Playing(track)

        self._current_thread = threading.Thread(target=self._play_thread, args=(track,), daemon=True)
        self._current_thread.start()

    def pause(self):
        if isinstance(self.state, Playing):
            track = self.state.track
            self.state = Paused(track)
            
            self._abort_current_stream()
            sd.stop()

    def stop(self):
        self.state = Stopped()
        self._abort_current_stream()
        sd.stop()

    def _next_track(self, from_play_thread=False):
        if not self.playlist:
            return

        # check if reached the end of the list
        if self.current_track_index >= len(self.playlist) - 1:
            random.shuffle(self.playlist)
            self.current_track_index = 0
        else:
            self.current_track_index += 1

        self.play_playlist(from_play_thread=from_play_thread)
    
    def skip_track(self):
        if self.playlist:
            self._next_track(from_play_thread=False)

    def previous_track(self):
        if self.playlist:
            self.current_track_index = (self.current_track_index - 1) % len(self.playlist)
            self.play_playlist()

    def quit(self):
        self.state = Quitting()
        self._abort_current_stream()
        sd.stop()
