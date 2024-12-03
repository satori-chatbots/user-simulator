import speech_recognition as sr
from pydantic import BaseModel, ValidationError
from typing import List, Union, Dict, Optional
import time
from .utils.utilities import read_yaml
from openai import OpenAI
import warnings
import pygame
import logging
logger = logging.getLogger('Info Logger')


pygame.mixer.init()
warnings.filterwarnings("ignore", category=FutureWarning, module="whisper")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub")
client = OpenAI()
audio_format = "mp3"

class SttModel(BaseModel):
    energy_threshold: float = 50
    pause_threshold: float = 1

class TtsModel(BaseModel):
    model: str = "tts-1"
    voice: str = "alloy"
    speed: float = 1.0

class SpeechModel(BaseModel):
    stt: Optional[SttModel] = SttModel
    tts: Optional[TtsModel] = TtsModel

class STTModule:

    def __init__(self, config):

        if config:
            config_file = read_yaml(config)
            try:
                validated_data = SpeechModel(**config_file)
            except ValidationError as e:
                print(e.json())
                raise

        #STT
            self.energy_th = validated_data.stt.energy_threshold
            self.pause_th = validated_data.stt.pause_threshold

        #TTS
            self.model = validated_data.tts.model
            self.voice = validated_data.tts.voice
            self.speed = validated_data.tts.speed

        else:
        # STT
            self.energy_th = 50
            self.pause_th = 1

        # TTS
            self.model = "tts-1"
            self.voice = "alloy"
            self.speed = 1.0

    def hear(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("Listening...")
            r.energy_threshold = self.energy_th  # lower values for quieter rooms
            r.pause_threshold = self.pause_th
            audio = r.listen(source)

        try:
            logger.info("Recognizing...")
            start = time.time()
            text = r.recognize_whisper(audio)
            end = time.time()
            logger.info(f"Recognition time:  {end - start}")
            return True, text
        except sr.UnknownValueError:
            logger.warning("Recognition model could not understand audio")
            return True, "Repeat, please."
        except sr.RequestError as e:
            logger.warning("Could not request results from Speech Recognition service; {0}".format(e))
            return False, None


    def say(self, message):

        with client.audio.speech.with_streaming_response.create(
            model=self.model,
            voice=self.voice,
            speed=self.speed,
            input=message,
            response_format=audio_format
        ) as response:
            response.stream_to_file("audio_test/output." + audio_format)

        logger.info("Playing...")
        audio_path = f"audio_test/output.{audio_format}"
        with open(audio_path, 'rb') as audio_file:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)