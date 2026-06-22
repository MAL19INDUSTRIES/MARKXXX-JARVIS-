"""
TTS engine — Gemini voices only.
"""

import io
import threading
from typing import Callable

import numpy as np
import sounddevice as sd

RECEIVE_SAMPLE_RATE = 24000

PROVIDER_VOICES: dict[str, list[tuple[str, str]]] = {
    "gemini": [
        ("Puck",          "puck"),
        ("Charon",        "charon"),
        ("Kore",          "kore"),
        ("Fenrir",        "fenrir"),
        ("Aoede",         "aoede"),
        ("Leda",          "leda"),
        ("Orus",          "orus"),
        ("Schedar",       "schedar"),
        ("Zubenelgenubi", "zubenelgenubi"),
    ],
}

EXTERNAL_PROVIDERS = set()
DEFAULT_PROVIDER = "gemini"
DEFAULT_VOICE_ID = "orus"
PROVIDER_TUTORIAL: dict[str, dict] = {}


def _mp3_bytes_to_pcm(mp3_bytes: bytes) -> np.ndarray:
    """Decode MP3 bytes → int16 numpy array at RECEIVE_SAMPLE_RATE."""
    try:
        import soundfile as sf
        buf = io.BytesIO(mp3_bytes)
        data, sr = sf.read(buf, dtype="int16", always_2d=False)
        if sr != RECEIVE_SAMPLE_RATE:
            ratio = RECEIVE_SAMPLE_RATE / sr
            new_len = int(len(data) * ratio)
            indices = np.round(np.linspace(0, len(data) - 1, new_len)).astype(int)
            data = data[indices]
        if data.ndim > 1:
            data = data[:, 0]
        return data
    except Exception as e:
        print(f"[TTS] ⚠️ MP3 decode error: {e}")
        return np.array([], dtype=np.int16)


def _play_pcm(pcm: np.ndarray, on_start: Callable | None = None,
              on_stop: Callable | None = None) -> None:
    """Play int16 PCM array through sounddevice using RawOutputStream (blocking)."""
    if pcm.size == 0:
        if on_stop:
            on_stop()
        return
    try:
        if on_start:
            on_start()
        raw = pcm.tobytes()
        stream = sd.RawOutputStream(
            samplerate=RECEIVE_SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        stream.start()
        chunk_size = 4096
        for i in range(0, len(raw), chunk_size):
            stream.write(raw[i:i + chunk_size])
        stream.stop()
        stream.close()
    except Exception as e:
        print(f"[TTS] Playback error: {e}")
    finally:
        if on_stop:
            on_stop()


class TTSEngine:
    """
    Wraps ElevenLabs / OpenAI TTS.

    Usage:
        engine = TTSEngine(provider="openai", api_key="...", voice_id="onyx")
        engine.speak("Hello, Sir.")
    """

    def __init__(
        self,
        provider: str = "gemini",
        api_key: str = "",
        voice_id: str = "",
        openai_model: str = "tts-1",
        on_speaking_start: Callable | None = None,
        on_speaking_stop: Callable | None = None,
    ):
        self.provider = provider.lower()
        self.api_key = api_key
        self.voice_id = voice_id
        self.openai_model = openai_model
        self.on_speaking_start = on_speaking_start
        self.on_speaking_stop = on_speaking_stop
        self._lock = threading.Lock()

    def speak(self, text: str) -> None:
        """Synthesize text and play audio (non-blocking)."""
        if not text or not text.strip():
            return
        threading.Thread(target=self._speak_sync, args=(text,), daemon=True).start()

    def speak_sync(self, text: str) -> None:
        """Synthesize text and play audio (blocking)."""
        self._speak_sync(text)

    def _speak_sync(self, text: str) -> None:
        with self._lock:
            try:
                print(f"[TTS] Synthesizing with {self.provider} / {self.voice_id}, text={text[:60]}...")
                mp3 = self._synthesize(text)
                if mp3:
                    print(f"[TTS] Got {len(mp3)} bytes of audio")
                    pcm = _mp3_bytes_to_pcm(mp3)
                    print(f"[TTS] Decoded to {len(pcm)} PCM samples")
                    _play_pcm(pcm, self.on_speaking_start, self.on_speaking_stop)
                    print(f"[TTS] Playback complete")
                else:
                    print(f"[TTS] No audio returned from {self.provider}")
            except Exception as e:
                print(f"[TTS] ❌ {self.provider} error: {e}")
                import traceback; traceback.print_exc()
                if self.on_speaking_stop:
                    self.on_speaking_stop()

    def _synthesize(self, text: str) -> bytes | None:
        if self.provider == "elevenlabs":
            return self._elevenlabs(text)
        elif self.provider == "openai":
            return self._openai(text)
        elif self.provider == "edge":
            return self._edge(text)
        return None

    def _elevenlabs(self, text: str) -> bytes | None:
        try:
            from elevenlabs.client import ElevenLabs
            client = ElevenLabs(api_key=self.api_key)
            voice_id = self.voice_id or ELEVENLABS_VOICES[0][1]
            audio_gen = client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            chunks = [chunk for chunk in audio_gen if isinstance(chunk, bytes)]
            return b"".join(chunks) if chunks else None
        except Exception as e:
            print(f"[TTS] ❌ ElevenLabs: {e}")
            return None

    def _edge(self, text: str) -> bytes | None:
        """Microsoft Edge TTS - free, no API key needed."""
        try:
            import asyncio
            import edge_tts

            voice = self.voice_id or "en-US-GuyNeural"

            async def _generate():
                communicate = edge_tts.Communicate(text, voice)
                audio_chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_chunks.append(chunk["data"])
                return b"".join(audio_chunks)

            loop = asyncio.new_event_loop()
            audio = loop.run_until_complete(_generate())
            loop.close()
            return audio if audio else None
        except Exception as e:
            print(f"[TTS] Edge TTS error: {e}")
            return None

    def _openai(self, text: str) -> bytes | None:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            voice = self.voice_id or "onyx"
            response = client.audio.speech.create(
                model=self.openai_model,
                voice=voice,
                input=text,
                response_format="mp3",
            )
            return response.content
        except Exception as e:
            print(f"[TTS] ❌ OpenAI TTS: {e}")
            return None
