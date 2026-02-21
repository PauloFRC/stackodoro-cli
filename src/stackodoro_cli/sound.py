import os
import random
from pathlib import Path
import pygame

class SoundManager:
    def __init__(self, music_folder: str | None = None):
        if pygame is None:
            raise ImportError("pygame is required for sound playback")

        pygame.mixer.init()
        self.music_folder = music_folder
        self.current_playlist = []
        self.current_track_index = 0
        self._setup_music_playlist()

    def _setup_music_playlist(self) -> None:
        if not self.music_folder or not os.path.isdir(self.music_folder):
            return

        audio_extensions = {'.mp3', '.ogg', '.wav', '.flac'}
        music_files = [
            os.path.join(self.music_folder, f)
            for f in os.listdir(self.music_folder)
            if os.path.splitext(f)[1].lower() in audio_extensions
        ]

        self.current_playlist = music_files
        random.shuffle(self.current_playlist)
        self.current_track_index = 0

    def play_sound(self, sound_file: str) -> None:
        if not os.path.isfile(sound_file):
            raise FileNotFoundError(f"Sound file not found: {sound_file}")

        sound = pygame.mixer.Sound(sound_file)
        sound.play()

    def play_music(self, music_file: str, loops: int = 0) -> None:
        if not os.path.isfile(music_file):
            raise FileNotFoundError(f"Music file not found: {music_file}")

        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(loops=loops)

    def play_playlist(self, loops: int = -1) -> None:
        if not self.current_playlist:
            raise ValueError(
                "No music files found. Ensure music_folder is set "
                "and contains audio files."
            )

        if self.current_playlist:
            self.play_music(self.current_playlist[0], loops=0)
            self.current_track_index = 1

    def next_track(self) -> None:
        if not self.current_playlist:
            return

        if self.current_track_index >= len(self.current_playlist):
            random.shuffle(self.current_playlist)
            self.current_track_index = 0

        next_file = self.current_playlist[self.current_track_index]
        self.play_music(next_file, loops=0)
        self.current_track_index += 1

    def stop_sound(self) -> None:
        pygame.mixer.stop()

    def stop_music(self) -> None:
        pygame.mixer.music.stop()

    def stop_all(self) -> None:
        self.stop_sound()
        self.stop_music()

    def pause_music(self) -> None:
        pygame.mixer.music.pause()

    def unpause_music(self) -> None:
        pygame.mixer.music.unpause()

    def set_music_volume(self, volume: float) -> None:
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def set_sound_volume(self, volume: float) -> None:
        pygame.mixer.set_reserved(1)
        for channel in pygame.mixer.get_busy():
            channel.set_volume(max(0.0, min(1.0, volume)))

    def cleanup(self) -> None:
        self.stop_all()
        pygame.mixer.quit()
